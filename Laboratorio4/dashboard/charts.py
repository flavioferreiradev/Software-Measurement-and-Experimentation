"""Gráficos de apresentação derivados exclusivamente do contrato G1/G2."""

from bisect import bisect_left
import json
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
