"""Dashboard final da Lab04. Execute: streamlit run dashboard/app.py."""

import math
from pathlib import Path
import sys

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dashboard.charts import (
    g1_histogram, g2_binomial, g2_z, g3_type_i, g4_power,
    load_contract, load_s02_contract, selected_rows,
)
from dashboard.real_analysis import analyze_real


REPOSITORY = "https://github.com/flavioferreiradev/Software-Measurement-and-Experimentation"
PROJECT = "https://github.com/users/flavioferreiradev/projects/3"


def percentage(value, digits=1):
    return f"{100 * value:.{digits}f}".replace(".", ",") + "%"


def decimal(value, digits=6):
    return f"{value:.{digits}f}".replace(".", ",")


def section(number, title, subtitle):
    st.markdown(f'<div class="section-kicker">SEÇÃO {number} · LAB04</div>', unsafe_allow_html=True)
    st.header(title)
    st.markdown(f'<p class="section-subtitle">{subtitle}</p>', unsafe_allow_html=True)


st.set_page_config(page_title="Lab04 · Testes de hipótese por dentro", page_icon="📊", layout="wide")
st.markdown(f"<style>{(Path(__file__).parent / 'styles.css').read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True)

try:
    data = load_contract()
    s02 = load_s02_contract()
except (OSError, ValueError) as error:
    st.error(f"Não foi possível abrir os contratos versionados: {error}")
    st.stop()

scenario = data["scenario"]
source = data["source"]
g1 = data["g1"]
example = data["example"]
z = data["g2"]["z"]
exact = data["g2"]["binomial_exact"]
alpha = scenario["alpha"]
p0 = scenario["p0"]
if not (math.isclose(s02["protocol"]["p0"], p0) and math.isclose(s02["protocol"]["alpha"], alpha)):
    st.error("Os protocolos S01 e S02 usam p₀ ou α diferentes.")
    st.stop()
try:
    real_result = analyze_real(p0=p0, alpha=alpha)
except (OSError, ValueError, KeyError) as error:
    st.error(f"Não foi possível analisar o CSV real: {error}")
    st.stop()

st.markdown(
    f"""
    <div class="hero">
      <div class="hero-top"><span class="eyebrow">PUC MINAS · LABORATÓRIO 04</span><span class="status">ENTREGA FINAL · G1–G4</span></div>
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
    st.markdown("Antes da simulação, o grupo previu que o binomial exato controlaria melhor o nível nominal com falhas raras e n pequeno. G3 e G4 confrontam essa previsão com os experimentos da S02.")

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

st.divider()
section("04", "Erro tipo I · G3", "Q1 e Q3: 10.000 amostras sob p = 5% em cada tamanho amostral.")
null_rows = {row["n"]: row for row in selected_rows(s02, "g3")}
st.plotly_chart(g3_type_i(s02), width="stretch", theme=None, config={"displaylogo": False})
st.markdown(
    f"Em n=200, os dois testes rejeitaram H₀ em {percentage(null_rows[200]['tests']['z']['rejection_rate'], 2)} das amostras; "
    "a linha de 5% representa o nível nominal, não uma taxa que a simulação precise atingir exatamente. "
    f"Em n=42, o Z chegou a {percentage(null_rows[42]['tests']['z']['rejection_rate'], 2)} e o binomial exato a "
    f"{percentage(null_rows[42]['tests']['binomial_exact']['rejection_rate'], 2)}: o primeiro excedeu o nível nominal e o segundo foi conservador. "
    "As barras de erro são intervalos de incerteza Monte Carlo das 10.000 repetições, não intervalos para a taxa real de falhas."
)

st.divider()
section("05", "Poder · G4", "Q2 e Q3: frequência de rejeição conforme aumenta a taxa geradora de falhas.")
st.plotly_chart(g4_power(s02), width="stretch", theme=None, config={"displaylogo": False})
power_rows = selected_rows(s02, "g4")
at_ten_percent = {row["n"]: row for row in power_rows if math.isclose(row["p"], 0.10)}
st.markdown(
    "O ponto de efeito zero reutiliza Q1: ele mede erro tipo I, enquanto os pontos à direita medem poder sob alternativas. "
    f"Quando p=10% (+5 p.p. sobre a meta), o Z e o exato rejeitaram em "
    f"{percentage(at_ten_percent[200]['tests']['z']['rejection_rate'], 2)} das amostras de n=200; "
    "as curvas coincidem porque ambos usam o limiar K≥16 nesse tamanho. "
    f"Em n=42, foram {percentage(at_ten_percent[42]['tests']['z']['rejection_rate'], 2)} para o Z e "
    f"{percentage(at_ten_percent[42]['tests']['binomial_exact']['rejection_rate'], 2)} para o exato; "
    "a maior detecção do Z deve ser lida junto ao erro tipo I acima de 5% em G3."
)

st.divider()
section("06", "Dados reais", "Inferência sobre o CSV validado, separada do exemplo simulado e das repetições Monte Carlo.")
effect_pp = f"{100 * real_result['effect_difference']:+.2f}".replace(".", ",") + " p.p."
st.markdown(
    f"O recorte contém **{real_result['k']} falhas em {real_result['n']} execuções** "
    f"(p̂ = **{percentage(real_result['p_hat'], 2)}**), diferença observada de "
    f"**{effect_pp}** em relação à meta de 5%."
)
real_table = []
for key, name in (("z", "Teste Z"), ("binomial_exact", "Binomial exato")):
    test = real_result["tests"][key]
    statistic = (f"Z = {decimal(test['statistic'], 3)}" if key == "z" else
                 f"K = {test['count_statistic']}; p̂ = {percentage(test['statistic'], 2)}")
    real_table.append({
        "Teste": name,
        "Estatística": statistic,
        "p-valor": decimal(test["p_value"], 6),
        "Efeito observado": effect_pp,
        "Decisão (α=5%)": "Rejeitar H₀" if test["reject_h0"] else "Não rejeitar H₀",
        "Conclusão": ("Evidência de taxa acima de 5%" if test["reject_h0"] else
                      "Evidência insuficiente de taxa acima de 5%"),
    })
st.dataframe(real_table, hide_index=True, width="stretch")
st.markdown(
    "Os dois p-valores foram recalculados dos registros reais, apesar de a contagem de falhas coincidir com a amostra simulada da S01. "
    "A diferença observada de 4,52 p.p. não basta, com estes testes e α=5%, para afirmar que a taxa supera a meta. "
    "Não rejeitar H₀ também não demonstra que a meta foi cumprida."
)

st.divider()
section("07", "Conclusão", "O que os experimentos e os dados reais permitem recomendar.")
st.markdown(
    "A previsão registrada antes da simulação se confirmou quanto ao **controle do erro tipo I em amostra pequena**: "
    f"com n=42, o exato rejeitou {percentage(null_rows[42]['tests']['binomial_exact']['rejection_rate'], 2)} "
    f"sob H₀, enquanto o Z rejeitou {percentage(null_rows[42]['tests']['z']['rejection_rate'], 2)}. "
    "O exato ficou bem abaixo dos 5% por causa dos degraus da distribuição binomial; seu menor poder em G4 é o custo desse conservadorismo. "
    "Com n=200, os testes produziram as mesmas decisões neste protocolo porque compartilham K≥16, embora seus p-valores não sejam geralmente iguais."
)
st.markdown(
    f"Nos dados reais, p̂={percentage(real_result['p_hat'], 2)} é maior que a meta, mas nenhum dos testes rejeita H₀ a 5%; "
    "o resultado é inconclusivo sobre uma taxa populacional acima da meta. "
    "Para falhas raras e amostras pequenas sob o modelo iid Bernoulli, recomendamos o **binomial exato** se a prioridade é "
    "não ultrapassar o erro tipo I nominal; aceitar sua menor capacidade de detecção ou coletar mais execuções. "
    "Com amostra maior e aproximação normal avaliada, o Z pode ser uma alternativa; se houver dependência temporal ou "
    "probabilidade de falha variável, é preciso revisar o modelo antes de confiar em qualquer um dos dois testes."
)
st.caption(
    "Limites: as 42 execuções vieram de uma janela temporal por conveniência; commits, reruns e infraestrutura podem criar "
    "dependência. A meta de 5% é pedagógica, não uma política declarada pelo projeto fonte. G3/G4 estudam tamanho "
    "amostral sob Bernoulli iid; não simulam essas fontes de viés dos dados reais."
)
