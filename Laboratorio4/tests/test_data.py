import copy
import csv
import hashlib
import json
from pathlib import Path

import pytest

from src.collect import ROOT, select_runs
from src.data import load_real


def test_versioned_real_csv():
    rows, metadata = load_real(ROOT / "data/real_ci.csv")
    assert len(rows) >= 30
    assert len({x["run_id"] for x in rows}) == len(rows)
    assert len(rows) + sum(metadata["exclusions"].values()) == metadata["api_total_count"]
    assert rows == sorted(rows, key=lambda x: (x["created_at"], int(x["run_id"])), reverse=True)


def make_copy(tmp_path, mutation, rehash=True):
    source = ROOT / "data/real_ci.csv"
    with source.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fields, rows = reader.fieldnames, list(reader)
    mutation(rows)
    path = tmp_path / "real_ci.csv"
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    metadata = json.loads((ROOT / "data/source_metadata.json").read_text(encoding="utf-8"))
    if rehash:
        metadata["csv_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    (tmp_path / "source_metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
    return path


@pytest.mark.parametrize("field,value", [("run_id", "-1"), ("failed", "9"), ("event", "pull_request"),
                                         ("head_branch", "other"), ("status", "queued"),
                                         ("created_at", "2025-01-01T00:00:00Z"),
                                         ("html_url", "https://example.com"), ("head_sha", "x" * 40),
                                         ("run_attempt", "0"), ("conclusion", "cancelled")])
def test_rejects_invalid_records(tmp_path, field, value):
    path = make_copy(tmp_path, lambda rows: rows[0].update({field: value}))
    with pytest.raises(ValueError):
        load_real(path)


def test_rejects_duplicates(tmp_path):
    def duplicate(rows):
        rows[1] = dict(rows[0])
    with pytest.raises(ValueError, match="duplicado"):
        load_real(make_copy(tmp_path, duplicate))


def test_rejects_csv_tampering(tmp_path):
    with pytest.raises(ValueError, match="SHA256"):
        load_real(make_copy(tmp_path, lambda rows: rows.reverse(), rehash=False))


def test_rejects_too_few_records(tmp_path):
    with pytest.raises(ValueError, match="Quantidade"):
        load_real(make_copy(tmp_path, lambda rows: rows.__delitem__(slice(20, None))))


def api_fixture():
    metadata = json.loads((ROOT / "data/source_metadata.json").read_text(encoding="utf-8"))
    runs = []
    for row in metadata["audit"]:
        run = copy.deepcopy(row)
        run["id"] = run.pop("run_id")
        run["name"] = run.pop("workflow_name")
        runs.append(run)
    return runs


def test_collection_filters_and_deduplicates_without_network():
    runs = api_fixture()
    selected, audit = select_runs(runs + [copy.deepcopy(runs[0])])
    assert len(selected) == 42
    assert len(audit) == 46
    assert sum(row["failed"] for row in selected) == 4
    assert all(x["conclusion"] == "cancelled" for x in audit if x["selection"] != "included")


def test_collector_rejects_insufficient_and_out_of_scope():
    runs = api_fixture()
    with pytest.raises(ValueError, match="Somente"):
        select_runs(runs[:20])
    runs[0]["event"] = "pull_request"
    with pytest.raises(ValueError, match="recorte"):
        select_runs(runs)
