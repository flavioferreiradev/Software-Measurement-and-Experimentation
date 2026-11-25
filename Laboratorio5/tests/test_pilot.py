"""Verificação de ponta a ponta do contrato e da geração reproduzível do piloto."""

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "src" / "run_pilot.py"
sys.path.insert(0, str(SCRIPT.parent))
from validate_full_s02 import validate


class PilotTest(unittest.TestCase):
    def test_repeated_run_preserves_inputs_and_both_treatments(self):
        with tempfile.TemporaryDirectory() as directory:
            outputs = []
            for run_number in (1, 2):
                output = Path(directory) / str(run_number)
                subprocess.run(
                    [sys.executable, str(SCRIPT), "--rows", "300", "--customers", "30",
                     "--queries", "6", "--blocks", "2", "--inserts", "10",
                     "--replications", "2", "--output-dir", str(output)],
                    check=True, capture_output=True, text=True,
                )
                metadata = json.loads((output / "metadata.json").read_text())
                with (output / "read_timings.csv").open(newline="") as stream:
                    reads = list(csv.DictReader(stream))
                with (output / "write_timings.csv").open(newline="") as stream:
                    writes = list(csv.DictReader(stream))
                self.assertEqual(len(reads), 2 * 2 * 6 * 2)
                self.assertEqual(len(writes), 2 * 2 * 2)
                self.assertEqual({row["condition"] for row in reads}, {"without_index", "with_index"})
                self.assertEqual([rep["final_rows"] for rep in metadata["replications"]], [320, 320])
                for rep in metadata["replications"]:
                    self.assertIn("SCAN orders", rep["query_plans"]["without_index"])
                    self.assertTrue(any("idx_customer_created" in plan for plan in rep["query_plans"]["with_index"]))
                outputs.append(metadata)

            self.assertEqual(
                [rep["baseline_sha256"] for rep in outputs[0]["replications"]],
                [rep["baseline_sha256"] for rep in outputs[1]["replications"]],
            )
            self.assertEqual(
                [rep["query_customer_ids"] for rep in outputs[0]["replications"]],
                [rep["query_customer_ids"] for rep in outputs[1]["replications"]],
            )
            report = validate(Path(directory) / "1", outputs[0]["config"],
                              outputs[0]["environment"]["sqlite"])
            self.assertEqual((report["pairs"], report["read_records"], report["write_batches"]),
                             (2, 48, 8))

            read_path = Path(directory) / "1" / "read_timings.csv"
            with read_path.open(newline="", encoding="utf-8") as stream:
                rows = list(csv.DictReader(stream))
            rows[0]["customer_id"] = str(int(rows[0]["customer_id"]) + 1)
            with read_path.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
                writer.writeheader()
                writer.writerows(rows)
            with self.assertRaisesRegex(ValueError, "IDs de cliente divergentes|Consultas não pareadas"):
                validate(Path(directory) / "1", outputs[0]["config"],
                         outputs[0]["environment"]["sqlite"])


if __name__ == "__main__":
    unittest.main()
