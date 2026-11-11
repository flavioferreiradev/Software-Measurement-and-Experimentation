"""Protocolo estatístico da Issue #34: Q1/Q2 em n=200 e n=42 (Q3)."""

from fractions import Fraction
import hashlib
from numbers import Integral
import platform

import numpy as np
import scipy
from scipy.stats import binom, binomtest, norm

from .collect import ROOT
from .data import load_real
from .statistics import positive_integer, probability

SCHEMA_VERSION = "1.0.0"
P0 = 0.05
ALPHA = 0.05
SEED = 42
REPETITIONS = 10_000
P_LEVELS = (0.05, 0.075, 0.10, 0.125, 0.15, 0.20)
SCENARIOS = (
    {"id": "reference_n200", "label_pt": "Referência: n=200", "n": 200,
     "role": "reference", "n_source": "Issue #34"},
    {"id": "small_n42", "label_pt": "Amostra pequena: n=42", "n": 42,
     "role": "small_sample", "n_source": "S01 empirical sample size"},
)
TESTS = ("z", "binomial_exact")
COMPARISON_COUNT = len(SCENARIOS) * len(P_LEVELS) * len(TESTS)


def validate_seed(seed):
    if isinstance(seed, bool) or not isinstance(seed, Integral) or seed < 0:
        raise ValueError("seed deve ser inteiro não negativo")
    return int(seed)


def stream_entropy(seed, n, p):
    """Identidade por parâmetros, independente da ordem de execução dos cenários."""
    seed = validate_seed(seed)
    n = positive_integer(n)
    p = probability(p)
    fraction = Fraction(str(p))
    return [seed, n, fraction.numerator, fraction.denominator]


def generate_counts(n, p, repetitions=REPETITIONS, seed=SEED):
    """Suficiente K~Bin(n,p), equivalente em distribuição a somar n Bernoulli iid."""
    repetitions = positive_integer(repetitions, "repetitions")
    entropy = stream_entropy(seed, n, p)
    rng = np.random.default_rng(np.random.SeedSequence(entropy))
    return rng.binomial(int(n), float(p), size=repetitions)


def tests_from_counts(counts, n, p0=P0, alpha=ALPHA):
    """Mesmas fórmulas e regra estrita da S01, vetorizadas sobre contagens."""
    n = positive_integer(n)
    p0 = probability(p0, "p0", endpoints=False)
    alpha = probability(alpha, "alpha", endpoints=False)
    counts = np.asarray(counts)
    if (counts.ndim != 1 or counts.size == 0 or counts.dtype.kind not in "iu"
            or np.any(counts < 0) or np.any(counts > n)):
        raise ValueError("counts deve ser vetor de inteiros entre 0 e n")
    # Evita underflow em K-1 quando o consumidor fornece um array unsigned.
    counts = counts.astype(np.int64)
    p_hat = counts / n
    z = (p_hat - p0) / np.sqrt(p0 * (1 - p0) / n)
    z_p = norm.sf(z)
    exact_p = binom.sf(counts - 1, n, p0)
    return {
        "z": {"statistic": z, "p_value": z_p, "reject_h0": z_p < alpha},
        "binomial_exact": {"statistic": p_hat, "p_value": exact_p, "reject_h0": exact_p < alpha},
    }


def rejection_rules(n, p0=P0, alpha=ALPHA):
    """Região de rejeição enumerada, inclusive quando a região é vazia."""
    table = tests_from_counts(np.arange(n + 1), n, p0, alpha)
    rules = {}
    for name in TESTS:
        rejected = np.flatnonzero(table[name]["reject_h0"])
        rules[name] = {"critical_k": int(rejected[0]) if rejected.size else None,
                       "rule": "K >= critical_k; empty when null"}
    return rules


def theoretical_rejection_rate(n, p, critical_k):
    """Probabilidade exata de rejeitar para qualquer teste com região de cauda."""
    return 0.0 if critical_k is None else float(binom.sf(critical_k - 1, n, p))


def summarize_rejections(rejections, repetitions, theoretical_rate, comparison_count=COMPARISON_COUNT):
    """Incerteza Monte Carlo e confronto com a distribuição teórica das contagens."""
    rate = rejections / repetitions
    interval = binomtest(rejections, repetitions).proportion_ci(0.95, method="wilson")
    # Limite global conservador de 1% por Bonferroni (24 estimativas no protocolo).
    tail = 0.01 / (2 * comparison_count)
    lower = int(binom.ppf(tail, repetitions, theoretical_rate))
    upper = int(binom.isf(tail, repetitions, theoretical_rate))
    return {
        "rejections": int(rejections), "rejection_rate": rate,
        "mc_standard_error": float(np.sqrt(rate * (1 - rate) / repetitions)),
        "mc_ci95_wilson": [float(interval.low), float(interval.high)],
        "theoretical_rejection_rate": theoretical_rate,
        "theory_mc_standard_error": float(np.sqrt(theoretical_rate * (1 - theoretical_rate) / repetitions)),
        "mc_minus_theory": rate - theoretical_rate,
        "mc_validation_count_interval": [lower, upper],
        "mc_consistent_with_theory": lower <= rejections <= upper,
    }


