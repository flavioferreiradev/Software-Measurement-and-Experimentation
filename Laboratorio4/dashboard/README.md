# Dashboard final da Lab04 — Issues #31, #34 e #35

Execute a partir de `Laboratorio4/`, após instalar `requirements.txt`:

```bash
streamlit run dashboard/app.py
```

A página abre offline e lê os snapshots versionados `results/demo_s01.json`
(G1/G2) e `results/experiments_s02.json` (G3/G4). A seção de dados reais valida
`data/real_ci.csv` com sua auditoria SHA256 e aplica novamente os dois testes;
ela nunca copia os p-valores do exemplo simulado. `charts.py` valida e transforma
os contratos em seis figuras Plotly; `real_analysis.py` isola a inferência do
CSV; `app.py` organiza as sete seções; `styles.css` cuida da apresentação.

G1 usa as duas sequências do contrato, bins `[-0.5, 0.5, 1.5]` e escala comum.
G2 mostra a cauda contínua do Z aproximado e as massas binomiais discretas;
as regiões críticas aparecem dentro das caudas dos p-valores. A janela inicial
do binomial amplia K=0..13 para leitura, mas o objeto Plotly contém todo o
suporte K=0..42 e permite zoom. As áreas numéricas são as analíticas do JSON.

| Seção | Fonte | Conteúdo |
|---|---|---|
| 1 Cenário | Contrato S01 | Pergunta, hipóteses, fonte e previsão inicial |
| 2 Dados / G1 | Contrato S01 | Histogramas das sequências real e simulada |
| 3 Testes / G2 | Contrato S01 | Caudas e regiões críticas do exemplo simulado |
| 4 Erro tipo I / G3 | Contrato S02 | Taxas sob H₀ por n e teste, linha nominal de 5%, IC Monte Carlo |
| 5 Poder / G4 | Contrato S02 | Quatro séries em um gráfico, por efeito, n e teste |
| 6 Dados reais | CSV validado | Estatísticas, p-valores, efeito, decisões e conclusões |
| 7 Conclusão | Resultados anteriores | Previsão versus achados, recomendação e limites |

G4 mostra `Δ = p − p₀` em pontos percentuais. O ponto zero reaproveita Q1 e é
erro tipo I; os demais pontos são poder. Em n=200, as séries coincidem porque
os dois testes têm a mesma região crítica neste protocolo. Não deslocamos
valores para separá-las. Azul petróleo identifica Z e violeta identifica o
binomial exato em G3/G4; linha tracejada identifica n=200 em G4.

Cada gráfico tem título, eixos/unidades e explicação junto à figura. As barras
de erro de G3 medem apenas incerteza Monte Carlo. A tabela real e a conclusão
distinguem observação de 9,52% de evidência estatística; o recorte temporal e
a hipótese de execuções iid limitam inferências sobre o projeto fonte.

Para regenerar S01, S02 e a análise real por um único comando, sem sobrescrever
os snapshots oficiais, execute `python -m src.run_all`.
