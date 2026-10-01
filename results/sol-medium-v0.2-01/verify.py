#!/usr/bin/env python3
"""Verify this recorded run and regrade its frozen evidence without model calls."""

import hashlib
import json
from pathlib import Path
import runpy


ROOT = Path(__file__).resolve().parent


def read_json(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def check_hash(path, expected, size=None):
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError(f"Hash mismatch: {path.relative_to(ROOT)}")
    if size is not None and len(data) != size:
        raise ValueError(f"Size mismatch: {path.relative_to(ROOT)}")


def main():
    manifest = read_json("frozen-manifest.json")
    expected_files = set()
    for name, record in manifest.items():
        filename = "assistant-response.md" if name == "__assistant_final_response__" else name
        expected_files.add(filename)
        check_hash(ROOT / "submission" / filename, record["sha256"], record.get("bytes"))
    actual_files = {str(path.relative_to(ROOT / "submission"))
                    for path in (ROOT / "submission").rglob("*") if path.is_file()}
    if actual_files != expected_files:
        raise ValueError("Submission inventory differs from the frozen manifest")

    extraction = read_json("grading/extraction-manifest.json")
    for name, digest in extraction["sha256"].items():
        check_hash(ROOT / "grading" / name, digest)
    reveal = read_json("grading/reference-reveal.json")
    check_hash(ROOT / "grading/reference.json", reveal["reference_sha256"])
    if not reveal["extraction_frozen_first"] or extraction["frozen_at"] >= reveal["revealed_at"]:
        raise ValueError("Reference reveal must follow the frozen extraction")

    original = read_json("grading/evidence.json")
    reviewed = read_json("grading/reviewed-evidence.json")
    numerical = lambda data: {key: value for key, value in data.items()
                              if key not in {"artifacts", "scope_review"}}
    if numerical(original) != numerical(reviewed):
        raise ValueError("Reviewed evidence changes extracted values")

    evaluator = runpy.run_path(str(ROOT / "grading/evaluator.py"))
    reference = evaluator["load_json"](ROOT / "grading/reference.json")
    report = evaluator["grade"](reference, reviewed, ROOT / "submission")
    report["reporting_period"] = reference["reporting_period"]
    if report != read_json("grading/report.json"):
        raise ValueError("Recomputed report differs from the saved report")
    print(f"Verified {len(manifest)} submission files, frozen extraction and reference.")
    print(f"Saved grading report reproduced exactly: quality {report['quality']['score']:.4f}.")


if __name__ == "__main__":
    main()