def simulate_cell(scenario, p, repetitions=REPETITIONS, seed=SEED):
    n = scenario["n"]
    p = probability(p)
    if p < P0:
        raise ValueError("O protocolo S02 utiliza p >= p0")
    counts = generate_counts(n, p, repetitions, seed)
    # Um único vetor alimenta ambos os testes; preservamos seu hash e histograma.
    tests = tests_from_counts(counts, n)
    rules = rejection_rules(n)
    null_row = p == P0
    delta = float(Fraction(str(p)) - Fraction(str(P0)))
    row = {
        "id": f"{scenario['id']}_p{Fraction(str(p)).numerator}of{Fraction(str(p)).denominator}",
        "scenario_id": scenario["id"], "n": n, "p": p, "delta": delta,
        "estimand": "type_i_error" if null_row else "power",
        "used_by": ["Q1", "Q2", "Q3"] if null_row else ["Q2", "Q3"],
        "repetitions": int(repetitions), "stream_entropy": stream_entropy(seed, n, p),
        "counts_sha256": hashlib.sha256(counts.astype("<u4").tobytes()).hexdigest(),
        "counts_histogram": np.bincount(counts, minlength=n + 1).tolist(),
        "tests": {},
    }
    for name in TESTS:
        q = theoretical_rejection_rate(n, p, rules[name]["critical_k"])
        r = int(np.count_nonzero(tests[name]["reject_h0"]))
        row["tests"][name] = summarize_rejections(r, len(counts), q)
    z = tests["z"]["reject_h0"]
    exact = tests["binomial_exact"]["reject_h0"]
    row["paired_decisions"] = {
        "neither": int(np.count_nonzero(~z & ~exact)),
        "z_only": int(np.count_nonzero(z & ~exact)),
        "exact_only": int(np.count_nonzero(~z & exact)),
        "both": int(np.count_nonzero(z & exact)),
    }
    return row


def build_experiments(repetitions=REPETITIONS, seed=SEED):
    repetitions = positive_integer(repetitions, "repetitions")
    seed = validate_seed(seed)
    # A S02 lê o snapshot da S01 para validar n=42; não faz coleta nem inferência real.
    real_path = ROOT / "data/real_ci.csv"
    rows, source = load_real(real_path)
    if len(rows) != 42:
        raise ValueError("O protocolo da Issue #34 exige o snapshot S01 com n=42")
    scenarios = []
    for scenario in SCENARIOS:
        n = scenario["n"]
        scenarios.append({
            **scenario, "expected_failures_h0": n * P0,
            "expected_successes_h0": n * (1 - P0),
            "normal_rule_of_thumb": "n*p0 >= 10 and n*(1-p0) >= 10",
            "normal_rule_of_thumb_met": min(n * P0, n * (1 - P0)) >= 10,
            "rejection_rules": rejection_rules(n),
        })
    results = [simulate_cell(s, p, repetitions, seed) for s in scenarios for p in P_LEVELS]
    return {
        "schema_version": SCHEMA_VERSION, "scope": "Lab04S02 Q1 Q2 Q3; Issue #34",
        "protocol": {"p0": P0, "alpha": ALPHA, "alternative": "greater",
                     "decision_rule": "p_value < alpha", "seed": seed,
                     "repetitions": repetitions, "p_levels": list(P_LEVELS),
                     "effect_definition": "delta = p - p0", "effect_unit": "proportion",
                     "sampling_distribution": "Binomial(n,p), sum of n iid Bernoulli(p)",
                     "rng": "numpy.random.default_rng(SeedSequence([seed,n,p_numerator,p_denominator]))",
                     "bit_generator": "PCG64", "p_encoding": "Fraction(str(float(p)))",
                     "paired_tests": True, "null_reuse": "One row at p0 per scenario feeds Q1 and the Q2 origin",
                     "total_independent_samples": len(results) * repetitions},
        "source_s01": {"path": "data/real_ci.csv", "n": len(rows),
                       "csv_sha256": source["csv_sha256"], "use": "sample size only; no new collection or real-data inference"},
        "scenarios": scenarios, "rows": results,
        "g3": {"row_ids": [r["id"] for r in results if r["estimand"] == "type_i_error"],
               "nominal_rate": ALPHA, "y_field": "tests.<test>.rejection_rate"},
        "g4": {"row_ids": [r["id"] for r in results], "x_field": "delta",
               "y_field": "tests.<test>.rejection_rate", "series_fields": ["scenario_id", "test"],
               "zero_effect_note": "The null point is type I error, not power under an alternative"},
        "mc_validation": {"method": "exact binomial count intervals, Bonferroni",
                          "family_error_probability": 0.01, "comparison_count": len(results) * len(TESTS),
                          "ci95_note": "Wilson intervals are pointwise Monte Carlo uncertainty, not uncertainty about real CI failure p"},
        "software": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
    }
