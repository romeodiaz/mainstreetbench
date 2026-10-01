#!/bin/zsh
# Double-click on macOS. Inputs and old reports are never removed.
set -e
cd "$(dirname "$0")"
if [[ ! -x .venv/bin/python3 ]]; then
  python3 -m venv .venv
fi
.venv/bin/python3 -m pip install -q -r requirements.txt
printf 'Close month (YYYY-MM), e.g. 2026-10: '
read close_month
printf 'Input folder (press Enter for this folder): '
read input_folder
input_folder=${input_folder:-.}
.venv/bin/python3 reconcile.py --input "$input_folder" --month "$close_month"
open "reports/$close_month/dashboard.html"
printf '\nDone. Press Enter to close. '
read close_done
