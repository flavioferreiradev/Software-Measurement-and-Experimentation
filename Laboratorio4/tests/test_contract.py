import csv
import json
import subprocess
import sys

import numpy as np
import pytest
from scipy.stats import binom, norm

from src.collect import ROOT
from src.run_demo import build_artifact, null_distributions, write_artifact
from src.statistics import test_proportion as apply_tests


def test_versioned_contract_matches_offline_generation():
    expected = json.loads((ROOT / "results/demo_s01.json").read_text(encoding="utf-8"))
    actual = build_artifact()
    # Python patch/minor versions can differ across supported systems.
    expected.pop("software")
    actual.pop("software")
    def compare(left, right):
        if isinstance(left, dict):
            assert left.keys() == right.keys()
            for key in left:
                compare(left[key], right[key])
        elif isinstance(left, list):
            assert len(left) == len(right)
            for a, b in zip(left, right):
                compare(a, b)
        elif isinstance(left, float):
            # SciPy/BLAS podem diferir no último bit entre Windows e Linux.
            assert right == pytest.approx(left, rel=1e-12, abs=1e-15)
        else:
            assert type(left) is type(right)
            assert left == right
    compare(expected, actual)


def test_g1_consistent_same_sample():
    data = build_artifact()
    assert data["schema_version"] == "1.0.0"
    assert set(data) == {"schema_version", "scope", "scenario", "source", "empirical", "generator", "g1", "example", "g2", "software"}
    assert data["g1"]["bin_edges"] == [-0.5, 0.5, 1.5]
    for key in ("real", "simulated"):
        values = data["g1"][key]["values"]
        assert set(values) <= {0, 1}
        assert data["g1"][key]["counts"] == [values.count(0), values.count(1)]
    example = data["example"]
    assert example == apply_tests(data["g1"]["simulated"]["values"])
    assert data["generator"]["n"] == data["empirical"]["n"]
    assert data["generator"]["p"] == data["empirical"]["p_hat"]
    assert data["generator"]["seed"] == 42
    json.dumps(data, allow_nan=False)


@pytest.mark.parametrize("n,k", [(42, 0), (42, 4), (42, 42), (60, 6), (60, 7)])
def test_g2_areas_and_regions(n, k):
    result = apply_tests([1] * k + [0] * (n - k))
    plots = null_distributions(result)
    z = plots["z"]
    assert len(z["x"]) == len(z["pdf"])
    assert z["critical_value"] == pytest.approx(norm.isf(0.05))
    assert norm.sf(z["observed"]) == pytest.approx(z["p_value_tail"]["area"])
    assert z["critical_tail"]["area"] == 0.05
    exact = plots["binomial_exact"]
    pmf = np.array(exact["pmf"])
    assert pmf.sum() == pytest.approx(1)
    assert pmf[exact["p_value_mask"]].sum() == pytest.approx(exact["p_value_area"], rel=1e-10)
    assert pmf[exact["rejection_mask"]].sum() == pytest.approx(exact["critical_area"])
    assert exact["critical_area"] < 0.05
    for count, reject in zip(exact["k_support"], exact["rejection_mask"]):
        assert reject == (binom.sf(count - 1, n, 0.05) < 0.05)
    assert (k >= exact["critical_k"]) == result["tests"]["binomial_exact"]["reject_h0"]
    assert z["finite_sample_null"]["pmf"] == exact["pmf"]


def test_empty_exact_rejection_region():
    result = apply_tests([0], p0=0.9, alpha=0.01)
    exact = null_distributions(result)["binomial_exact"]
    assert exact["critical_k"] is None
    assert not any(exact["rejection_mask"])
    assert exact["critical_area"] == 0


def test_cli_and_saved_sample(tmp_path):
    completed = subprocess.run([sys.executable, "-m", "src.run_demo", "--output", str(tmp_path)],
                               cwd=ROOT, text=True, capture_output=True)
    assert completed.returncode == 0, completed.stderr
    data = json.loads((tmp_path / "demo_s01.json").read_text(encoding="utf-8"))
    with (tmp_path / "simulated_sample.csv").open(encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert [int(row["failed"]) for row in rows] == data["g1"]["simulated"]["values"]
    assert [int(row["observation"]) for row in rows] == list(range(1, data["example"]["n"] + 1))
    assert (tmp_path / "demo_interpretation.md").exists()
    original = (tmp_path / "demo_s01.json").read_bytes()
    write_artifact(build_artifact(), tmp_path)
    assert (tmp_path / "demo_s01.json").read_bytes() == original


def test_configurable_demo():
    data = build_artifact(n=30, p=0.2, seed=7)
    assert data["generator"]["n"] == 30
    assert data["generator"]["p"] == 0.2
    assert data["generator"]["seed"] == 7
    assert data["empirical"]["n"] == 42
