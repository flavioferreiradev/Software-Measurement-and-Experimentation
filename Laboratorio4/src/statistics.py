"""Testes unilaterais à direita para uma proporção, sem correção de continuidade."""

from numbers import Integral, Real
import numpy as np
from scipy.stats import binomtest, norm


def positive_integer(value, name="n"):
    if isinstance(value, bool) or not isinstance(value, Integral) or value <= 0:
        raise ValueError(f"{name} deve ser um inteiro positivo")
    return int(value)


def probability(value, name="p", endpoints=True):
    if isinstance(value, bool) or not isinstance(value, Real) or not np.isfinite(value):
        raise ValueError(f"{name} deve ser uma probabilidade finita")
    if not (0 <= value <= 1 if endpoints else 0 < value < 1):
        raise ValueError(f"{name} fora do intervalo permitido")
    return float(value)


def binary_sample(sample):
    data = np.asarray(sample)
    if data.ndim != 1 or data.size == 0 or data.dtype.kind not in "biuf":
        raise ValueError("A amostra deve ser um vetor numérico binário não vazio")
    if not np.all((data == 0) | (data == 1)):
        raise ValueError("A amostra só pode conter 0 e 1")
    return data.astype(np.int64)


def generate_sample(n, p, seed=42):
    n = positive_integer(n)
    p = probability(p)
    if isinstance(seed, bool) or not isinstance(seed, Integral) or seed < 0:
        raise ValueError("seed deve ser inteiro não negativo")
    return np.random.default_rng(int(seed)).binomial(1, p, size=n)


def summarize(sample):
    data = binary_sample(sample)
    n, k = len(data), int(data.sum())
    p_hat = k / n
    return {"n": n, "k": k, "p_hat": p_hat,
            "bernoulli_variance": p_hat * (1 - p_hat),
            "sample_variance": float(data.var(ddof=1)) if n > 1 else None}


def interpretation(reject):
    return ("Rejeitar H₀: o exemplo fornece evidência de proporção de falhas superior a 5%."
            if reject else
            "Não rejeitar H₀: o exemplo não fornece evidência suficiente de que a proporção de falhas supera 5%; isso não comprova H₀.")


def test_proportion(sample, p0=0.05, alpha=0.05):
    """Mesma amostra nos dois testes; rejeitar apenas se p-valor < alpha."""
    summary = summarize(sample)
    p0 = probability(p0, "p0", endpoints=False)
    alpha = probability(alpha, "alpha", endpoints=False)
    n, k, p_hat = (summary[x] for x in ("n", "k", "p_hat"))
    se = float(np.sqrt(p0 * (1 - p0) / n))
    z = float((p_hat - p0) / se)
    z_p = float(norm.sf(z))
    exact = binomtest(k, n, p=p0, alternative="greater")
    tests = {
        "z": {"statistic_name": "Z", "statistic": z, "standard_error_h0": se,
              "p_value": z_p, "approximation": "standard_normal_no_continuity_correction",
              "expected_failures_h0": n * p0, "expected_successes_h0": n * (1 - p0),
              "normal_rule_of_thumb_met": min(n * p0, n * (1 - p0)) >= 10},
        "binomial_exact": {"statistic_name": "p_hat (SciPy binomtest)",
                           "statistic": float(exact.statistic), "count_statistic": k,
                           "p_value": float(exact.pvalue)},
    }
    for result in tests.values():
        result.update({"reject_h0": result["p_value"] < alpha,
                       "alternative": "greater", "alpha": alpha, "p0": p0})
        # A interpretação é gerada com a referência configurada, não um valor fixo.
        pct = f"{p0 * 100:g}%"
        result["interpretation_pt"] = interpretation(result["reject_h0"]).replace("5%", pct)
    return {**summary, "p0": p0, "alpha": alpha,
            "effect_difference": p_hat - p0, "tests": tests}
