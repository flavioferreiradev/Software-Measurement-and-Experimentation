"""Reproduz S01, S02 e inferência real com uma semente fixa, sem rede."""

import argparse
import json
from pathlib import Path

from .collect import ROOT
from .data import load_real
from .experiments import build_experiments
from .run_demo import build_artifact, write_artifact
from .run_experiments import write_experiments
from .statistics import test_proportion


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / ".pytest-tmp" / "lab04-full",
                        help="Diretório de reprodução; os snapshots oficiais não são sobrescritos")
    args = parser.parse_args()
    s01 = build_artifact(seed=42)
    s02 = build_experiments(seed=42)
    rows, metadata = load_real(ROOT / "data" / "real_ci.csv")
    real = test_proportion([int(row["failed"]) for row in rows],
                           p0=s01["scenario"]["p0"], alpha=s01["scenario"]["alpha"])
    output = args.output
    write_artifact(s01, output / "s01")
    write_experiments(s02, output / "s02")
    (output / "real_analysis.json").write_text(json.dumps({
        "schema_version": "1.0.0", "source": "data/real_ci.csv",
        "csv_sha256": metadata["csv_sha256"], "result": real,
    }, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    print(f"Lab04 reproduzido em {output}: S01, 12 células S02 e análise real n={real['n']}, k={real['k']}.")


if __name__ == "__main__":
    main()
