"""Uma demonstração S01 offline; exporta o contrato G1/G2, sem criar gráficos."""

import argparse
import csv
import json
from pathlib import Path
import platform

import numpy as np
import scipy
from scipy.stats import binom, norm

from .collect import ROOT
from .data import load_real
from .statistics import generate_sample, test_proportion


def null_distributions(result):
    """Referências analíticas G2; não executa estudos Monte Carlo da S02."""
    n, k, p0, alpha = (result[key] for key in ("n", "k", "p0", "alpha"))
    z = result["tests"]["z"]["statistic"]
    z_critical = float(norm.isf(alpha))
    x = np.linspace(min(-4.0, z - 1), max(4.0, z + 1, z_critical + 1), 801)
    support = np.arange(n + 1)
    pmf = binom.pmf(support, n, p0)
    tails = binom.sf(support - 1, n, p0)
    reject = tails < alpha
    critical = int(support[reject][0]) if reject.any() else None
    # Z é discreto em amostras finitas; N(0,1) é a aproximação usada pelo teste.
    actual_z = (support / n - p0) / result["tests"]["z"]["standard_error_h0"]
    return {
        "z": {"reference_distribution": "N(0,1) approximation", "x_unit": "standard_deviations",
              "y_unit": "probability_density", "x": x.tolist(), "pdf": norm.pdf(x).tolist(),
              "observed": z, "critical_value": z_critical, "rejection_rule": "Z > critical_value",
              "p_value_tail": {"lower": z, "upper": "+infinity", "area": result["tests"]["z"]["p_value"]},
              "critical_tail": {"lower": z_critical, "upper": "+infinity", "area": alpha},
              "finite_sample_null": {"z_support": actual_z.tolist(), "pmf": pmf.tolist(),
                                     "note": "Distribuição discreta real de Z sob p=p0; a curva normal é apenas aproximação."}},
        "binomial_exact": {"reference_distribution": "Binomial(n,p0)", "n": n, "p0": p0,
                           "x_unit": "failure_count", "y_unit": "probability_mass",
                           "k_support": support.tolist(), "p_hat_support": (support / n).tolist(),
                           "pmf": pmf.tolist(), "right_tail_inclusive": tails.tolist(),
                           "observed_k": k, "observed_p_hat": k / n, "critical_k": critical,
                           "rejection_rule": "K >= critical_k (empty if null)",
                           "rejection_mask": reject.tolist(), "p_value_mask": (support >= k).tolist(),
                           "p_value_area": result["tests"]["binomial_exact"]["p_value"],
                           "critical_area": float(pmf[reject].sum()),
                           "tail_includes_observed": True},
    }


def build_artifact(real_path=ROOT / "data" / "real_ci.csv", n=None, p=None, seed=42, p0=0.05, alpha=0.05):
    rows, metadata = load_real(real_path)
    real = [int(row["failed"]) for row in rows]
    empirical_n = len(real)
    empirical_k = sum(real)
    empirical_p = empirical_k / empirical_n
    sample = generate_sample(empirical_n if n is None else n, empirical_p if p is None else p, seed)
    result = test_proportion(sample, p0, alpha)
    return {
        "schema_version": "1.0.0", "scope": "Lab04S01 single simulated sample",
        "scenario": {"pair": "P4", "question_pt": "A proporção de execuções de CI com falha supera a meta de 5%?",
                     "h0": "p <= p0", "h1": "p > p0", "p0": p0, "alpha": alpha,
                     "alternative": "greater", "decision_rule": "p_value < alpha",
                     "variable": "failed", "coding": {"0": "success", "1": "failure or timed_out"},
                     "sample_unit": "one completed workflow run.id (latest available attempt)"},
        "source": {key: metadata[key] for key in ("repository", "workflow_id", "workflow_path", "workflow_url",
                   "branch", "event", "created_window", "observed_period", "collected_at_utc", "csv_sha256")},
        "empirical": {"n": empirical_n, "k": empirical_k, "p_hat": empirical_p,
                      "bernoulli_variance": empirical_p * (1 - empirical_p)},
        "generator": {"distribution": "Bernoulli", "numpy_api": "numpy.random.default_rng(seed).binomial(1,p,size=n)",
                      "n": result["n"], "p": empirical_p if p is None else float(p), "seed": int(seed),
                      "n_source": "empirical.n" if n is None else "CLI override",
                      "p_source": "empirical.p_hat" if p is None else "CLI override"},
        "g1": {"variable": "failed", "unit": "binary outcome per run", "bin_edges": [-0.5, 0.5, 1.5],
               "labels": ["Sucesso (0)", "Falha (1)"], "real": {"values": real, "counts": [empirical_n - empirical_k, empirical_k]},
               "simulated": {"values": sample.tolist(), "counts": [result["n"] - result["k"], result["k"]]},
               "recommended_y_unit": "relative_frequency"},
        "example": result,
        "g2": null_distributions(result),
        "software": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
    }


def write_artifact(artifact, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    (output / "demo_s01.json").write_text(json.dumps(artifact, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    with (output / "simulated_sample.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["observation", "failed"])
        writer.writerows(enumerate(artifact["g1"]["simulated"]["values"], start=1))
    result = artifact["example"]
    lines = ["# Demonstração S01 (gerada automaticamente)", "",
             f"n={result['n']}; k={result['k']}; proporção={result['p_hat']:.6f}; p₀={result['p0']}; α={result['alpha']}.", "",
             "| Teste | Estatística | p-valor | Rejeitar H₀? |", "|---|---:|---:|---|"]
    for name, test in result["tests"].items():
        lines += [f"| {name} | {test['statistic']:.9f} | {test['p_value']:.9f} | {'Sim' if test['reject_h0'] else 'Não'} |"]
    lines += [""] + [f"- {name}: {test['interpretation_pt']}" for name, test in result["tests"].items()]
    lines += ["", "O exemplo é simulado, não uma conclusão inferencial sobre o projeto fonte.",
              "A previsão de desempenho continua pendente de avaliação na S02.", ""]
    (output / "demo_interpretation.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--real", type=Path, default=ROOT / "data" / "real_ci.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "results")
    parser.add_argument("--n", type=int)
    parser.add_argument("--p", type=float)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    artifact = build_artifact(args.real, args.n, args.p, args.seed)
    write_artifact(artifact, args.output)
    print(f"Artefatos S01 em {args.output}; n={artifact['example']['n']}, k={artifact['example']['k']}")


if __name__ == "__main__":
    main()
