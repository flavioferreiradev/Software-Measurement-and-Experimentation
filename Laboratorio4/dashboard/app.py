"""Dashboard explicativo da Lab04S01. Execute: streamlit run dashboard/app.py."""

from pathlib import Path
import sys

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dashboard.charts import g1_histogram, g2_binomial, g2_z, load_contract


REPOSITORY = "https://github.com/flavioferreiradev/Software-Measurement-and-Experimentation"
PROJECT = "https://github.com/users/flavioferreiradev/projects/3"


def percentage(value, digits=1):
    return f"{100 * value:.{digits}f}".replace(".", ",") + "%"


def decimal(value, digits=6):
    return f"{value:.{digits}f}".replace(".", ",")


def section(number, title, subtitle):
    st.markdown(f'<div class="section-kicker">SEÇÃO {number} · LAB04S01</div>', unsafe_allow_html=True)
    st.header(title)
    st.markdown(f'<p class="section-subtitle">{subtitle}</p>', unsafe_allow_html=True)


st.set_page_config(page_title="Lab04 · Testes de hipótese por dentro", page_icon="📊", layout="wide")
st.markdown(f"<style>{(Path(__file__).parent / 'styles.css').read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True)

try:
    data = load_contract()
except (OSError, ValueError) as error:
    st.error(f"Não foi possível abrir o contrato versionado: {error}")
    st.stop()

scenario = data["scenario"]
source = data["source"]
g1 = data["g1"]
example = data["example"]
z = data["g2"]["z"]
exact = data["g2"]["binomial_exact"]
alpha = scenario["alpha"]
p0 = scenario["p0"]

st.markdown(
    f"""
    <div class="hero">
      <div class="hero-top"><span class="eyebrow">PUC MINAS · LABORATÓRIO 04</span><span class="status">SPRINT 01 · G1 + G2</span></div>
      <h1>Testes de hipótese por dentro</h1>
      <p>Quando a taxa de falhas do CI parece superar a meta: o que o teste Z e o binomial exato realmente mostram?</p>
      <nav class="hero-links" aria-label="Links do projeto">
        <a href="./">↗ Dashboard</a>
        <a href="{REPOSITORY}" target="_blank" rel="noopener noreferrer">↗ Repositório</a>
        <a href="{PROJECT}" target="_blank" rel="noopener noreferrer">↗ GitHub Projects</a>
      </nav>
    </div>
    """,
    unsafe_allow_html=True,
)

section("01", "Cenário", "Uma pergunta de qualidade de software, duas maneiras de calcular a cauda sob H₀.")
st.markdown(f'<p class="question">{scenario["question_pt"]}</p>', unsafe_allow_html=True)
columns = st.columns(4)
with columns[0]:
    st.metric("Meta de falhas", percentage(p0, 0))
with columns[1]:
    st.metric("Significância α", percentage(alpha, 0))
with columns[2]:
    st.metric("Execuções reais válidas", data["empirical"]["n"])
with columns[3]:
    st.metric("Testes", "Z + exato")

left, right = st.columns([1, 1], gap="large")
with left:
    st.markdown("**Hipóteses e direção**")
    st.markdown(f"H₀: p ≤ {percentage(p0, 0)}. H₁: p > {percentage(p0, 0)}. A cauda é à direita: só um excesso de falhas responde à pergunta.")
    st.markdown("Cada observação é uma execução concluída do workflow; 0 significa sucesso e 1 significa falha ou timeout.")
with right:
    st.markdown("**Fonte e previsão anterior à simulação**")
    st.markdown(
        f"[Workflow test de {source['repository']}]({source['workflow_url']}), "
        f"eventos `{source['event']}` na branch `{source['branch']}`, entre "
        f"{source['observed_period']['start'][:10]} e {source['observed_period']['end'][:10]} (UTC). "
        "Quatro execuções canceladas foram excluídas da amostra."
    )
    st.markdown("Antes da simulação, o grupo previu que o binomial exato controlaria melhor o nível nominal com falhas raras e n pequeno; isso será avaliado na S02.")

st.divider()
section("02", "Os dados · G1", "Histogramas discretos: os dois intervalos representam sucesso (0) e falha (1).")
real_n = len(g1["real"]["values"])
sim_n = len(g1["simulated"]["values"])
real_k = g1["real"]["counts"][1]
sim_k = g1["simulated"]["counts"][1]
real_col, sim_col = st.columns(2, gap="large")
with real_col:
    with st.container(border=True):
        st.subheader("Dados reais")
        st.caption(f"n = {real_n} · {g1['real']['counts'][0]} sucessos · {real_k} falhas · p̂ = {percentage(real_k / real_n, 2)}")
        st.plotly_chart(g1_histogram(data, "real"), width="stretch", theme=None, config={"displaylogo": False})
        st.markdown(
            f"Das {real_n} execuções válidas, {real_k} falharam; a frequência observada é {percentage(real_k / real_n, 2)}. "
            "A variável é binária, então há apenas dois intervalos e não há assimetria ou outliers contínuos a interpretar. "
            "O recorte é temporal e exclui cancelamentos; a proporção descreve somente as execuções incluídas."
        )
with sim_col:
    with st.container(border=True):
        st.subheader("Dados simulados")
        st.caption(f"n = {sim_n} · {g1['simulated']['counts'][0]} sucessos · {sim_k} falhas · p̂ = {percentage(sim_k / sim_n, 2)}")
        st.plotly_chart(g1_histogram(data, "simulated"), width="stretch", theme=None, config={"displaylogo": False})
        st.markdown(
            f"A amostra foi gerada com Bernoulli(p={percentage(data['generator']['p'], 2)}), n={data['generator']['n']} e seed={data['generator']['seed']}. "
            "Escolhemos p a partir da frequência real para manter uma escala plausível de falhas; o modelo supõe execuções independentes e probabilidade constante. "
            "As contagens coincidiram por acaso (38 sucessos, quatro falhas), embora as sequências sejam diferentes."
        )

st.divider()
section("03", "Como os testes funcionam · G2", "Duas distribuições sob a fronteira H₀: p = 5%; p-valores do mesmo exemplo simulado.")
st.info(
    f"**Exemplo simulado:** {example['k']} falhas em {example['n']} execuções (p̂ = {percentage(example['p_hat'], 2)}). "
    "Os valores abaixo não são resultados inferenciais da amostra real."
)
z_col, exact_col = st.columns(2, gap="large")
with z_col:
    with st.container(border=True):
        st.subheader("Teste Z · aproximação normal")
        st.caption(f"Z observado = {decimal(z['observed'], 3)} · Z crítico = {decimal(z['critical_value'], 3)} · p = {decimal(z['p_value_tail']['area'])}")
        st.plotly_chart(g2_z(data), width="stretch", theme=None, config={"displaylogo": False})
        st.markdown(
            f"A curva N(0,1) aproxima a distribuição de Z sob H₀; a cauda âmbar começa no Z observado e representa p={decimal(z['p_value_tail']['area'])}. "
            f"A faixa vermelha, dentro dessa cauda, é a região de rejeição acima de {decimal(z['critical_value'], 3)}; sua área analítica é {percentage(z['critical_tail']['area'], 0)} e ambas as caudas continuam até +∞. "
            "Como p ≥ α, não rejeitamos H₀; isso não comprova que a meta seja atendida. "
            f"Aqui n·p₀={decimal(example['tests']['z']['expected_failures_h0'], 1)}: a aproximação normal pode ser ruim para falhas raras."
        )
with exact_col:
    with st.container(border=True):
        st.subheader("Binomial exato · massas discretas")
        st.caption(f"K observado = {exact['observed_k']} · crítico K ≥ {exact['critical_k']} · p = {decimal(exact['p_value_area'])}")
        st.plotly_chart(g2_binomial(data), width="stretch", theme=None, config={"displaylogo": False})
        st.markdown(
            f"As barras são massas Binomial(n={exact['n']}, p₀={percentage(exact['p0'], 0)}) sob H₀; o p-valor soma K ≥ {exact['observed_k']}, inclusive a barra observada. "
            f"As barras hachuradas K ≥ {exact['critical_k']} também pertencem à cauda do p-valor e formam a região crítica, cuja probabilidade é {percentage(exact['critical_area'], 3)}. "
            f"Como p={decimal(exact['p_value_area'])} ≥ α, não rejeitamos H₀; isso não comprova que a meta seja atendida. "
            "A distribuição completa vai até K=42; use o zoom do gráfico para ver a cauda remanescente."
        )

st.markdown(
    '<div class="explanation"><strong>Por que os p-valores diferem?</strong> '
    "O Z usa uma cauda normal contínua aproximada. O binomial soma as massas inteiras de K=4 até 42; "
    "com apenas 2,1 falhas esperadas sob H₀, os degraus da distribuição importam. "
    "Os dois testes não rejeitam H₀ neste exemplo, mas isso não comprova que a meta seja atendida "
    "nem indica qual teste tem melhor desempenho em geral.</div>",
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="future"><strong>Próximas etapas do dashboard</strong><br>'
    "04 · Erro tipo I (G3) &nbsp;·&nbsp; 05 · Poder (G4) &nbsp;·&nbsp; "
    "06 · Dados reais &nbsp;·&nbsp; 07 · Conclusão. "
    "As simulações e conclusões dessas seções serão adicionadas nas próximas entregas.</div>",
    unsafe_allow_html=True,
)
