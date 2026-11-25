"""Executa o protocolo congelado da Lab05S02 em um diretório vazio."""

import argparse
import sqlite3
from pathlib import Path

from run_pilot import run


EXPECTED_SQLITE = "3.53.4"
CONFIG = {
    "rows": 50_000,
    "customers": 2_500,
    "queries": 50,
    "blocks": 3,
    "inserts": 500,
    "replications": 20,
    "seed": 20261125,
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir", type=Path,
        default=Path(__file__).resolve().parents[1] / "results" / "full_s02",
    )
    args = parser.parse_args()
    if sqlite3.sqlite_version != EXPECTED_SQLITE:
        parser.error(
            f"SQLite {EXPECTED_SQLITE} exigido pelo protocolo; instalado: {sqlite3.sqlite_version}"
        )
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        parser.error(f"Diretório de saída não está vazio: {args.output_dir}")
    run(argparse.Namespace(**CONFIG, output_dir=args.output_dir, scope="full_s02_data_no_inference"))


if __name__ == "__main__":
    main()
