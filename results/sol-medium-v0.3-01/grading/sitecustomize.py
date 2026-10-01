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
