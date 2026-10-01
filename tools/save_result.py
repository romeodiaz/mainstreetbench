#!/usr/bin/env python3
"""Copy a finished run's evidence into results/ (maintainer only), for runs made without --save-results.

    python3 tools/save_result.py ../MainStreetBench-runs/evidence/<run>
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_bench import save_results  # noqa: E402

if len(sys.argv) != 2 or not (Path(sys.argv[1]) / "SCORECARD.md").is_file():
    raise SystemExit(__doc__)
evidence = Path(sys.argv[1]).expanduser().resolve()
target = save_results(evidence, evidence.name)
print(f"Copied into {target} and results/{evidence.name}.md; review, then commit and push.")
