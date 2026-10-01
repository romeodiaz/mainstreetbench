#!/usr/bin/env python3
"""Run unchanged trusted acceptance grader; all bakery.server children are sandboxed.

The parent evaluator is trusted and runs with an explicitly clean environment.
macOS refuses nested Seatbelt profiles, so the evaluator itself is not nested
inside another profile. The server child cannot read the hidden suite/evaluator.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


def manifest(root):
    result = {}
    for path in sorted(root.rglob('*')):
        if path.is_symlink():
            raise ValueError(f'Symlink not permitted: {path}')
        if path.is_file():
            result[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
        elif not path.is_dir():
            raise ValueError(f'Nonregular entry not permitted: {path}')
    return result


def profile(read_roots, tmp, grader_home):
    runtime = Path(sys.prefix).resolve()
    base_runtime = Path(sys.base_prefix).resolve()
    allow = ['/System/Library', '/System/Volumes/Preboot', '/usr/bin', '/usr/lib', '/usr/share',
             '/Library/Apple', '/private/preboot', '/private/var/db/dyld',
             str(runtime), str(base_runtime), *map(str, read_roots), str(tmp), str(grader_home), '/private/var/db/timezone']
    filters = ' '.join(f'(subpath {json.dumps(s)})' for s in allow)
    return f'''(version 1)
(deny default)
(allow process-fork process-exec)
(allow signal (target same-sandbox))
(allow file-map-executable)
(allow sysctl-read)
(allow file-read-metadata)
(allow file-read* {filters} (literal "/private/etc/localtime") (literal "/") (literal "/dev/null") (literal "/dev/random") (literal "/dev/urandom"))
(allow file-write* (subpath {json.dumps(str(tmp))}) (literal "/dev/null"))
(allow network-outbound (remote ip "localhost:*"))
(allow network-inbound (local ip "localhost:*"))
(allow network-bind (local ip "localhost:*"))
'''


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--site', required=True, type=Path)
    p.add_argument('--source', required=True, type=Path, help='Snapshot root with evaluators and tasks/ordering-site/{starter,hidden_tests}')
    p.add_argument('--out', required=True, type=Path, help='New empty grading evidence directory')
    p.add_argument('--chromium', required=True, type=Path, help='Controller-installed Chromium executable')
    p.add_argument('--browsers-path', required=True, type=Path, help='Controller-only Playwright browser installation directory')
    args = p.parse_args()
    site, source, out = [x.resolve() for x in (args.site, args.source, args.out)]
    if not (site/'bakery/server.py').is_file():
        p.error('Missing bakery/server.py')
    before = manifest(site)
    if out.exists() and any(out.iterdir()):
        p.error('Grading output directory is not empty')
    out.mkdir(parents=True, exist_ok=True)
    trusted = out/'trusted'
    (trusted/'evaluators').mkdir(parents=True)
    shutil.copy2(source/'evaluators/ordering_site.py', trusted/'evaluators/ordering_site.py')
    for part in ['hidden_tests', 'starter']:
        shutil.copytree(source/'tasks/ordering-site'/part, trusted/'tasks/ordering-site'/part,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    source_hashes = manifest(trusted)
    (out/'source-manifest.json').write_text(json.dumps(source_hashes, indent=2)+'\n')
    (out/'site-before.json').write_text(json.dumps(before, indent=2)+'\n')
    tmp, grader_home = out/'scratch/tmp', out/'scratch/grader-home'
    for folder in (tmp, grader_home, trusted/'bootstrap'):
        folder.mkdir(parents=True)
    sandbox = out/'site.sb'
    sandbox.write_text(profile([site, trusted/'tasks/ordering-site/starter'], tmp, grader_home))
    hook_source = Path(__file__).parent/'trusted/bootstrap/sitecustomize.py'
    if not hook_source.is_file():
        hook_source = Path(__file__).parent/'sitecustomize.py'
    shutil.copy2(hook_source, trusted/'bootstrap/sitecustomize.py')
    probe = grader_home/'sandbox_probe.py'
    probe.write_text('''import errno,json,socket,sys\nfrom pathlib import Path\nblocked=[]\nfor name in sys.argv[1:]:\n    try: Path(name).read_bytes()\n    except PermissionError: blocked.append(name)\n    else: raise AssertionError("Forbidden read was not denied: "+name)\ns=socket.socket();s.bind(("127.0.0.1",0));s.listen(1)\nc=socket.create_connection(s.getsockname());a,_=s.accept();a.close();c.close();s.close()\ns=socket.socket();s.settimeout(2)\ntry: s.connect(("1.1.1.1",443))\nexcept PermissionError: pass\nelse: raise AssertionError("External network was not denied")\nprint(json.dumps({"blocked_reads":blocked,"loopback":"allowed","external_network":"denied"}))\n''')
    env = {'PATH':'/usr/bin:/bin:/usr/sbin:/sbin', 'TMPDIR':str(tmp),
           'PYTHONNOUSERSITE':'1', 'PYTHONDONTWRITEBYTECODE':'1'}
    forbidden = [trusted/'evaluators/ordering_site.py', trusted/'tasks/ordering-site/hidden_tests/harness.py',
                 source/'tasks/ordering-site/reference/bakery/server.py',
                 Path('/Users/romeodiaz/.codex/auth.json'), Path('/Users/romeodiaz/Code/mainstreetbench/README.md'),
                 Path('/System/Volumes/Data/Users/romeodiaz/.codex/auth.json'),
                 Path('/System/Volumes/Data/Users/romeodiaz/Code/mainstreetbench/README.md')]
    forbidden = [str(x) for x in forbidden if x.is_file() and not x.is_relative_to(site)]
    preflight = subprocess.run(['/usr/bin/sandbox-exec','-f',str(sandbox),sys.executable,str(probe),*forbidden],
                              cwd=grader_home, env=env, capture_output=True, text=True)
    (out/'preflight-stdout.txt').write_text(preflight.stdout)
    (out/'preflight-stderr.txt').write_text(preflight.stderr)
    if preflight.returncode:
        raise RuntimeError('Sandbox preflight failed: '+preflight.stderr[-2000:])
    env.update({'PYTHONPATH':str(trusted/'bootstrap'), 'MSB_SITE_SANDBOX':str(sandbox),
                'MSB_LAUNCH_LOG':str(out/'server-launches.jsonl'),
                'MSB_BROWSER_LOG':str(out/'browser-launches.jsonl'),
                'CHROMIUM_PATH':str(args.chromium.resolve()),
                'PLAYWRIGHT_BROWSERS_PATH':str(args.browsers_path.resolve())})
    cmd = [sys.executable,str(trusted/'evaluators/ordering_site.py'),'--site',str(site),'--report',str(out/'report.json')]
    start = time.time()
    run = subprocess.run(cmd, cwd=trusted, env=env, capture_output=True, text=True, timeout=1850)
    (out/'stdout.txt').write_text(run.stdout)
    (out/'stderr.txt').write_text(run.stderr)
    after = manifest(site)
    (out/'site-after.json').write_text(json.dumps(after, indent=2)+'\n')
    unchanged = before == after
    launch_count = len((out/'server-launches.jsonl').read_text().splitlines()) if (out/'server-launches.jsonl').exists() else 0
    meta = {'argv':cmd, 'started_epoch':start,'elapsed_seconds':round(time.time()-start,3),
            'returncode':run.returncode,'server_launch_count':launch_count,
            'site_bytes_unchanged':unchanged,'clean_environment_keys':sorted(env),
            'python':sys.version,'server_sandbox_sha256':hashlib.sha256(sandbox.read_bytes()).hexdigest(),
            'chromium_path':str(args.chromium.resolve()),
            'chromium_sha256':hashlib.sha256(args.chromium.read_bytes()).hexdigest(),
            'browser_policy':'Fresh Playwright contexts and temporary profiles; Chromium built-in sandbox explicitly enabled; clean environment; browser behavior/network otherwise unchanged.',
            'hook_sha256':hashlib.sha256((trusted/'bootstrap/sitecustomize.py').read_bytes()).hexdigest(),
            'scope':'Trusted evaluator and hidden suite outside sandbox; every bakery.server subprocess in deny-default Seatbelt sandbox.'}
    (out/'run.json').write_text(json.dumps(meta, indent=2)+'\n')
    print(run.stdout, end='')
    if run.stderr:
        print(run.stderr, file=sys.stderr, end='')
    if run.returncode or not unchanged or not launch_count:
        raise RuntimeError(f'Grading integrity failure: rc={run.returncode}, unchanged={unchanged}, launches={launch_count}')
    print(f'Sandboxed server launches: {launch_count}; frozen site bytes unchanged.')

if __name__ == '__main__':
    main()
