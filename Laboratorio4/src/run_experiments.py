"""Comando offline da S02: apenas artefatos novos, sem modificar resultados S01."""

import argparse
import csv
import json
from pathlib import Path

from .collect import ROOT
from .experiments import REPETITIONS, SEED, TESTS, build_experiments


def write_experiments(artifact, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    (output / "experiments_s02.json").write_text(
        json.dumps(artifact, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8", newline="\n")
    columns = ["scenario_id", "n", "p", "delta", "estimand", "repetitions", "test",
               "rejections", "rejection_rate", "mc_standard_error", "theoretical_rejection_rate",
               "mc_ci95_low", "mc_ci95_high", "mc_consistent_with_theory"]
    with (output / "experiments_s02.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row in artifact["rows"]:
            for name in TESTS:
                test = row["tests"][name]
                record = {key: row[key] for key in columns[:6]}
                record.update({key: test[key] for key in ("rejections", "rejection_rate", "mc_standard_error",
                                                         "theoretical_rejection_rate", "mc_consistent_with_theory")})
                record.update(test=name, mc_ci95_low=test["mc_ci95_wilson"][0], mc_ci95_high=test["mc_ci95_wilson"][1])
                writer.writerow(record)
    lines = ["# Resultados executados — Lab04S02 / #34", "",
             f"Seed={artifact['protocol']['seed']}; {artifact['protocol']['repetitions']} repetições por (n,p).",
             "Δ=p−p₀ em proporção; p₀=0,05; α=0,05; rejeição estrita p-valor<α.", "",
             "| Situação | p | Δ | Tipo | Rejeições Z | Taxa Z | Rejeições exato | Taxa exato |",
             "|---|---:|---:|---|---:|---:|---:|---:|"]
    for row in artifact["rows"]:
        z, exact = (row["tests"][name] for name in TESTS)
        lines.append(f"| {row['scenario_id']} | {row['p']:g} | {row['delta']:g} | {row['estimand']} | "
                     f"{z['rejections']} | {z['rejection_rate']:.4f} | {exact['rejections']} | {exact['rejection_rate']:.4f} |")
    lines += ["", "## Q1: confronto com a teoria", "",
              "| n | Teste | Taxa simulada | Probabilidade teórica | IC MC 95% (Wilson) | Compatível MC* |",
              "|---:|---|---:|---:|---|---|"]
    for row in artifact["rows"]:
        if row["estimand"] == "type_i_error":
            for name in TESTS:
                test = row["tests"][name]
                low, high = test["mc_ci95_wilson"]
                lines.append(f"| {row['n']} | {name} | {test['rejection_rate']:.4f} | "
                             f"{test['theoretical_rejection_rate']:.9f} | [{low:.6f}, {high:.6f}] | "
                             f"{test['mc_consistent_with_theory']} |")
    passed = sum(test["mc_consistent_with_theory"] for row in artifact["rows"] for test in row["tests"].values())
    lines += ["", f"*Confronto por intervalos binomiais exatos de contagem, com Bonferroni para {artifact['mc_validation']['comparison_count']} "
              f"estimativas e erro familiar máximo de 1%: {passed}/{artifact['mc_validation']['comparison_count']} compatíveis.",
              "", "As diferenças pequenas podem ser ruído Monte Carlo; a probabilidade teórica usa a região de rejeição real de cada teste.",
              "n=42 tem n·p₀=2,1 e aproximação normal inadequada pela regra prática. n=200 tem n·p₀=10, no limite da regra.",
              "A Q3 compara essas duas situações; em ambas o modelo gerador continua binomial iid.",
              "O binomial exato pode ser conservador pela discretização. Comparar poder exige considerar o erro tipo I realizado.",
              "G3/G4, inferência dos dados reais e conclusão geral pertencem ao Flávio.", ""]
    (output / "experiments_s02_summary.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "results")
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--repetitions", type=int, default=REPETITIONS,
                        help="Entrega oficial: 10000; outros valores são execuções exploratórias")
    args = parser.parse_args()
    try:
        artifact = build_experiments(args.repetitions, args.seed)
    except ValueError as error:
        parser.error(str(error))
    write_experiments(artifact, args.output)
    total = artifact["protocol"]["total_independent_samples"]
    print(f"S02: {len(artifact['rows'])} células, {total} amostras pareadas; artefatos em {args.output}")


if __name__ == "__main__":
    main()
