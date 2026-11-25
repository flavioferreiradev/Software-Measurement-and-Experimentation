"""Valida independentemente os arquivos brutos da coleta Lab05S02."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

from run_full_s02 import CONFIG, EXPECTED_SQLITE


CONDITIONS = ("without_index", "with_index")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    return ordered[math.ceil(fraction * len(ordered)) - 1]


def checked_csv(path: Path, fields: set[str]) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        require(set(reader.fieldnames or ()) == fields, f"Cabeçalho inválido em {path.name}")
        rows = list(reader)
    require(all(None not in row and all(value != "" for value in row.values()) for row in rows),
            f"Célula ausente em {path.name}")
    return rows


def same_number(actual: float, expected: float, name: str) -> None:
    require(math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12),
            f"Resumo divergente em {name}: {actual} != {expected}")


def validate(
    output_dir: Path,
    expected_config: dict = CONFIG,
    expected_sqlite: str = EXPECTED_SQLITE,
) -> dict:
    output_dir = Path(output_dir)
    metadata = json.loads((output_dir / "metadata.json").read_text(encoding="utf-8"))
    summary = json.loads((output_dir / "summary.json").read_text(encoding="utf-8"))
    require(metadata["config"] == expected_config, "Configuração diferente do protocolo")
    require(metadata["environment"]["sqlite"] == expected_sqlite,
            "Versão do SQLite diferente do protocolo")
    require(metadata["data_type"] == "synthetic_no_personal_data", "Tipo de dados inesperado")

    pairs = expected_config["replications"]
    blocks = expected_config["blocks"]
    queries = expected_config["queries"]
    inserts = expected_config["inserts"]
    require(len(metadata["replications"]) == pairs, "Número de pares incorreto")
    initial_hashes = set()
    for pair, info in enumerate(metadata["replications"], start=1):
        require(info["replication"] == pair, f"ID do par incorreto: {pair}")
        require(info["seed"] == expected_config["seed"] + (pair - 1) * 1009,
                f"Semente incorreta no par {pair}")
        ids = info["query_customer_ids"]
        require(len(ids) == queries and len(set(ids)) == queries and
                all(isinstance(customer, int) and 0 <= customer < expected_config["customers"] for customer in ids),
                f"Clientes consultados inválidos no par {pair}")
        plans = info["query_plans"]
        require(any("SCAN orders" in step for step in plans["without_index"]),
                f"Plano sem índice inválido no par {pair}")
        require(any("idx_customer_created" in step for step in plans["with_index"]),
                f"Plano com índice inválido no par {pair}")
        require(info["final_rows"] == expected_config["rows"] + blocks * inserts,
                f"Contagem final incorreta no par {pair}")
        require(len(info["baseline_sha256"]) == 64 and len(info["final_sha256"]) == 64,
                f"Hash ausente no par {pair}")
        require(info["baseline_sha256"] not in initial_hashes,
                f"Dados iniciais repetidos no par {pair}")
        initial_hashes.add(info["baseline_sha256"])
        require(info["index_build_ms"] > 0, f"Tempo de construção inválido no par {pair}")
        require(all(info["database_bytes"][condition] > 0 for condition in CONDITIONS),
                f"Tamanho de banco inválido no par {pair}")

    reads = checked_csv(
        output_dir / "read_timings.csv",
        {"replication", "block", "position", "condition", "customer_id", "result_count", "duration_ns"},
    )
    writes = checked_csv(
        output_dir / "write_timings.csv",
        {"replication", "block", "condition", "batch_count", "duration_ns", "ns_per_row"},
    )
    require(len(reads) == pairs * blocks * queries * 2, "Número de consultas incorreto")
    require(len(writes) == pairs * blocks * 2, "Número de lotes incorreto")

    read_groups = defaultdict(list)
    for row in reads:
        key = (int(row["replication"]), int(row["block"]), row["condition"])
        require(key[2] in CONDITIONS, f"Condição de leitura inválida: {key}")
        require(int(row["duration_ns"]) > 0, f"Duração de leitura inválida: {key}")
        require(0 <= int(row["result_count"]) <= 20, f"Resultado de leitura inválido: {key}")
        read_groups[key].append(row)

    write_groups = defaultdict(list)
    for row in writes:
        key = (int(row["replication"]), int(row["block"]), row["condition"])
        require(key[2] in CONDITIONS, f"Condição de escrita inválida: {key}")
        require(int(row["batch_count"]) == inserts, f"Lote incompleto: {key}")
        duration = int(row["duration_ns"])
        require(duration > 0, f"Duração de escrita inválida: {key}")
        same_number(float(row["ns_per_row"]), duration / inserts, f"ns_per_row {key}")
        write_groups[key].append(row)

    for pair in range(1, pairs + 1):
        expected_ids = set(metadata["replications"][pair - 1]["query_customer_ids"])
        for block in range(1, blocks + 1):
            ordered = {}
            for condition in CONDITIONS:
                key = (pair, block, condition)
                group = read_groups[key]
                require(len(group) == queries, f"Consultas faltantes em {key}")
                group.sort(key=lambda row: int(row["position"]))
                require([int(row["position"]) for row in group] == list(range(1, queries + 1)),
                        f"Posições de consulta inválidas em {key}")
                require({int(row["customer_id"]) for row in group} == expected_ids,
                        f"IDs de cliente divergentes em {key}")
                require(len(write_groups[key]) == 1, f"Lote de escrita faltante ou duplicado em {key}")
                ordered[condition] = group
            for left, right in zip(ordered[CONDITIONS[0]], ordered[CONDITIONS[1]]):
                require(left["customer_id"] == right["customer_id"] and
                        left["result_count"] == right["result_count"],
                        f"Consultas não pareadas no par {pair}, bloco {block}")
    require(len(read_groups) == pairs * blocks * 2 and len(write_groups) == pairs * blocks * 2,
            "Há registros fora dos pares/blocos previstos")

    for condition in CONDITIONS:
        read_ms = [int(row["duration_ns"]) / 1_000_000 for row in reads if row["condition"] == condition]
        write_ms = [float(row["ns_per_row"]) / 1_000_000 for row in writes if row["condition"] == condition]
        sizes = [info["database_bytes"][condition] for info in metadata["replications"]]
        observed_read = summary["read_latency"][condition]
        observed_write = summary["write_latency"][condition]
        observed_size = summary["database_size"][condition]
        require(observed_read["n"] == len(read_ms) and observed_write["n_batches"] == len(write_ms),
                f"Contagens do resumo incorretas em {condition}")
        same_number(observed_read["median_ms"], statistics.median(read_ms),
                    f"mediana de leitura {condition}")
        same_number(observed_read["p95_ms"], percentile(read_ms, 0.95),
                    f"p95 de leitura {condition}")
        same_number(observed_write["median_ms_per_row"], statistics.median(write_ms),
                    f"mediana de escrita {condition}")
        same_number(observed_size["median_bytes"], statistics.median(sizes),
                    f"mediana de armazenamento {condition}")
    same_number(
        summary["index_build_median_ms"],
        statistics.median(info["index_build_ms"] for info in metadata["replications"]),
        "mediana de construção do índice",
    )
    expected_scope = (
        "full_s02_data_no_inference"
        if expected_config == CONFIG else "pilot_exploratory_not_final_inference"
    )
    require(summary["scope"] == expected_scope, "Escopo do resumo incorreto")

    source_files = ("read_timings.csv", "write_timings.csv", "metadata.json", "summary.json")
    report = {
        "status": "passed",
        "pairs": pairs,
        "read_records": len(reads),
        "write_batches": len(writes),
        "sqlite_version": metadata["environment"]["sqlite"],
        "source_sha256": {
            name: hashlib.sha256((output_dir / name).read_bytes()).hexdigest()
            for name in source_files
        },
    }
    (output_dir / "validation.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir", type=Path,
        default=Path(__file__).resolve().parents[1] / "results" / "full_s02",
    )
    args = parser.parse_args()
    try:
        report = validate(args.output_dir)
    except (KeyError, ValueError, OSError, json.JSONDecodeError) as error:
        parser.exit(1, f"Validação falhou: {error}\n")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
