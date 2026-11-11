"""Contrato G3/G4, reprodução completa e preservação da S01, sem gráficos novos."""

import csv
import hashlib
import json
import math
import os
from pathlib import Path
import socket
import subprocess
import sys
import urllib.request

import numpy as np
import pytest
from scipy.stats import binom

from src.collect import ROOT
from src.experiments import build_experiments, rejection_rules


@pytest.fixture(scope="module")
def artifact():
    return build_experiments()


def assert_equivalent(left, right):
    if isinstance(left, dict):
        assert left.keys() == right.keys()
        for key in left:
            assert_equivalent(left[key], right[key])
    elif isinstance(left, list):
        assert len(left) == len(right)
        for a, b in zip(left, right):
            assert_equivalent(a, b)
    elif isinstance(left, float):
        assert right == pytest.approx(left, rel=1e-12, abs=1e-15)
    else:
        assert type(left) is type(right)
        assert left == right


def test_versioned_results_match_execution(artifact):
    saved = json.loads((ROOT / "results/experiments_s02.json").read_text(encoding="utf-8"))
    current = json.loads(json.dumps(artifact))
    saved.pop("software")
    current.pop("software")
    assert_equivalent(saved, current)


def test_contract_structure_and_exact_protocol(artifact):
    assert set(artifact) == {"schema_version", "scope", "protocol", "source_s01", "scenarios", "rows", "g3", "g4", "mc_validation", "software"}
    assert artifact["schema_version"] == "1.0.0"
    protocol = artifact["protocol"]
    assert protocol["p0"] == protocol["alpha"] == 0.05
    assert protocol["seed"] == 42
    assert protocol["repetitions"] == 10_000
    assert protocol["p_levels"] == [0.05, 0.075, 0.1, 0.125, 0.15, 0.2]
    assert protocol["total_independent_samples"] == 120_000
    assert protocol["effect_unit"] == "proportion"
    assert protocol["paired_tests"] is True
    assert artifact["mc_validation"]["comparison_count"] == 24
    assert len(artifact["rows"]) == 12
    assert len({r["id"] for r in artifact["rows"]}) == 12
    assert len({tuple(r["stream_entropy"]) for r in artifact["rows"]}) == 12
    assert {s["n"] for s in artifact["scenarios"]} == {42, 200}
    small = next(s for s in artifact["scenarios"] if s["n"] == 42)
    reference = next(s for s in artifact["scenarios"] if s["n"] == 200)
    assert small["expected_failures_h0"] == 2.1
    assert small["normal_rule_of_thumb_met"] is False
    assert reference["normal_rule_of_thumb_met"] is True


def test_no_nan_or_infinite_values(artifact):
    def visit(value):
        if isinstance(value, dict):
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
        elif isinstance(value, float):
            assert math.isfinite(value)
    visit(artifact)
    json.dumps(artifact, allow_nan=False)


def test_counts_rates_theory_and_uncertainty_are_consistent(artifact):
    for row in artifact["rows"]:
        repetitions = row["repetitions"]
        assert repetitions == 10_000
        assert row["delta"] == pytest.approx(row["p"] - 0.05)
        histogram = row["counts_histogram"]
        assert len(histogram) == row["n"] + 1
        assert sum(histogram) == repetitions
        assert all(type(x) is int and x >= 0 for x in histogram)
        assert len(row["counts_sha256"]) == 64
        rules = rejection_rules(row["n"])
        for name, test in row["tests"].items():
            critical = rules[name]["critical_k"]
            assert test["rejections"] == sum(histogram[critical:])
            assert test["rejection_rate"] == test["rejections"] / repetitions
            assert 0 <= test["rejection_rate"] <= 1
            lo, hi = test["mc_ci95_wilson"]
            assert 0 <= lo <= test["rejection_rate"] + 1e-15 <= hi + 1e-15 <= 1 + 1e-15
            q = float(binom.sf(critical - 1, row["n"], row["p"]))
            assert test["theoretical_rejection_rate"] == pytest.approx(q)
            assert test["mc_minus_theory"] == pytest.approx(test["rejection_rate"] - q)
            # Critério fixado antes do confronto, não ajustado aos resultados.
            assert test["mc_consistent_with_theory"] is True
        paired = row["paired_decisions"]
        assert sum(paired.values()) == repetitions
        assert paired["both"] + paired["z_only"] == row["tests"]["z"]["rejections"]
        assert paired["both"] + paired["exact_only"] == row["tests"]["binomial_exact"]["rejections"]


