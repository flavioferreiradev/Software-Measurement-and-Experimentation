"""Analisa somente a coleta existente da S02; Python 3.10+, sem dependências."""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import math
import statistics as st
import tempfile
from collections import defaultdict
from pathlib import Path

from validate_full_s02 import CONDITIONS, percentile, require, validate

ROOT = Path(__file__).resolve().parents[1]
SOURCE_FILES = ("read_timings.csv", "write_timings.csv", "metadata.json", "summary.json")
# Direção: benefício positivo em leitura; custo positivo em escrita e disco.
METRICS = {
    "read_median_ms": ("Leitura: mediana", "ms/consulta", True),
    "read_p95_ms": ("Leitura: p95", "ms/consulta", True),
    "write_ms_per_row": ("Inserção em lote", "ms/linha", False),
    "database_bytes": ("Arquivo final", "bytes", False),
}


def describe(values: list[float]) -> dict:
    """Quantis nearest-rank, exceto mediana (média dos centrais se n par)."""
    return {
        "n": len(values), "median": st.median(values), "mean": st.mean(values),
        "sd": st.stdev(values) if len(values) > 1 else 0.0,
        "q25": percentile(values, .25), "q75": percentile(values, .75),
        "iqr": percentile(values, .75) - percentile(values, .25),
        "p95": percentile(values, .95), "min": min(values), "max": max(values),
    }


