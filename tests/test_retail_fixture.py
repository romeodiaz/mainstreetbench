"""End-to-end fixture checks: the key is derivable from the inputs, and shortcuts score lower."""

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import reference_solver  # noqa: E402


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


EVALUATOR = load("retail_evaluator", ROOT / "evaluators/retail_reconciliation.py")
GENERATOR = ROOT / "tasks/retail-reconciliation/generate.py"


def generate(folder, *args):
    subprocess.run([sys.executable, str(GENERATOR), "--output-root", str(folder), *args],
                   check=True, capture_output=True)
    key = EVALUATOR.load_json(Path(folder) / "answer-keys/retail-reconciliation.json")
    return key, Path(folder) / "tasks/retail-reconciliation/inputs"


class FixtureTests(unittest.TestCase):
    def test_committed_fixture_matches_default_regeneration(self):
        with tempfile.TemporaryDirectory() as folder:
            generate(folder)
            for relative in ("answer-keys/retail-reconciliation.json", "answer-keys/retail-reconciliation.md",
                             *(f"tasks/retail-reconciliation/inputs/{name}" for name in (
                                 "orders.csv", "payments.csv", "refunds.csv", "customers.csv", "products.csv",
                                 "bookkeeping_notes.md"))):
                with self.subTest(file=relative):
                    self.assertEqual((Path(folder) / relative).read_bytes(), (ROOT / relative).read_bytes())

    def test_committed_input_hashes_match_key(self):
        key = json.loads((ROOT / "answer-keys/retail-reconciliation.json").read_text(encoding="utf-8"))
        for name, digest in key["input_hashes"].items():
            path = ROOT / "tasks/retail-reconciliation/inputs" / name
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), digest)

    def test_reference_solver_scores_perfectly_and_naive_solver_does_not(self):
        for seed in ("20260930", "7", "11"):
            with self.subTest(seed=seed), tempfile.TemporaryDirectory() as folder:
                key, inputs = generate(folder, "--seed", seed)
                reference = EVALUATOR.grade(key, reference_solver.solve(inputs), inputs)
                self.assertEqual(reference["quality"]["score"], 1.0, reference["quality"])
                self.assertEqual(reference["input_preservation"]["passed"], 6)
                naive = EVALUATOR.grade(key, reference_solver.naive_solve(inputs), inputs)
                self.assertLess(naive["quality"]["score"], 0.5, naive["quality"])

    def test_instances_are_numerous_and_scattered(self):
        key = json.loads((ROOT / "answer-keys/retail-reconciliation.json").read_text(encoding="utf-8"))
        types = {entry["type"] for entry in key["instances"]}
        self.assertGreaterEqual(len(key["instances"]), 100)
        self.assertGreaterEqual(len(types), 20)
        numbers = sorted(int(a.rsplit("-", 1)[1]) for e in key["instances"] for a in e["anchor_ids"]
                         if a.startswith("O-202609-"))
        # Keyed orders must not cluster at the start of the ID range as in v0.1.
        self.assertGreater(numbers[len(numbers) // 2], key["metrics"]["order_count"] // 4)


if __name__ == "__main__":
    unittest.main()
