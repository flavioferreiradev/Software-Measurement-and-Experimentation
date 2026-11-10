"""Equivalência estatística e incerteza Monte Carlo da Issue #34."""

import hashlib
import math

import numpy as np
import pytest
from scipy.stats import binomtest

from src.experiments import (SCENARIOS, generate_counts, rejection_rules, simulate_cell,
                             stream_entropy, summarize_rejections, tests_from_counts as count_tests,
                             theoretical_rejection_rate)
from src.statistics import test_proportion as sample_tests


@pytest.mark.parametrize("n,p0,alpha", [(42, 0.05, 0.05), (200, 0.05, 0.05),
                                      (30, 0.1, 0.01), (1, 0.9, 0.01)])
def test_all_attainable_counts_match_s01(n, p0, alpha):
    counts = np.arange(n + 1)
    vector = count_tests(counts, n, p0, alpha)
    for k in counts:
        scalar = sample_tests([1] * k + [0] * (n - k), p0, alpha)
        for name in ("z", "binomial_exact"):
            expected = scalar["tests"][name]
            assert vector[name]["statistic"][k] == pytest.approx(expected["statistic"], rel=1e-13)
            assert vector[name]["p_value"][k] == pytest.approx(expected["p_value"], rel=1e-12, abs=1e-300)
            assert bool(vector[name]["reject_h0"][k]) is expected["reject_h0"]


@pytest.mark.parametrize("n,z_critical,exact_critical", [(42, 5, 6), (200, 16, 16)])
def test_rejection_frontiers(n, z_critical, exact_critical):
    rules = rejection_rules(n)
    assert rules["z"]["critical_k"] == z_critical
    assert rules["binomial_exact"]["critical_k"] == exact_critical
    for name, critical in [("z", z_critical), ("binomial_exact", exact_critical)]:
        vector = count_tests(np.array([critical - 1, critical]), n)
        assert vector[name]["reject_h0"].tolist() == [False, True]
        assert vector[name]["p_value"][0] >= 0.05 > vector[name]["p_value"][1]


@pytest.mark.parametrize("name", ["z", "binomial_exact"])
def test_strict_pvalue_alpha_equality(name):
    value = float(count_tests([5], 42)[name]["p_value"][0])
    assert not count_tests([5], 42, alpha=value)[name]["reject_h0"][0]
    assert count_tests([5], 42, alpha=value + 1e-10)[name]["reject_h0"][0]


@pytest.mark.parametrize("n", [42, 200])
def test_theory_against_independent_combinatorial_sum(n):
    for name, rule in rejection_rules(n).items():
        critical = rule["critical_k"]
        for p in [0.05, 0.075, 0.20]:
            expected = math.fsum(math.comb(n, k) * p**k * (1 - p)**(n - k)
                                 for k in range(critical, n + 1))
            assert theoretical_rejection_rate(n, p, critical) == pytest.approx(expected, rel=1e-12)
        # Também verifica a aproximação Z sem usar scipy.stats.norm na referência.
        z = (critical / n - 0.05) / math.sqrt(0.05 * 0.95 / n)
        assert count_tests([critical], n)["z"]["p_value"][0] == pytest.approx(math.erfc(z / math.sqrt(2)) / 2)


def test_empty_rejection_region():
    rules = rejection_rules(1, p0=0.9, alpha=0.01)
    assert rules["binomial_exact"]["critical_k"] is None
    assert theoretical_rejection_rate(1, 0.2, None) == 0


def test_unsigned_counts_do_not_underflow_at_zero():
    result = count_tests(np.array([0, 42], dtype=np.uint8), 42)
    assert result["binomial_exact"]["p_value"][0] == 1
    assert result["binomial_exact"]["p_value"][1] == pytest.approx(0.05**42)


@pytest.mark.parametrize("counts", [[], [1.0], [True], [-1], [43], [[1, 2]], [float("nan")], ["1"]])
def test_invalid_counts(counts):
    with pytest.raises(ValueError):
        count_tests(counts, 42)


@pytest.mark.parametrize("field,value", [("n", 0), ("n", True), ("n", 1.5),
                                         ("p", -0.1), ("p", 1.1), ("p", float("nan")),
                                         ("repetitions", 0), ("repetitions", True), ("repetitions", 2.5),
                                         ("seed", -1), ("seed", True), ("seed", None)])
def test_invalid_generator_parameters(field, value):
    kwargs = dict(n=42, p=0.05, repetitions=100, seed=42)
    kwargs[field] = value
    with pytest.raises(ValueError):
        generate_counts(**kwargs)


@pytest.mark.parametrize("field,value", [("p0", 0), ("p0", 1), ("alpha", 0),
                                         ("alpha", 1), ("alpha", float("inf"))])
def test_invalid_test_parameters(field, value):
    with pytest.raises(ValueError):
        count_tests([0, 1], 42, **{field: value})


def test_seed_stream_is_parameter_addressed_and_order_independent():
    expected = {}
    for n, p in [(42, 0.05), (200, 0.075), (42, 0.2)]:
        expected[n, p] = generate_counts(n, p, 100)
        np.testing.assert_array_equal(expected[n, p], generate_counts(n, p, 100))
    for n, p in reversed(list(expected)):
        np.testing.assert_array_equal(expected[n, p], generate_counts(n, p, 100))
    assert stream_entropy(42, 200, 0.075) == [42, 200, 3, 40]
    assert stream_entropy(42, 42, 0.05) == [42, 42, 1, 20]
    assert not np.array_equal(expected[42, 0.05], generate_counts(42, 0.05, 100, seed=43))


def test_both_tests_consume_same_repetitions_and_histogram():
    scenario = SCENARIOS[1]
    row = simulate_cell(scenario, 0.1)
    counts = generate_counts(42, 0.1)
    vector = count_tests(counts, 42)
    assert row["counts_sha256"] == hashlib.sha256(counts.astype("<u4").tobytes()).hexdigest()
    assert row["counts_histogram"] == np.bincount(counts, minlength=43).tolist()
    for name in ("z", "binomial_exact"):
        assert row["tests"][name]["rejections"] == int(vector[name]["reject_h0"].sum())
    paired = row["paired_decisions"]
    assert sum(paired.values()) == 10_000
    assert paired["both"] + paired["z_only"] == row["tests"]["z"]["rejections"]
    assert paired["both"] + paired["exact_only"] == row["tests"]["binomial_exact"]["rejections"]


@pytest.mark.parametrize("r,q", [(0, 0), (10_000, 1), (573, 0.057277894)])
def test_monte_carlo_uncertainty_and_exact_count_bands(r, q):
    summary = summarize_rejections(r, 10_000, q)
    interval = binomtest(r, 10_000).proportion_ci(0.95, method="wilson")
    assert summary["mc_ci95_wilson"] == pytest.approx([interval.low, interval.high])
    lo, hi = summary["mc_validation_count_interval"]
    assert summary["mc_consistent_with_theory"] == (lo <= r <= hi)
    assert 0 <= lo <= hi <= 10_000
    assert summary["mc_standard_error"] == pytest.approx(math.sqrt((r / 10_000) * (1 - r / 10_000) / 10_000))
    if r == 10_000:
        assert interval.low < 1  # 100% observado não significa certeza de probabilidade 1.


def test_mc_band_flags_a_large_discrepancy():
    assert not summarize_rejections(5000, 10_000, 0.05)["mc_consistent_with_theory"]
