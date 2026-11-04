"""Leitura e validação estrita do contrato de dados reais."""

import csv
from datetime import datetime
import hashlib
import json
from pathlib import Path

from .collect import CLASSIFICATION, FIELDS


def load_real(path, metadata_path=None):
    path = Path(path)
    metadata_path = Path(metadata_path) if metadata_path else path.with_name("source_metadata.json")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if hashlib.sha256(path.read_bytes()).hexdigest() != metadata["csv_sha256"]:
        raise ValueError("SHA256 do CSV difere da coleta registrada")
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != FIELDS:
            raise ValueError("Cabeçalho do CSV incompatível")
        rows = list(reader)
    if len(rows) < 30 or len(rows) != metadata["valid_count"]:
        raise ValueError("Quantidade de observações reais inválida")
    ids = set()
    audit = {str(x["run_id"]): x for x in metadata["audit"] if x["selection"] == "included"}
    for row in rows:
        run_id = row["run_id"]
        if not run_id.isdigit() or int(run_id) <= 0 or run_id in ids:
            raise ValueError("Identificador inválido ou duplicado")
        ids.add(run_id)
        if row["conclusion"] not in CLASSIFICATION or row["failed"] != str(CLASSIFICATION[row["conclusion"]]):
            raise ValueError("Classificação inválida")
        for field, expected in (("repository", metadata["repository"]), ("workflow_id", str(metadata["workflow_id"])),
                                ("head_branch", metadata["branch"]), ("event", metadata["event"]),
                                ("status", "completed")):
            if row[field] != expected:
                raise ValueError(f"Recorte inválido: {field}")
        if row["html_url"] != f"https://github.com/{metadata['repository']}/actions/runs/{run_id}":
            raise ValueError("Referência da execução inválida")
        created = datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
        start, end = (datetime.fromisoformat(metadata["created_window"][key].replace("Z", "+00:00")) for key in ("start", "end"))
        if created.tzinfo is None or not start <= created <= end:
            raise ValueError("Data fora da janela")
        if len(row["head_sha"]) != 40 or any(c not in "0123456789abcdef" for c in row["head_sha"]):
            raise ValueError("Commit SHA inválido")
        if not row["run_attempt"].isdigit() or int(row["run_attempt"]) < 1:
            raise ValueError("Tentativa inválida")
        if run_id not in audit or any(str(audit[run_id][key]) != row[key] for key in FIELDS):
            raise ValueError("CSV diverge da auditoria normalizada")
    if ids != set(audit):
        raise ValueError("Execuções incluídas divergem da auditoria")
    return rows, metadata
