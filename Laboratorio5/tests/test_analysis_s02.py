"""Auditoria numérica da análise; nenhum teste executa coleta ou cria bancos."""

import csv
import json
import statistics
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from analyze_s02 import (METRICS, SOURCE_FILES, aggregate_pairs, analyze,
                         audited_input, describe, median_ci, sign_test_greater)


class InferenceTest(unittest.TestCase):
    def test_exact_sign_tail_direction_and_ties(self):
        self.assertEqual(sign_test_greater([1] * 20)["p_one_sided"], 1 / 1048576)
        self.assertEqual(sign_test_greater([-1] * 20)["p_one_sided"], 1)
        self.assertEqual(sign_test_greater([0] * 20)["p_one_sided"], 1)
        self.assertAlmostEqual(sign_test_greater([1, -1] * 10)["p_one_sided"], .5880985260009766)
        # Não descartar 19 zeros e reportar n=1 como se o estimando não mudasse.
        self.assertEqual(sign_test_greater([1] + [0] * 19)["n_pairs"], 20)
        self.assertGreater(sign_test_greater([1] + [0] * 19)["p_one_sided"], .99)
        with self.assertRaises(ValueError):
            sign_test_greater([])

    def test_order_interval_and_quantile_conventions(self):
        ci = median_ci(list(range(1, 21)))
        self.assertEqual((ci["low"], ci["high"]), (6, 15))
        self.assertAlmostEqual(ci["coverage_at_least"], .9586105346679688)
        self.assertEqual(median_ci([9] * 20)["low"], 9)
        self.assertIsNone(median_ci([1, 2])["low"])
        stats = describe(list(range(1, 151)))
        self.assertEqual((stats["median"], stats["p95"], stats["iqr"]), (75.5, 143, 75))


class AuditTest(unittest.TestCase):
    def test_all_pair_values_against_raw_using_decimal(self):
        source = ROOT / "results" / "full_s02"
        before = {p.name: p.read_bytes() for p in source.iterdir()}
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "analysis"
            summary = analyze(source, output)
            with (output / "per_pair.csv").open(newline="", encoding="utf-8") as stream:
                pairs = list(csv.DictReader(stream))
            metadata = json.loads((source / "metadata.json").read_text(encoding="utf-8"))
            def rows(name):
                with (source / name).open(newline="", encoding="utf-8") as stream:
                    return list(csv.DictReader(stream))
            reads, writes = rows("read_timings.csv"), rows("write_timings.csv")
            differences = []
            for pair in pairs:
                rid = int(pair["pair"])
                expected = {}
                for condition in ("without_index", "with_index"):
                    rr = sorted(Decimal(r["duration_ns"]) / 1000000 for r in reads
                                if int(r["replication"]) == rid and r["condition"] == condition)
                    ww = [r for r in writes if int(r["replication"]) == rid and r["condition"] == condition]
                    self.assertEqual(len(rr), 150)
                    self.assertEqual(len(ww), 3)
                    expected["read_median_ms", condition] = (rr[74] + rr[75]) / 2
                    expected["read_p95_ms", condition] = rr[142]
                    expected["write_ms_per_row", condition] = (
                        sum(Decimal(r["duration_ns"]) for r in ww) /
                        sum(Decimal(r["batch_count"]) for r in ww) / 1000000)
                    expected["database_bytes", condition] = Decimal(metadata["replications"][rid-1]["database_bytes"][condition])
                for metric, (_, _, benefit) in METRICS.items():
                    a, b = [expected[metric, c] for c in ("without_index", "with_index")]
                    for condition in ("without_index", "with_index"):
                        self.assertAlmostEqual(float(pair[f"{metric}_{condition}"]), float(expected[metric, condition]))
                    diff, ratio = (a-b, a/b) if benefit else (b-a, b/a)
                    self.assertAlmostEqual(float(pair[f"{metric}_difference"]), float(diff))
                    self.assertAlmostEqual(float(pair[f"{metric}_ratio"]), float(ratio))
                differences.append(float(expected["read_median_ms", "without_index"] - expected["read_median_ms", "with_index"]))
            self.assertEqual(len(pairs), 20)
            self.assertAlmostEqual(summary["primary_effect"]["median_difference_ms"], statistics.median(differences))
            self.assertAlmostEqual(summary["primary_effect"]["median_difference_ci"]["low"], sorted(differences)[5])
            self.assertAlmostEqual(summary["primary_effect"]["median_difference_ci"]["high"], sorted(differences)[14])
            self.assertEqual(summary["primary_test"]["n_pairs"], 20)
            self.assertTrue(all(d["n"] == 20 for info in summary["metrics"].values() for d in info["descriptive"].values()))
            self.assertAlmostEqual(summary["primary_effect"]["median_difference_ms"], 1.014261)
            audit = json.loads((output / "audit.json").read_text(encoding="utf-8"))
            self.assertEqual(audit["revalidation"]["read_records"], 6000)
            # Todos os sete artefatos devem ser estáveis em uma segunda análise.
            snapshot = {p.name: p.read_bytes() for p in output.iterdir()}
            analyze(source, output)
            self.assertEqual(snapshot, {p.name: p.read_bytes() for p in output.iterdir()})
        self.assertEqual(before, {p.name: p.read_bytes() for p in source.iterdir()})

    def test_checkout_line_endings_and_corruption(self):
        source = ROOT / "results" / "full_s02"
        with tempfile.TemporaryDirectory() as directory:
            copied = Path(directory) / "raw"
            copied.mkdir()
            for name in (*SOURCE_FILES, "validation.json"):
                lf = (source / name).read_bytes().replace(b"\r\n", b"\n")
                (copied / name).write_bytes(lf)
            _, audit_lf, _, _ = audited_input(copied)
            self.assertEqual(audit_lf["crlf_to_lf_in_temporary_copy"], [])
            for name in SOURCE_FILES:
                p = copied / name
                p.write_bytes(p.read_bytes().replace(b"\n", b"\r\n"))
            _, audit_crlf, _, _ = audited_input(copied)
            self.assertEqual(audit_lf["revalidation"], audit_crlf["revalidation"])
            p = copied / "read_timings.csv"
            p.write_bytes(p.read_bytes().replace(b"1046125", b"1046126", 1))
            with self.assertRaisesRegex(ValueError, "Hash divergente"):
                analyze(copied, Path(directory) / "output")
            self.assertFalse((Path(directory) / "output").exists())

    def test_outputs_cannot_overlap_raw(self):
        source = ROOT / "results" / "full_s02"
        for output in (source, source / "analysis", source.parent):
            with self.assertRaisesRegex(ValueError, "sobreposição"):
                analyze(source, output)

    def test_write_aggregation_weights_rows(self):
        # Contrato do agregador: tempo total / linhas totais, não média sem pesos.
        metadata = {"replications": [{"replication": 1, "seed": 1, "index_build_ms": 1,
                                      "database_bytes": {"without_index": 10, "with_index": 20}}]}
        reads, writes = [], []
        for condition in ("without_index", "with_index"):
            reads.append({"replication": "1", "condition": condition, "duration_ns": "1000000"})
            for count, duration in ((1, 1000000), (9, 18000000)):
                writes.append({"replication": "1", "condition": condition,
                               "batch_count": str(count), "duration_ns": str(duration)})
        pair = aggregate_pairs(metadata, reads, writes)[0]
        self.assertEqual(pair["write_ms_per_row_without_index"], 1.9)


if __name__ == "__main__":
    unittest.main()
