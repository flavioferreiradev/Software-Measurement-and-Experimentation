import math

import numpy as np
import pytest
from scipy.stats import binom, binomtest, norm

from src.statistics import binary_sample, generate_sample, summarize, test_proportion as apply_tests


def test_reproducibility():
    a = generate_sample(42, 4 / 42, 42)
    np.testing.assert_array_equal(a, generate_sample(42, 4 / 42, 42))
    np.testing.assert_array_equal(a, np.random.default_rng(42).binomial(1, 4 / 42, 42))
    assert set(a) <= {0, 1}


@pytest.mark.parametrize("n", [0, -1, 1.5, True, "30", None, float("nan")])
def test_invalid_n(n):
    with pytest.raises(ValueError):
        generate_sample(n, 0.05)


@pytest.mark.parametrize("p", [-0.1, 1.1, float("nan"), float("inf"), "0.1", None, True])
def test_invalid_p(p):
    with pytest.raises(ValueError):
        generate_sample(30, p)


@pytest.mark.parametrize("seed", [-1, 1.1, True, None])
def test_invalid_seed(seed):
    with pytest.raises(ValueError):
        generate_sample(30, 0.05, seed)


@pytest.mark.parametrize("sample", [[], [[0, 1]], [0, 2], [float("nan")], ["0", "1"], [None]])
def test_invalid_sample(sample):
    with pytest.raises(ValueError):
        binary_sample(sample)


@pytest.mark.parametrize("p,k", [(0, 0), (1, 30)])
def test_generator_endpoints(p, k):
    assert generate_sample(30, p).sum() == k


@pytest.mark.parametrize("field", ["p0", "alpha"])
@pytest.mark.parametrize("value", [0, 1, -1, float("nan"), True])
def test_invalid_test_parameters(field, value):
    with pytest.raises(ValueError):
        apply_tests([0, 1], **{field: value})


@pytest.mark.parametrize("n,k", [(30, 0), (30, 30), (42, 4), (60, 6), (60, 7), (1, 0), (1, 1)])
def test_against_independent_mathematical_references(n, k):
    result = apply_tests([1] * k + [0] * (n - k))
    assert result["p_hat"] == k / n
    se = math.sqrt(0.05 * 0.95 / n)
    z = (k / n - 0.05) / se
    z_p = math.erfc(z / math.sqrt(2)) / 2
    exact_p = sum(math.comb(n, j) * 0.05**j * 0.95**(n - j) for j in range(k, n + 1))
    assert result["tests"]["z"]["standard_error_h0"] == pytest.approx(se)
    assert result["tests"]["z"]["statistic"] == pytest.approx(z)
    assert result["tests"]["z"]["p_value"] == pytest.approx(z_p, rel=1e-10, abs=1e-300)
    assert result["tests"]["z"]["p_value"] == pytest.approx(norm.sf(z))
    assert result["tests"]["binomial_exact"]["p_value"] == pytest.approx(exact_p, rel=1e-10)
    assert result["tests"]["binomial_exact"]["p_value"] == pytest.approx(binom.sf(k - 1, n, 0.05))
    assert result["tests"]["binomial_exact"]["statistic"] == k / n
    for test in result["tests"].values():
        assert test["reject_h0"] == (test["p_value"] < 0.05)
        assert 0 <= test["p_value"] <= 1


def test_no_failures_and_all_failures():
    zero = apply_tests([0] * 30)
    assert zero["tests"]["binomial_exact"]["p_value"] == 1
    assert all(not x["reject_h0"] for x in zero["tests"].values())
    assert all(x["reject_h0"] for x in apply_tests([1] * 30)["tests"].values())
    assert "não comprova H₀" in zero["tests"]["z"]["interpretation_pt"]


def test_strict_alpha_boundary():
    data = [1] * 4 + [0] * 38
    alpha = binomtest(4, 42, p=0.05, alternative="greater").pvalue
    assert not apply_tests(data, alpha=alpha)["tests"]["binomial_exact"]["reject_h0"]
    assert apply_tests(data, alpha=alpha + 1e-8)["tests"]["binomial_exact"]["reject_h0"]


def test_summary_variance():
    result = summarize([0, 0, 0, 1])
    assert result["p_hat"] == 0.25
    assert result["bernoulli_variance"] == 0.1875
    assert result["sample_variance"] == 0.25
    assert summarize([0])["sample_variance"] is None
