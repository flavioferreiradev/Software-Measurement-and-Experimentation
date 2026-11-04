# Dashboard da Lab04S01 — Issue #31

Execute a partir de `Laboratorio4/`, após instalar `requirements.txt`:

```bash
streamlit run dashboard/app.py
```

O dashboard lê `results/demo_s01.json` v1.0.0, sem rede, nova coleta ou
simulação. `charts.py` transforma apenas os valores, suportes e máscaras do
contrato em objetos Plotly. `app.py` organiza as seções 1–3 e explica o exemplo
simulado; `styles.css` e `.streamlit/config.toml` definem a apresentação.

G1 usa as duas sequências do contrato, bins `[-0.5, 0.5, 1.5]` e escala comum.
G2 mostra a cauda contínua do Z aproximado e as massas binomiais discretas;
as regiões críticas aparecem dentro das caudas dos p-valores. A janela inicial
do binomial amplia K=0..13 para leitura, mas o objeto Plotly contém todo o
suporte K=0..42 e permite zoom. As áreas numéricas são as analíticas do JSON.

As futuras seções 4–7 estão identificadas no rodapé, sem resultados da S02.
Para incluir G3/G4 posteriormente, acrescente novos gráficos alimentados por
um contrato versionado e novas seções após G2, mantendo a ordem do enunciado.
