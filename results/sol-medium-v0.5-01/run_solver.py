from pathlib import Path
from datetime import datetime, timezone
import json, os, signal, subprocess, time

control=Path(__file__).resolve().parent
meta=json.loads((control/'run.json').read_text())
args=['/usr/bin/sandbox-exec','-f',str(control/'solver.sb'),'codex','--no-daemon','exec','--ignore-user-config','--ignore-rules','--ephemeral','--skip-git-repo-check','-C',meta['workspace'],'-m','gpt-6.1-sol','-c','model_reasoning_effort="medium"','-c','web_search="disabled"','--sandbox','danger-full-access','--disable','multi_agent','--disable','multi_agent_v2','--disable','memories','--disable','chronicle','--disable','apps','--disable','plugins','--disable','hooks','--enable','skip_host_skill_discovery','--disable','fast_mode','--json','--color','never','-']
# Preserve ordinary identity variables, excluding inherited provider credentials and integration configuration.
env={k:v for k,v in os.environ.items() if k in {'HOME','USER','LOGNAME','LANG','LC_ALL','TERM'}}
env['PATH']='/Users/romeodiaz/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin:/Users/romeodiaz/.local/bin:/usr/bin:/bin:/usr/sbin:/sbin'
env['TMPDIR']=str(Path(meta['workspace']).parent/'tmp'); Path(env['TMPDIR']).mkdir(exist_ok=True)
env['PYTHONDONTWRITEBYTECODE']='1'
meta.update(argv=args,started_at=datetime.now(timezone.utc).isoformat(),status='running',environment_variable_names=sorted(env))
(control/'run.json').write_text(json.dumps(meta,indent=2)+'\n')
start=time.monotonic()
with (control/'events.jsonl').open('w') as out, (control/'stderr.log').open('w') as err:
 p=subprocess.Popen(args,cwd=meta['workspace'],env=env,stdin=subprocess.PIPE,stdout=out,stderr=err,text=True,start_new_session=True)
 meta['pid']=p.pid; (control/'run.json').write_text(json.dumps(meta,indent=2)+'\n')
 print('Started',meta['run_id'],'PID',p.pid,flush=True)
 try:
  p.communicate((control/'prompt.txt').read_text(),timeout=meta['time_limit_seconds'])
  meta['status']='completed' if p.returncode==0 else 'runner_failed'
 except subprocess.TimeoutExpired:
  os.killpg(p.pid,signal.SIGTERM)
  try: p.wait(timeout=10)
  except subprocess.TimeoutExpired:
   os.killpg(p.pid,signal.SIGKILL); p.wait()
  meta['status']='time_limit'
 meta['exit_code']=p.returncode
meta['elapsed_seconds']=round(time.monotonic()-start,3)
meta['finished_at']=datetime.now(timezone.utc).isoformat()
usage=[]; finals=[]
for line in (control/'events.jsonl').read_text().splitlines():
 try: event=json.loads(line)
 except ValueError: continue
 if event.get('type')=='turn.completed': usage.append(event.get('usage',{}))
 item=event.get('item',{})
 if event.get('type')=='item.completed' and item.get('type')=='agent_message': finals.append(item.get('text',''))
meta['usage']=usage
if finals: (control/'final-response.md').write_text(finals[-1])
(control/'run.json').write_text(json.dumps(meta,indent=2)+'\n')
print('Finished',meta['status'],'after',meta['elapsed_seconds'],'seconds',flush=True)
