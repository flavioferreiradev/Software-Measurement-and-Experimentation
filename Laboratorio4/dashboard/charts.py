"""Gráficos de apresentação derivados dos contratos versionados G1–G4."""

from bisect import bisect_left
import json
import math
from pathlib import Path

import plotly.graph_objects as go


ROOT = Path(__file__).resolve().parents[1]
TEAL = "#087F8C"
VIOLET = "#6752B8"
AMBER = "#E8A23A"
RED = "#C94B53"
INK = "#203247"
MUTED = "#627386"
GRID = "#E8EDF1"


def load_contract(path=ROOT / "results" / "demo_s01.json"):
    """Lê o snapshot versionado; nenhuma coleta ou simulação acontece aqui."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema_version") != "1.0.0":
        raise ValueError("O dashboard requer o contrato G1/G2 v1.0.0.")
    return payload


def load_s02_contract(path=ROOT / "results" / "experiments_s02.json"):
    """Valida os campos consumidos por G3/G4 antes de abrir o dashboard."""
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Não foi possível ler o contrato G3/G4: {error}") from error
    try:
        if payload["schema_version"] != "1.0.0":
            raise ValueError("O dashboard requer o contrato G3/G4 v1.0.0.")
        protocol = payload["protocol"]
        if not (0 < protocol["p0"] < 1 and 0 < protocol["alpha"] < 1 and protocol["repetitions"] > 0):
            raise ValueError("Parâmetros inválidos no contrato G3/G4.")
        scenarios = {item["id"]: item for item in payload["scenarios"]}
        rows = {item["id"]: item for item in payload["rows"]}
        if len(scenarios) != len(payload["scenarios"]) or len(scenarios) != 2 or len(rows) != len(payload["rows"]):
            raise ValueError("Situações ou linhas duplicadas no contrato G3/G4.")
        g3_ids, g4_ids = payload["g3"]["row_ids"], payload["g4"]["row_ids"]
        if (len(g3_ids) != 2 or len(set(g3_ids)) != 2 or len(g4_ids) < 10
                or not set(g3_ids) <= set(g4_ids)
                or set(g4_ids) != set(rows) or len(set(g4_ids)) != len(g4_ids)):
            raise ValueError("Seletores G3/G4 incompatíveis com as linhas.")
        if not math.isclose(payload["g3"]["nominal_rate"], protocol["alpha"]):
            raise ValueError("Referência nominal de G3 difere de α.")
        for row in rows.values():
            if row["scenario_id"] not in scenarios or row["n"] != scenarios[row["scenario_id"]]["n"]:
                raise ValueError("Linha G3/G4 com situação ou n incompatível.")
            if row["repetitions"] != protocol["repetitions"] or not math.isclose(row["delta"], row["p"] - protocol["p0"]):
                raise ValueError("Linha G3/G4 com repetição ou efeito incompatível.")
            if set(row["tests"]) != {"z", "binomial_exact"}:
                raise ValueError("Linha G3/G4 sem os dois testes.")
            for result in row["tests"].values():
                rate = result["rejection_rate"]
                low, high = result["mc_ci95_wilson"]
                if (not all(math.isfinite(value) for value in (rate, low, high))
                        or not 0 <= low <= rate <= high <= 1
                        or result["rejections"] / row["repetitions"] != rate):
                    raise ValueError("Taxa ou intervalo Monte Carlo inválido em G3/G4.")
        if any(rows[key]["estimand"] != "type_i_error" for key in g3_ids):
            raise ValueError("G3 deve apontar apenas para linhas sob H₀.")
        if {rows[key]["scenario_id"] for key in g3_ids} != set(scenarios):
            raise ValueError("G3 deve conter uma linha nula por situação.")
    except (KeyError, TypeError, IndexError, ZeroDivisionError) as error:
        raise ValueError("Contrato G3/G4 incompleto ou malformado.") from error
    return payload


def selected_rows(payload, selector):
    rows = {row["id"]: row for row in payload["rows"]}
    return [rows[key] for key in payload[selector]["row_ids"]]


def style_figure(figure, *, height=345, legend_y=-0.27):
    figure.update_layout(
        height=height,
        margin=dict(l=48, r=20, t=56, b=60),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial, sans-serif", color=INK, size=13),
        hoverlabel=dict(bgcolor="#FFFFFF", font_color=INK),
        legend=dict(orientation="h", yanchor="top", y=legend_y, x=0, font_size=11),
        bargap=0.25,
    )
    figure.update_xaxes(showline=True, linecolor=GRID, gridcolor=GRID, zeroline=False)
    figure.update_yaxes(showline=False, gridcolor=GRID, zeroline=False)
    return figure


def horizontal_y_label(figure, label):
    """Mantém o nome da unidade legível também em telas estreitas."""
    figure.add_annotation(
        xref="paper", yref="paper", x=0, y=1.07, text=label,
        showarrow=False, xanchor="left", yanchor="bottom",
        font=dict(color=MUTED, size=12),
    )
    return figure


def g1_histogram(payload, group):
    """Bins discretos idênticos para a amostra real e a simulada."""
    if group not in ("real", "simulated"):
        raise ValueError("Grupo G1 desconhecido")
    g1 = payload["g1"]
    edges = g1["bin_edges"]
    figure = go.Figure(go.Histogram(
        x=g1[group]["values"],
        xbins=dict(start=edges[0], end=edges[-1], size=edges[1] - edges[0]),
        histnorm="probability",
        marker=dict(color=TEAL if group == "real" else VIOLET, line=dict(color="#FFFFFF", width=2)),
        hovertemplate="Resultado %{x:.0f}<br>Frequência relativa %{y:.1%}<extra></extra>",
        name="Execuções",
        showlegend=False,
    ))
    style_figure(figure, height=320)
    figure.update_xaxes(
        title="Resultado da execução de CI",
        tickmode="array", tickvals=[0, 1], ticktext=g1["labels"], range=[edges[0] - 0.12, edges[-1] + 0.12],
    )
    figure.update_yaxes(tickformat=".0%", range=[0, 1.05], dtick=0.2)
    return horizontal_y_label(figure, "Frequência relativa")


def _tail_points(x, y, lower):
    """Insere o limiar exato na malha somente para desenhar a cauda."""
    i = bisect_left(x, lower)
    if i == len(x):
        return [lower], [0]
    if x[i] == lower:
        return x[i:], y[i:]
    left, right = i - 1, i
    ordinate = y[left] + (y[right] - y[left]) * (lower - x[left]) / (x[right] - x[left])
    return [lower, *x[i:]], [ordinate, *y[i:]]


def g2_z(payload):
    ref = payload["g2"]["z"]
    x, density = ref["x"], ref["pdf"]
    observed = ref["observed"]
    critical = ref["critical_value"]
    px, py = _tail_points(x, density, observed)
    cx, cy = _tail_points(x, density, critical)
    figure = go.Figure()
    figure.add_trace(go.Scatter(
        x=px, y=py, mode="lines", line=dict(color=AMBER, width=1), fill="tozeroy",
        fillcolor="rgba(232,162,58,0.58)", name="Área do p-valor",
        hovertemplate="Z=%{x:.2f}<br>Densidade=%{y:.3f}<extra>Cauda do p-valor</extra>",
    ))
    figure.add_trace(go.Scatter(
        x=cx, y=cy, mode="lines", line=dict(color=RED, width=1), fill="tozeroy",
        fillcolor="rgba(201,75,83,0.72)", name="Região de rejeição",
        hovertemplate="Z=%{x:.2f}<br>Densidade=%{y:.3f}<extra>Região crítica</extra>",
    ))
    figure.add_trace(go.Scatter(
        x=x, y=density, mode="lines", line=dict(color=TEAL, width=3), name="N(0,1) aproximada",
        hovertemplate="Z=%{x:.2f}<br>Densidade=%{y:.3f}<extra>N(0,1)</extra>",
    ))
    figure.add_vline(x=observed, line=dict(color=TEAL, width=2, dash="dot"))
    figure.add_vline(x=critical, line=dict(color=RED, width=2, dash="dash"))
    figure.add_annotation(x=observed, y=0.30, text=f"Z observado {observed:.3f}", showarrow=False,
                          xanchor="right", font=dict(color=TEAL, size=11), bgcolor="rgba(255,255,255,.88)")
    figure.add_annotation(x=critical, y=0.22, text=f"Crítico {critical:.3f}", showarrow=False,
                          xanchor="left", font=dict(color=RED, size=11), bgcolor="rgba(255,255,255,.88)")
    style_figure(figure, height=390, legend_y=-0.27)
    figure.update_xaxes(title="Estatística Z (desvios-padrão)", range=[x[0], x[-1]])
    figure.update_yaxes(rangemode="tozero")
    return horizontal_y_label(figure, "Densidade de probabilidade")


def g2_binomial(payload):
    ref = payload["g2"]["binomial_exact"]
    support, mass = ref["k_support"], ref["pmf"]
    p_mask, critical_mask = ref["p_value_mask"], ref["rejection_mask"]
    figure = go.Figure()
    figure.add_trace(go.Bar(
        x=support, y=mass, name="Massa sob H₀", marker_color="rgba(103,82,184,0.38)",
        hovertemplate="K=%{x}<br>Massa=%{y:.5f}<extra>Binomial sob H₀</extra>",
    ))
    figure.add_trace(go.Bar(
        x=[k for k, selected in zip(support, p_mask) if selected],
        y=[p for p, selected in zip(mass, p_mask) if selected],
        name="Área do p-valor", marker_color=AMBER,
        hovertemplate="K=%{x}<br>Massa=%{y:.5f}<extra>Cauda do p-valor</extra>",
    ))
    figure.add_trace(go.Bar(
        x=[k for k, selected in zip(support, critical_mask) if selected],
        y=[p for p, selected in zip(mass, critical_mask) if selected],
        name="Região de rejeição", marker=dict(
            color="rgba(255,255,255,0)", line=dict(color=RED, width=2),
            pattern=dict(shape="/", fgcolor=RED, bgcolor="rgba(255,255,255,0)", size=6),
        ),
        hovertemplate="K=%{x}<br>Massa=%{y:.5f}<extra>Região crítica (também no p-valor)</extra>",
    ))
    figure.add_vline(x=ref["observed_k"], line=dict(color=VIOLET, width=2, dash="dot"))
    figure.add_annotation(x=ref["observed_k"], y=max(mass) * 0.85,
                          text=f"K observado = {ref['observed_k']}", showarrow=False,
                          xanchor="left", font=dict(color=VIOLET, size=11), bgcolor="rgba(255,255,255,.9)")
    style_figure(figure, height=390, legend_y=-0.27)
    figure.update_layout(barmode="overlay")
    figure.update_xaxes(title="Número K de falhas (execuções)", tickmode="linear", dtick=2,
                        range=[-0.6, min(max(support) + 0.6, 13.5)])
    figure.update_yaxes(rangemode="tozero")
    return horizontal_y_label(figure, "Massa de probabilidade")


def g3_type_i(payload):
    """Taxas simuladas sob H₀, separadas por situação e teste."""
    rows = selected_rows(payload, "g3")
    scenarios = {item["id"]: item for item in payload["scenarios"]}
    labels = [scenarios[row["scenario_id"]]["label_pt"] for row in rows]
    figure = go.Figure()
    upper = payload["g3"]["nominal_rate"]
    for key, name, color in (("z", "Teste Z", TEAL), ("binomial_exact", "Binomial exato", VIOLET)):
        results = [row["tests"][key] for row in rows]
        rates = [result["rejection_rate"] for result in results]
        lows = [result["mc_ci95_wilson"][0] for result in results]
        highs = [result["mc_ci95_wilson"][1] for result in results]
        upper = max(upper, *highs)
        figure.add_trace(go.Bar(
            x=labels, y=rates, name=name, marker_color=color,
            text=[f"{rate:.2%}".replace(".", ",") for rate in rates], textposition="outside",
            error_y=dict(type="data", symmetric=False,
                         array=[high - rate for high, rate in zip(highs, rates)],
                         arrayminus=[rate - low for low, rate in zip(lows, rates)],
                         color=color, thickness=1.5, width=4),
            customdata=[[result["theoretical_rejection_rate"], low, high]
                        for result, low, high in zip(results, lows, highs)],
            hovertemplate="%{x}<br>Taxa simulada: %{y:.2%}<br>Probabilidade teórica: %{customdata[0]:.2%}"
                          "<br>IC MC 95%: [%{customdata[1]:.2%}, %{customdata[2]:.2%}]<extra>" + name + "</extra>",
        ))
    figure.add_hline(y=payload["g3"]["nominal_rate"], line=dict(color=RED, width=2, dash="dash"),
                     annotation_text="α = 5% (nominal)", annotation_position="top left")
    style_figure(figure, height=410, legend_y=-0.26)
    figure.update_layout(barmode="group", margin=dict(l=58, r=25, t=52, b=75))
    figure.update_yaxes(title="Amostras rejeitadas (%)", tickformat=".0%", range=[0, upper * 1.27])
    figure.update_xaxes(title="Situação simulada")
    return figure


def g4_power(payload):
    """Quatro séries em um gráfico; Δ=0 reutiliza a linha de erro tipo I."""
    rows = selected_rows(payload, "g4")
    scenarios = payload["scenarios"]
    figure = go.Figure()
    for scenario in scenarios:
        subset = sorted((row for row in rows if row["scenario_id"] == scenario["id"]),
                        key=lambda row: row["delta"])
        for key, name, color, symbol, size in (
            ("z", "Z", TEAL, "circle", 8),
            ("binomial_exact", "Binomial exato", VIOLET, "diamond-open", 12),
        ):
            figure.add_trace(go.Scatter(
                x=[100 * row["delta"] for row in subset],
                y=[row["tests"][key]["rejection_rate"] for row in subset],
                mode="lines+markers", name=f"{name} · n={scenario['n']}",
                line=dict(color=color, width=(5 if key == "z" else 2) if scenario["n"] == 200 else 3,
                          dash="dash" if scenario["n"] == 200 else "solid"),
                marker=dict(symbol=symbol, size=size, color=color, line=dict(color=color, width=2)),
                hovertemplate="Efeito: +%{x:g} p.p.<br>Rejeições: %{y:.1%}<extra>" +
                              f"{name} · n={scenario['n']}" + "</extra>",
            ))
    style_figure(figure, height=500, legend_y=-0.22)
    ticks = sorted({100 * row["delta"] for row in rows})
    figure.update_layout(margin=dict(l=60, r=25, t=52, b=100), hovermode="x unified")
    figure.update_xaxes(title="Aumento da taxa de falhas Δ (pontos percentuais)", tickvals=ticks,
                        ticktext=[f"{value:g}".replace(".", ",") for value in ticks], range=[-0.6, max(ticks) + 0.6])
    figure.update_yaxes(title="Amostras rejeitadas (%)", tickformat=".0%", range=[0, 1.07], dtick=0.2)
    return figure