def median_ci(values: list[float], confidence: float = .95) -> dict:
    """IC bilateral da mediana por estatísticas de ordem/binomial exata.

    Escolhe maior k com 2 P(Bin(n,.5) <= k-1) <= 1-confidence.
    Válido conservadoramente para empates; não exige simetria ou normalidade.
    """
    ordered = sorted(values)
    n = len(ordered)
    require(n > 0 and 0 < confidence < 1, "IC exige amostra e confiança válidas")
    choices = []
    for k in range(1, (n + 1) // 2 + 1):
        coverage = 1 - 2 * sum(math.comb(n, j) for j in range(k)) / 2**n
        if coverage >= confidence:
            choices.append((k, coverage))
    if not choices:
        return {"low": None, "high": None, "coverage_at_least": 1.0,
                "lower_order": 0, "upper_order": n + 1,
                "note": "Amostra insuficiente: intervalo ilimitado"}
    k, coverage = choices[-1]
    return {"low": ordered[k - 1], "high": ordered[n - k],
            "coverage_at_least": coverage, "lower_order": k, "upper_order": n + 1 - k}


def sign_test_greater(differences: list[float]) -> dict:
    """H0: mediana(D)<=0. Zeros retidos como não positivos: conservador."""
    n = len(differences)
    require(n > 0 and all(math.isfinite(x) for x in differences), "Diferenças inválidas")
    positive = sum(x > 0 for x in differences)
    negative = sum(x < 0 for x in differences)
    return {"n_pairs": n, "positive": positive, "negative": negative,
            "zero": n - positive - negative,
            "p_one_sided": sum(math.comb(n, j) for j in range(positive, n + 1)) / 2**n,
            "alpha": .05, "null": "median(without_index - with_index) <= 0",
            "alternative": "median(without_index - with_index) > 0",
            "method": "exact_binomial_sign_test_zeros_retained_as_nonpositive"}


def audited_input(source: Path) -> tuple[dict, dict, list, list]:
    """Revalida em cópia temporária, preservando todos os arquivos da coleta."""
    original = json.loads((source / "validation.json").read_text(encoding="utf-8"))
    checkout_hashes, normalized = {}, []
    with tempfile.TemporaryDirectory(prefix="lab05-analysis-") as directory:
        for name in SOURCE_FILES:
            raw = (source / name).read_bytes()
            checkout_hashes[name] = hashlib.sha256(raw).hexdigest()
            expected = original["source_sha256"][name]
            if checkout_hashes[name] != expected:
                raw = raw.replace(b"\r\n", b"\n")
                require(hashlib.sha256(raw).hexdigest() == expected,
                        f"Hash divergente mesmo após CRLF→LF: {name}")
                normalized.append(name)
            (Path(directory) / name).write_bytes(raw)
        checked = validate(Path(directory))
    require(checked == original, "Validação/hashes divergem da coleta publicada")
    audit = {"collection_commit": "dd31f1e", "revalidation": checked,
             "checkout_sha256": checkout_hashes, "crlf_to_lf_in_temporary_copy": normalized,
             "validation_sha256": hashlib.sha256((source / "validation.json").read_bytes()).hexdigest(),
             "raw_files_modified": False}
    metadata = json.loads((source / "metadata.json").read_text(encoding="utf-8"))
    def read_csv(name):
        with (source / name).open(newline="", encoding="utf-8") as stream:
            return list(csv.DictReader(stream))
    return metadata, audit, read_csv("read_timings.csv"), read_csv("write_timings.csv")


def aggregate_pairs(metadata: dict, reads: list[dict], writes: list[dict]) -> list[dict]:
    read_groups, write_groups = defaultdict(list), defaultdict(list)
    for row in reads:
        read_groups[int(row["replication"]), row["condition"]].append(int(row["duration_ns"]) / 1e6)
    for row in writes:
        write_groups[int(row["replication"]), row["condition"]].append(row)
    pairs = []
    for info in metadata["replications"]:
        pair = {"pair": info["replication"], "seed": info["seed"],
                "index_build_ms": info["index_build_ms"]}
        for condition in CONDITIONS:
            key = (info["replication"], condition)
            r = describe(read_groups[key])
            batches = write_groups[key]
            total_ns = sum(int(row["duration_ns"]) for row in batches)
            total_rows = sum(int(row["batch_count"]) for row in batches)
            w = describe([int(row["duration_ns"]) / int(row["batch_count"]) / 1e6 for row in batches])
            for field, value in r.items():
                pair[f"read_{field}_{condition}"] = value
            for field, value in w.items():
                pair[f"write_batch_{field}_{condition}"] = value
            pair[f"read_median_ms_{condition}"] = r["median"]
            pair[f"read_p95_ms_{condition}"] = r["p95"]
            pair[f"write_total_ns_{condition}"] = total_ns
            pair[f"write_rows_{condition}"] = total_rows
            pair[f"write_ms_per_row_{condition}"] = total_ns / total_rows / 1e6
            pair[f"database_bytes_{condition}"] = info["database_bytes"][condition]
        for metric, (_, _, benefit) in METRICS.items():
            a, b = (pair[f"{metric}_{c}"] for c in CONDITIONS)
            pair[f"{metric}_difference"] = a - b if benefit else b - a
            pair[f"{metric}_ratio"] = a / b if benefit else b / a
            pair[f"{metric}_change_pct"] = 100 * (b / a - 1)
        pairs.append(pair)
    return pairs


def summarize(pairs: list[dict]) -> dict:
    metrics = {}
    for metric, (label, unit, benefit) in METRICS.items():
        groups = {
            "without_index": [p[f"{metric}_without_index"] for p in pairs],
            "with_index": [p[f"{metric}_with_index"] for p in pairs],
            "difference": [p[f"{metric}_difference"] for p in pairs],
            "ratio": [p[f"{metric}_ratio"] for p in pairs],
            "change_pct": [p[f"{metric}_change_pct"] for p in pairs],
        }
        metrics[metric] = {"label": label, "unit": unit,
                           "direction": "without/with; without-with" if benefit else "with/without; with-without",
                           "descriptive": {name: describe(v) for name, v in groups.items()},
                           "median_ci": {name: median_ci(v) for name, v in groups.items()},
                           "positive_differences": sum(x > 0 for x in groups["difference"])}
    differences = [p["read_median_ms_difference"] for p in pairs]
    test = sign_test_greater(differences)
    test["reject_at_alpha"] = test["p_one_sided"] < test["alpha"]
    return {"scope": "20_paired_databases_synthetic_single_machine",
            "n_independent_pairs": len(pairs), "metrics": metrics,
            "primary_test": test,
            "primary_effect": {
                "median_difference_ms": st.median(differences),
                "median_difference_ci": median_ci(differences),
                "paired_sign_dominance": (test["positive"] - test["negative"]) / len(pairs),
                "paired_sign_dominance_definition": "(positive-negative)/all_pairs; range [-1,1]",
            },
            "index_build_ms": describe([p["index_build_ms"] for p in pairs]),
            "quantile_method": "nearest_rank; median averages central two for even n",
            "interval_method": "two_sided_order_statistics_median; nominal .95; pointwise",
            "write_estimand": "sum(batch duration_ns) / sum(batch_count) / 1e6 in each pair"}


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def svg_start(title: str, subtitle: str, width=1120, height=760) -> list[str]:
    return [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            f'<title>{html.escape(title)}</title><desc>{html.escape(subtitle)}</desc>',
            '<rect width="100%" height="100%" fill="#fafbfc"/>',
            '<style>text{font-family:Arial,sans-serif;fill:#192b3b;font-size:14px}.small{font-size:12px}.heading{font-size:22px;font-weight:bold}</style>',
            f'<text x="40" y="36" class="heading">{html.escape(title)}</text>',
            f'<text x="40" y="61">{html.escape(subtitle)}</text>']


def paired_plot(pairs: list[dict], path: Path) -> None:
    out = svg_start("Índice composto: observações nos 20 pares", "Cada linha liga os dois bancos do mesmo par. Leituras aquecidas; carga sintética, uma máquina.")
    specs = [("read_median_ms", "Mediana de leitura (ms/consulta)", True),
             ("read_p95_ms", "p95 de leitura (ms/consulta)", True),
             ("write_ms_per_row", "Inserção em lote (ms/linha)", False),
             ("database_bytes", "Tamanho final (MiB)", False)]
    for i, (metric, title, log) in enumerate(specs):
        x, top = 95 + (i % 2) * 550, 130 + (i // 2) * 310
        factor = 2**20 if metric == "database_bytes" else 1
        values = [p[f"{metric}_{c}"] / factor for p in pairs for c in CONDITIONS]
        transform = math.log10 if log else lambda v: v
        lo = math.floor(math.log10(min(values))) if log else 0
        hi = math.ceil(math.log10(max(values))) if log else max(values) * 1.12
        y = lambda v: top + 200 - (transform(v) - lo) / (hi - lo) * 200
        out.append(f'<text x="{x-45}" y="{top-24}">{title}{" — escala log" if log else ""}</text>')
        ticks = [10**v for v in range(lo, hi + 1)] if log else [hi * j / 4 for j in range(5)]
        for tick in ticks:
            yy = y(tick)
            out.extend([f'<line x1="{x}" y1="{yy:.2f}" x2="{x+340}" y2="{yy:.2f}" stroke="#dae1e7"/>',
                        f'<text x="{x-9}" y="{yy+4:.2f}" text-anchor="end" class="small">{tick:.3g}</text>'])
        for p in pairs:
            a, b = [p[f"{metric}_{c}"] / factor for c in CONDITIONS]
            out.append(f'<g><title>Par {p["pair"]}: sem={a:.9g}; com={b:.9g}</title><line x1="{x+40}" y1="{y(a):.2f}" x2="{x+300}" y2="{y(b):.2f}" stroke="#778899" opacity=".55"/>')
            for xx, value, color in ((x+40, a, "#bd5425"), (x+300, b, "#126e82")):
                out.append(f'<circle cx="{xx}" cy="{y(value):.2f}" r="3.5" fill="{color}" opacity=".65"/>')
            out.append('</g>')
        out.extend([f'<text x="{x+40}" y="{top+227}" text-anchor="middle">Sem índice</text>',
                    f'<text x="{x+300}" y="{top+227}" text-anchor="middle">Com índice</text>'])
    out.append('<text x="40" y="738" class="small">Disco: sem índice não houve variação; com índice há sobreposição de pontos. 1 MiB = 1.048.576 bytes. Ver per_pair.csv.</text></svg>')
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def effects_plot(pairs: list[dict], summary: dict, path: Path) -> None:
    out = svg_start("Diferenças pareadas e incerteza da mediana", "Pontos: 20 pares. Linha: mediana; faixa: IC por ordem, cobertura mínima de 95,86%.", height=820)
    for i, (metric, (label, unit, benefit)) in enumerate(METRICS.items()):
        top = 100 + i * 174
        divisor = 1024 if metric == "database_bytes" else 1
        shown_unit = "KiB" if metric == "database_bytes" else unit
        values = [p[f"{metric}_difference"] / divisor for p in pairs]
        hi = max(values) * 1.08
        scale = lambda v: 300 + v / hi * 750
        effect = summary["metrics"][metric]
        ci = effect["median_ci"]["difference"]
        med = effect["descriptive"]["difference"]["median"] / divisor
        out.append(f'<text x="40" y="{top+27}">{label}</text>')
        out.append(f'<text x="40" y="{top+49}" class="small">{"Sem − com" if benefit else "Com − sem"} ({shown_unit})</text>')
        left, right = scale(ci["low"] / divisor), scale(ci["high"] / divisor)
        out.append(f'<rect x="{left:.2f}" y="{top}" width="{max(right-left,1):.2f}" height="72" fill="#c6e3ed"/>')
        for j, value in enumerate(values):
            yy = top + 14 + (j % 4) * 14
            out.append(f'<circle cx="{scale(value):.2f}" cy="{yy}" r="4" fill="#126e82"><title>Par {j+1}: {value:.9g} {shown_unit}</title></circle>')
        out.append(f'<line x1="{scale(med):.2f}" y1="{top-5}" x2="{scale(med):.2f}" y2="{top+77}" stroke="#101d29" stroke-width="2"/>')
        for j in range(5):
            val = hi * j / 4
            xx = scale(val)
            out.append(f'<text x="{xx:.2f}" y="{top+100}" text-anchor="middle" class="small">{val:.5g}</text>')
        out.append(f'<text x="300" y="{top+127}" class="small">Mediana {med:.7g}; IC [{ci["low"]/divisor:.7g}; {ci["high"]/divisor:.7g}] {shown_unit}</text>')
    out.append('<text x="40" y="804" class="small">ICs pontuais, sem ajuste simultâneo. Apenas mediana de leitura é confirmatória. Intervalos condicionados à carga e máquina.</text></svg>')
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def tables(summary: dict, pairs: list[dict]) -> str:
    lines = ["# Tabelas geradas da análise S02", "", "Geradas por `src/analyze_s02.py`. Todos os resumos abaixo têm n = 20 pares; não são resumos de 6.000 réplicas.", "",
             "Quantis nearest-rank; mediana usa média dos dois centrais. DP amostral. IQR = Q75 − Q25. Valores arredondados só na apresentação.", "",
             "## Descritivas entre pares", "", "| Métrica | Condição | Mediana | Média | DP | IQR | p95 | Mín. | Máx. |", "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for metric, info in summary["metrics"].items():
        for condition, label in (("without_index", "Sem índice"), ("with_index", "Com índice")):
            d = info["descriptive"][condition]
            cells = " | ".join(f'{d[k]:.9g}' for k in ("median", "mean", "sd", "iqr", "p95", "min", "max"))
            lines.append(f'| {info["label"]} ({info["unit"]}) | {label} | {cells} |')
    lines += ["", "## Efeitos pareados", "", "Diferença/razão = sem − com / sem ÷ com para leitura; com − sem / com ÷ sem para escrita e disco. A mudança percentual é sempre 100 × (com/sem − 1).", "",
              "| Métrica | Mediana da diferença | IC da mediana | Mediana da razão | IC da mediana da razão | Mudança mediana (%) |", "|---|---:|---|---:|---|---:|"]
    for info in summary["metrics"].values():
        d, c = info["descriptive"], info["median_ci"]
        lines.append(f'| {info["label"]} ({info["unit"]}) | {d["difference"]["median"]:.9g} | [{c["difference"]["low"]:.9g}; {c["difference"]["high"]:.9g}] | {d["ratio"]["median"]:.9g} | [{c["ratio"]["low"]:.9g}; {c["ratio"]["high"]:.9g}] | {d["change_pct"]["median"]:.9g} |')
    lines += ["", "ICs bilaterais pontuais por ordem [x(6); x(15)], cobertura mínima 0,9586105347 (nominal 95%); empates podem aumentar a cobertura. A mediana das razões é calculada nos pares, não dividindo medianas marginais.", "", "## Efeitos dos 20 pares", "",
              "| Par | Δ leitura (ms) | Razão leitura | Δ inserção (ms/linha) | Razão inserção | Δ disco (bytes) | Razão disco |", "|---:|---:|---:|---:|---:|---:|---:|"]
    for p in pairs:
        values = [p[f"{metric}_{field}"] for metric in ("read_median_ms", "write_ms_per_row", "database_bytes") for field in ("difference", "ratio")]
        lines.append(f'| {p["pair"]} | ' + " | ".join(f"{v:.9g}" for v in values) + " |")
    lines += ["", "A tabela completa por par, incluindo p95 e dispersão dentro de cada banco, está em `per_pair.csv`. `descriptive.csv` inclui também dispersão das diferenças, razões e mudanças percentuais.", ""]
    return "\n".join(lines)


def analyze(source: Path, output: Path) -> dict:
    source, output = source.resolve(), output.resolve()
    require(source != output and source not in output.parents and output not in source.parents,
            "Origem e destino devem ser diretórios separados, sem sobreposição")
    metadata, audit, reads, writes = audited_input(source)
    pairs = aggregate_pairs(metadata, reads, writes)
    summary = summarize(pairs)
    output.mkdir(parents=True, exist_ok=True)
    write_csv(output / "per_pair.csv", pairs)
    descriptive_rows = []
    for metric, info in summary["metrics"].items():
        for group, stats in info["descriptive"].items():
            descriptive_rows.append({"metric": metric, "group": group, **stats,
                                     "median_ci_low": info["median_ci"][group]["low"],
                                     "median_ci_high": info["median_ci"][group]["high"]})
    write_csv(output / "descriptive.csv", descriptive_rows)
    for name, data in (("summary.json", summary), ("audit.json", audit)):
        (output / name).write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    paired_plot(pairs, output / "paired_metrics.svg")
    effects_plot(pairs, summary, output / "paired_effects.svg")
    (output / "tables.md").write_text(tables(summary, pairs), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=ROOT / "results" / "full_s02")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results" / "analysis_s02")
    args = parser.parse_args()
    try:
        result = analyze(args.input_dir, args.output_dir)
    except (ValueError, KeyError, OSError) as error:
        parser.exit(1, f"Análise falhou: {error}\n")
    print(json.dumps(result["primary_test"], indent=2, ensure_ascii=False))
    print(f"Resultados gravados em {args.output_dir}")


if __name__ == "__main__":
    main()
