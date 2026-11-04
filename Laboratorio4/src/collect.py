"""Coleta pequena e auditável; não é usada pela reprodução offline."""

import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "pytest-dev/pytest"
WORKFLOW_ID = 22158026
START = "2026-10-01T00:00:00Z"
END = "2026-11-04T18:00:00Z"
FIELDS = ["run_id", "repository", "workflow_id", "workflow_name", "head_branch",
          "event", "status", "conclusion", "failed", "run_attempt", "created_at",
          "updated_at", "head_sha", "html_url"]
CLASSIFICATION = {"success": 0, "failure": 1, "timed_out": 1}


def fetch_json(url):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "Lab04S01",
               "X-GitHub-Api-Version": "2022-11-28"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with urlopen(Request(url, headers=headers), timeout=30) as response:
        return json.load(response)


def normalize(run):
    """Preserva apenas metadados públicos necessários, sem atores/credenciais."""
    return {"run_id": run["id"], "repository": REPOSITORY,
            **{key: run[key] for key in ("workflow_id", "head_branch", "event", "status",
                                        "conclusion", "run_attempt", "created_at",
                                        "updated_at", "head_sha", "html_url")},
            "workflow_name": run["name"],
            "failed": CLASSIFICATION.get(run["conclusion"])}


def select_runs(runs, limit=60):
    """Seleciona por tempo, nunca pelo resultado; audita todos os descartes."""
    unique = {}
    for run in runs:
        if (run["workflow_id"] != WORKFLOW_ID or run["head_branch"] != "main"
                or run["event"] != "push" or run["status"] != "completed"
                or not START <= run["created_at"] <= END):
            raise ValueError("API retornou execução fora do recorte solicitado")
        previous = unique.get(run["id"])
        if previous is None or run["run_attempt"] > previous["run_attempt"]:
            unique[run["id"]] = run
    audit = []
    selected = []
    for run in sorted(unique.values(), key=lambda x: (x["created_at"], x["id"]), reverse=True):
        row = normalize(run)
        reason = ("excluded_conclusion" if row["failed"] is None else
                  "outside_latest_60" if len(selected) >= limit else "included")
        audit.append({**row, "selection": reason})
        if reason == "included":
            selected.append(row)
    if len(selected) < 30:
        raise ValueError(f"Somente {len(selected)} válidas: registrar revisão da janela antes de prosseguir")
    return selected, audit


def collect(output=ROOT / "data"):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    requests = []
    runs = []
    page = 1
    total = None
    while True:
        query = urlencode({"branch": "main", "event": "push", "status": "completed",
                           "created": f"{START}..{END}", "per_page": 100, "page": page})
        url = f"https://api.github.com/repos/{REPOSITORY}/actions/workflows/{WORKFLOW_ID}/runs?{query}"
        payload = fetch_json(url)
        requests.append(url)
        total = payload["total_count"]
        if total >= 1000:
            raise ValueError("Janela excede o limite da API; subdivisão seria necessária")
        batch = payload["workflow_runs"]
        runs.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    selected, audit = select_runs(runs)
    csv_path = output / "real_ci.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(selected)
    metadata = {
        "schema_version": "1.0.0", "repository": REPOSITORY,
        "workflow_id": WORKFLOW_ID, "workflow_path": ".github/workflows/test.yml",
        "workflow_url": f"https://github.com/{REPOSITORY}/actions/workflows/test.yml",
        "branch": "main", "event": "push", "created_window": {"start": START, "end": END},
        "collected_at_utc": datetime.now(timezone.utc).isoformat(), "api_requests": requests,
        "api_total_count": total, "received_count": len(runs),
        "duplicate_count": len(runs) - len(audit), "valid_count": len(selected),
        "selection_rule": "latest 60 valid by (created_at,id) descending; all if 30..59",
        "classification": CLASSIFICATION,
        "exclusions": dict(Counter(x["conclusion"] for x in audit if x["selection"] == "excluded_conclusion")),
        "observed_period": {"start": min(x["created_at"] for x in selected),
                            "end": max(x["created_at"] for x in selected)},
        "csv_sha256": hashlib.sha256(csv_path.read_bytes()).hexdigest(),
        "attempt_policy": "latest available attempt per run.id at collection time",
        "audit": audit,
    }
    (output / "source_metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{len(selected)} observações reais em {csv_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "data")
    collect(parser.parse_args().output)
