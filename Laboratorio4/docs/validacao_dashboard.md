# Validação do dashboard G1/G2 — Issue #31

Ambiente local: macOS, Python 3.12, Streamlit 1.52.2, Plotly 6.5.0.
Comandos executados a partir de `Laboratorio4/`:

| Verificação | Resultado |
|---|---|
| `.venv/bin/python -m pytest -q` | 76 passaram; inclui 73 testes anteriores e 3 de integração visual |
| `.venv/bin/python -m src.run_demo --output .pytest-tmp/flavio-smoke` | n=42, k=4; executou offline sem alterar o snapshot versionado |
| `.venv/bin/streamlit run dashboard/app.py --server.headless true --server.port 8501` | aplicação iniciou; quatro gráficos renderizados no navegador |
| `git diff --check` | sem erros de whitespace |

## Conferência científica

- G1 lê `g1.real.values` e `g1.simulated.values` do JSON v1.0.0: 42
  observações e quatro falhas em cada sequência. Os bins são
  `[-0.5, 0.5, 1.5]`, e os eixos usam a mesma escala percentual.
- G2 Z lê os 801 pontos `x/pdf`, Z observado 1,345185418, crítico
  1,644853627 e cauda p=0,089282682. A curva é identificada como
  aproximação N(0,1), com a região crítica contida na cauda do p-valor.
- G2 exato usa os 43 valores K=0..42 e suas massas, com cauda inclusiva
  K≥4 e região crítica K≥6. O p-valor é 0,156892615 e a probabilidade da
  região crítica é 0,017432006; os pontos além da janela inicial do gráfico
  permanecem disponíveis por zoom.
- Os dois p-valores são da amostra **simulada**. O dashboard evita inferência
  final sobre o CSV real e não afirma qual teste tem maior poder.

## Revisão visual e funcional no navegador

Foram inspecionadas larguras de 1280 px (desktop), 820 px (intermediária) e
390 px (mobile). Em desktop, G1 e G2 ficam lado a lado; em mobile, os painéis
se empilham. Foram conferidos títulos, unidades dos eixos, legendas, contraste,
regiões hachuradas, sobreposição das caudas, textos explicativos, links do topo
e ausência de erro da aplicação. A revisão detectou contraste ruim no tema
inicial e sobreposição de títulos verticais nos eixos estreitos; ambos foram
corrigidos com tema claro e rótulos horizontais. A janela inicial do binomial
destaca K≤13 por legibilidade, com suporte completo K≤42 mantido no Plotly.

As seções G3/G4 e a análise inferencial final dos dados reais pertencem às
próximas etapas e não foram simuladas no dashboard da S01.
