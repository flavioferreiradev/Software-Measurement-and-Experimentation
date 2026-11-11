# Validação do dashboard final — Issue #35

Base: `origin/main` em `ef5ceb7`, que integra a Issue #34 pelo PR #36. Branch da contribuição visual: `codex/lab04s02-flavio-35`. A implementação usa os snapshots S01/S02 já versionados e recalcula a inferência real do CSV validado; não houve nova coleta nem alteração de dados/resultados oficiais.

## Escopo verificado

- `dashboard/charts.py` lê e valida o contrato S02 v1.0.0, usa os seletores `g3.row_ids` e `g4.row_ids`, desenha G3 com linha nominal de 5% e G4 com quatro séries e cores fixas por teste.
- `dashboard/real_analysis.py` valida a origem e o SHA256 do CSV antes de aplicar os dois testes aos 42 valores reais.
- `dashboard/app.py` mostra as sete seções, seis gráficos, tabela de estatística/p-valor/efeito/decisão/conclusão para cada teste e recomendação condicionada às hipóteses do modelo.
- `python -m src.run_all` reproduz S01, S02 e análise real com seed=42 em `.pytest-tmp/lab04-full/`, sem sobrescrever os snapshots oficiais.

## Evidência local

Ambiente: macOS, Python 3.12.14, NumPy 2.4.2, SciPy 1.17.1, Streamlit 1.52.2 e Plotly 6.5.0. Comandos executados dentro de `Laboratorio4/`:

```bash
python -m src.run_all --output .pytest-tmp/lab04-final-check
python -m pytest -q
streamlit run dashboard/app.py --server.headless true --server.port 8502
```

O comando integral gerou S01, 12 células S02 e análise real `n=42, k=4` na pasta separada. A suíte passou com **133 testes**, zero falhas, em 4,42 s na execução final. `git diff --check` passou. Os testes novos conferem os dados efetivamente selecionados para G3/G4, a linha de 5%, as cores, os p-valores reais e a preservação byte a byte dos resultados oficiais durante a reprodução integral.

A página foi aberta localmente no navegador: os links do topo, as sete seções, G3, G4, a legenda de quatro séries, a tabela real e a conclusão renderizaram sem erro. G3 exibiu 4,19%/4,19% em n=200 e 5,77%/1,95% em n=42; G4 manteve as curvas n=200 coincidentes, sem deslocar dados. A tabela apresentou Z=1,345, p=0,089283; exato K=4, p=0,156893; efeito +4,52 p.p. para ambos.

## CI

O workflow `.github/workflows/lab04-tests.yml` está configurado para Python 3.12 em Windows e Ubuntu. Os runs recentes da #34 nem chegaram a executar etapas por bloqueio externo de cobrança do GitHub Actions, documentado na entrega de Luidi. A validação da #35 em CI será observada no PR; o resultado local acima não deve ser descrito como aprovação de Windows/Ubuntu.
