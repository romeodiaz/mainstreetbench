"""Controller-only isolation hook; the copied evaluator and harness remain unchanged."""
import json, os, subprocess, time
from pathlib import Path
_orig = subprocess.Popen
class SandboxedSitePopen(_orig):
    def __init__(self, args, *a, **kw):
        if isinstance(args, (list, tuple)) and list(args[1:3]) == ["-m", "bakery.server"]:
            profile = os.environ["MSB_SITE_SANDBOX"]
            allowed = {"PATH", "TMPDIR", "PYTHONNOUSERSITE", "PYTHONDONTWRITEBYTECODE", "CORNERLOAF_NOW", "ADMIN_PASSWORD"}
            env = {k: v for k, v in kw.get("env", os.environ).items() if k in allowed}
            record = {"argv": list(args), "cwd": str(kw.get("cwd")), "sandbox": profile, "time_ns": time.time_ns(), "environment_keys": sorted(env)}
            with open(os.environ["MSB_LAUNCH_LOG"], "a", encoding="utf-8") as stream:
                stream.write(json.dumps(record) + "\n")
            kw["env"] = env
            args = ["/usr/bin/sandbox-exec", "-f", profile, *args]
        super().__init__(args, *a, **kw)
subprocess.Popen = SandboxedSitePopen

# The trusted harness owns browsers; these hooks only enable Chromium's OS sandbox
# and record that launches/contexts are fresh. They do not alter tests or UI behavior.
if os.environ.get('MSB_BROWSER_LOG'):
    from playwright.sync_api import Browser, BrowserType
    _launch = BrowserType.launch
    _new_context = Browser.new_context
    def _browser_record(record):
        record['time_ns'] = time.time_ns()
        with open(os.environ['MSB_BROWSER_LOG'], 'a', encoding='utf-8') as stream:
            stream.write(json.dumps(record) + '\n')
    def _sandboxed_browser_launch(self, **kwargs):
        if self.name == 'chromium':
            kwargs['chromium_sandbox'] = True
        browser = _launch(self, **kwargs)
        _browser_record({'type': 'browser_launch', 'browser': self.name, 'version': browser.version,
                         'chromium_sandbox': kwargs.get('chromium_sandbox'),
                         'executable_path': kwargs.get('executable_path'),
                         'profile': 'new disposable Playwright launch profile'})
        return browser
    def _fresh_browser_context(self, **kwargs):
        context = _new_context(self, **kwargs)
        _browser_record({'type': 'browser_context', 'timezone_id': kwargs.get('timezone_id'),
                         'base_url': kwargs.get('base_url'), 'storage_state_supplied': bool(kwargs.get('storage_state'))})
        return context
    BrowserType.launch = _sandboxed_browser_launch
    Browser.new_context = _fresh_browser_context
