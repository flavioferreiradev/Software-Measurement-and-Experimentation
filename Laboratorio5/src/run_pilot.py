"""Experimento piloto reproduzível: índice composto em consultas SQLite.

Uso: python3 Laboratorio5/src/run_pilot.py
Não requer pacotes externos. Os bancos temporários são gerados do zero.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
import random
import sqlite3
import statistics
import tempfile
import time
from pathlib import Path


SCHEMA = """CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    created_at INTEGER NOT NULL,
    amount_cents INTEGER NOT NULL,
    status INTEGER NOT NULL
)"""
INDEX = "CREATE INDEX idx_customer_created ON orders(customer_id, created_at DESC)"
QUERY = """SELECT order_id, created_at, amount_cents
FROM orders WHERE customer_id = ? ORDER BY created_at DESC LIMIT 20"""
CONDITIONS = ("without_index", "with_index")


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(fraction * len(ordered)) - 1)]


def generated_rows(count: int, customers: int, seed: int, first_id: int = 1):
    rng = random.Random(seed)
    for offset in range(count):
        order_id = first_id + offset
        yield (
            order_id,
            rng.randrange(customers),
            1_700_000_000 + order_id * 37,
            rng.randrange(500, 100_000),
            rng.randrange(4),
        )


def row_digest(rows: list[tuple[int, int, int, int, int]]) -> str:
    digest = hashlib.sha256()
    for row in rows:
        digest.update((",".join(map(str, row)) + "\n").encode("ascii"))
    return digest.hexdigest()


def make_database(path: Path, rows: list[tuple[int, int, int, int, int]], indexed: bool):
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA journal_mode=DELETE")
    connection.execute("PRAGMA synchronous=FULL")
    connection.execute("PRAGMA cache_size=-2000")
    connection.execute(SCHEMA)
    connection.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?)", rows)
    connection.commit()
    index_build_ns = None
    if indexed:
        start = time.perf_counter_ns()
        connection.execute(INDEX)
        connection.commit()
        index_build_ns = time.perf_counter_ns() - start
    return connection, index_build_ns


def assert_same_answers(connections: dict[str, sqlite3.Connection], customer_ids: list[int]):
    for customer_id in customer_ids:
        answers = [
            connections[condition].execute(QUERY, (customer_id,)).fetchall()
            for condition in CONDITIONS
        ]
        if answers[0] != answers[1]:
            raise AssertionError(f"Resultados diferentes para customer_id={customer_id}")


def run(config: argparse.Namespace) -> dict:
    if min(config.rows, config.customers, config.queries, config.blocks, config.replications, config.inserts) < 1:
        raise ValueError("Todos os parâmetros numéricos devem ser positivos")
    if config.queries > config.customers:
        raise ValueError("--queries não pode superar --customers")

    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    read_records: list[dict] = []
    write_records: list[dict] = []
    replications: list[dict] = []

    for replication in range(config.replications):
        replication_seed = config.seed + replication * 1009
        baseline = list(generated_rows(config.rows, config.customers, replication_seed))
        query_rng = random.Random(replication_seed + 17)
        customer_ids = query_rng.sample(range(config.customers), config.queries)

        with tempfile.TemporaryDirectory(prefix="lab05-sqlite-") as temp:
            paths = {condition: Path(temp) / f"{condition}.db" for condition in CONDITIONS}
            connections = {}
            index_build_ns = None
            try:
                for condition in CONDITIONS:
                    connection, build_ns = make_database(
                        paths[condition], baseline, indexed=condition == "with_index"
                    )
                    connections[condition] = connection
                    if build_ns is not None:
                        index_build_ns = build_ns

                plans = {
                    condition: [row[3] for row in connections[condition].execute(
                        "EXPLAIN QUERY PLAN " + QUERY, (customer_ids[0],)
                    )]
                    for condition in CONDITIONS
                }
                if not any("SCAN orders" in step for step in plans["without_index"]):
                    raise AssertionError("A condição sem índice não fez SCAN orders")
                if not any("idx_customer_created" in step for step in plans["with_index"]):
                    raise AssertionError("A condição com índice não usou idx_customer_created")

                for block in range(config.blocks):
                    query_order = customer_ids.copy()
                    query_rng.shuffle(query_order)
                    condition_order = CONDITIONS if (replication + block) % 2 == 0 else CONDITIONS[::-1]

                    # Validação e aquecimento iguais antes de cada bloco medido.
                    assert_same_answers(connections, query_order[: min(10, len(query_order))])
                    for condition in CONDITIONS:
                        for customer_id in query_order[: min(10, len(query_order))]:
                            connections[condition].execute(QUERY, (customer_id,)).fetchall()

                    for condition in condition_order:
                        connection = connections[condition]
                        for position, customer_id in enumerate(query_order):
                            start = time.perf_counter_ns()
                            result = connection.execute(QUERY, (customer_id,)).fetchall()
                            duration_ns = time.perf_counter_ns() - start
                            read_records.append({
                                "replication": replication + 1,
                                "block": block + 1,
                                "position": position + 1,
                                "condition": condition,
                                "customer_id": customer_id,
                                "result_count": len(result),
                                "duration_ns": duration_ns,
                            })

                    first_id = config.rows + block * config.inserts + 1
                    new_rows = list(generated_rows(
                        config.inserts, config.customers, replication_seed + 100_000 + block,
                        first_id=first_id,
                    ))
                    for condition in condition_order[::-1]:
                        connection = connections[condition]
                        start = time.perf_counter_ns()
                        connection.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?)", new_rows)
                        connection.commit()
                        duration_ns = time.perf_counter_ns() - start
                        write_records.append({
                            "replication": replication + 1,
                            "block": block + 1,
                            "condition": condition,
                            "batch_count": config.inserts,
                            "duration_ns": duration_ns,
                            "ns_per_row": duration_ns / config.inserts,
                        })
                    assert_same_answers(connections, query_order[: min(10, len(query_order))])

                expected_rows = config.rows + config.blocks * config.inserts
                for condition in CONDITIONS:
                    actual_rows = connections[condition].execute("SELECT count(*) FROM orders").fetchone()[0]
                    if actual_rows != expected_rows:
                        raise AssertionError(f"Contagem incorreta em {condition}: {actual_rows}")
                    connections[condition].close()
                connections.clear()
                replications.append({
                    "replication": replication + 1,
                    "seed": replication_seed,
                    "baseline_sha256": row_digest(baseline),
                    "query_customer_ids": customer_ids,
                    "query_plans": plans,
                    "index_build_ms": index_build_ns / 1_000_000 if index_build_ns is not None else None,
                    "database_bytes": {condition: paths[condition].stat().st_size for condition in CONDITIONS},
                    "final_rows": expected_rows,
                })
            finally:
                for connection in connections.values():
                    connection.close()

    with (output_dir / "read_timings.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(read_records[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(read_records)
    with (output_dir / "write_timings.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(write_records[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(write_records)

    read_summary = {}
    write_summary = {}
    size_summary = {}
    for condition in CONDITIONS:
        read_ms = [row["duration_ns"] / 1_000_000 for row in read_records if row["condition"] == condition]
        write_ms = [row["ns_per_row"] / 1_000_000 for row in write_records if row["condition"] == condition]
        sizes = [row["database_bytes"][condition] for row in replications]
        read_summary[condition] = {
            "n": len(read_ms), "median_ms": statistics.median(read_ms),
            "p95_ms": percentile(read_ms, 0.95),
        }
        write_summary[condition] = {"n_batches": len(write_ms), "median_ms_per_row": statistics.median(write_ms)}
        size_summary[condition] = {"median_bytes": statistics.median(sizes)}

    summary = {
        "scope": "pilot_exploratory_not_final_inference",
        "read_latency": read_summary,
        "write_latency": write_summary,
        "database_size": size_summary,
        "index_build_median_ms": statistics.median(
            row["index_build_ms"] for row in replications
        ),
    }
    metadata = {
        "config": {key: value for key, value in vars(config).items() if key != "output_dir"},
        "environment": {
            "python": platform.python_version(),
            "sqlite": sqlite3.sqlite_version,
            "platform": platform.platform(),
            "journal_mode": "DELETE", "synchronous": "FULL", "cache_size_kib": 2000,
        },
        "schema": SCHEMA, "index": INDEX, "query": QUERY,
        "data_type": "synthetic_no_personal_data",
        "replications": replications,
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return summary


def parse_args() -> argparse.Namespace:
    default_output = Path(__file__).resolve().parents[1] / "results" / "pilot_s01"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=20_000)
    parser.add_argument("--customers", type=int, default=1_000)
    parser.add_argument("--queries", type=int, default=30)
    parser.add_argument("--blocks", type=int, default=2)
    parser.add_argument("--inserts", type=int, default=100)
    parser.add_argument("--replications", type=int, default=3)
    parser.add_argument("--seed", type=int, default=20261118)
    parser.add_argument("--output-dir", type=Path, default=default_output)
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