def test_q1_is_the_same_zero_effect_point_used_by_q2_and_q3(artifact):
    rows = {row["id"]: row for row in artifact["rows"]}
    assert len(artifact["g3"]["row_ids"]) == 2
    assert artifact["g3"]["nominal_rate"] == 0.05
    assert len(artifact["g4"]["row_ids"]) == 12
    assert set(artifact["g3"]["row_ids"]) <= set(artifact["g4"]["row_ids"])
    for scenario in artifact["scenarios"]:
        subset = [row for row in rows.values() if row["scenario_id"] == scenario["id"]]
        assert len(subset) == 6
        assert [r["delta"] for r in subset] == [0, 0.025, 0.05, 0.075, 0.1, 0.15]
        null = [r for r in subset if r["delta"] == 0]
        assert len(null) == 1
        assert null[0]["estimand"] == "type_i_error"
        assert null[0]["used_by"] == ["Q1", "Q2", "Q3"]
        assert null[0]["id"] in artifact["g3"]["row_ids"]
        assert all(r["estimand"] == "power" for r in subset if r["delta"] > 0)


def test_reference_decisions_coincide_but_pvalues_need_not(artifact):
    for row in artifact["rows"]:
        if row["n"] == 200:
            assert row["paired_decisions"]["z_only"] == row["paired_decisions"]["exact_only"] == 0
            assert row["tests"]["z"]["rejections"] == row["tests"]["binomial_exact"]["rejections"]


def test_s01_data_and_results_unchanged_from_initial_audit():
    manifest = json.loads((ROOT / "docs/s02_preservacao_s01.json").read_text(encoding="utf-8"))
    repo = ROOT.parent
    assert len(manifest["sha256"]) == 30
    # Preserva os artefatos congelados sem impedir Flávio de ampliar o dashboard.
    protected = [relative for relative in manifest["sha256"]
                 if relative.startswith(("Laboratorio4/data/", "Laboratorio4/results/"))]
    assert len(protected) == 5
    for relative in protected:
        expected = manifest["sha256"][relative]
        actual = hashlib.sha256((repo / relative).read_bytes()).hexdigest()
        assert actual == expected, f"S01 alterada: {relative}"


def test_full_protocol_runs_without_network_or_token(monkeypatch):
    def offline(*args, **kwargs):
        raise AssertionError("A execução S02 não pode consultar a rede")
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setattr(urllib.request, "urlopen", offline)
    monkeypatch.setattr(socket, "create_connection", offline)
    assert len(build_experiments()["rows"]) == 12


def test_full_cli_repeats_byte_identically_and_preserves_s01(tmp_path):
    env = dict(os.environ)
    env.pop("GITHUB_TOKEN", None)
    before = {p.name: p.read_bytes() for p in (ROOT / "results").glob("demo*")}
    before["simulated_sample.csv"] = (ROOT / "results/simulated_sample.csv").read_bytes()
    outputs = [tmp_path / "run_a", tmp_path / "run_b"]
    for output in outputs:
        completed = subprocess.run([sys.executable, "-m", "src.run_experiments", "--output", str(output)],
                                   cwd=ROOT, env=env, capture_output=True, text=True, timeout=60)
        assert completed.returncode == 0, completed.stderr
        assert "120000" in completed.stdout
    expected_names = {"experiments_s02.json", "experiments_s02.csv", "experiments_s02_summary.md"}
    assert {p.name for p in outputs[0].iterdir()} == expected_names
    for name in expected_names:
        assert (outputs[0] / name).read_bytes() == (outputs[1] / name).read_bytes()
    for name, original in before.items():
        assert (ROOT / "results" / name).read_bytes() == original
    with (outputs[0] / "experiments_s02.csv").open(encoding="utf-8", newline="") as stream:
        csv_rows = list(csv.DictReader(stream))
    data = json.loads((outputs[0] / "experiments_s02.json").read_text(encoding="utf-8"))
    assert len(csv_rows) == 24
    for csv_row, (row, name) in zip(csv_rows, [(r, t) for r in data["rows"] for t in ("z", "binomial_exact")]):
        assert csv_row["test"] == name
        assert csv_row["scenario_id"] == row["scenario_id"]
        assert int(csv_row["rejections"]) == row["tests"][name]["rejections"]
        assert float(csv_row["rejection_rate"]) == row["tests"][name]["rejection_rate"]


def test_cli_invalid_parameters_leave_no_artifact(tmp_path):
    output = tmp_path / "invalid"
    result = subprocess.run([sys.executable, "-m", "src.run_experiments", "--repetitions", "0", "--output", str(output)],
                            cwd=ROOT, capture_output=True, text=True, timeout=60)
    assert result.returncode != 0
    assert not output.exists()
