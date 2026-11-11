# Handoff S02 para Flávio — Issue #34

**Atualização após o handoff:** o [PR #36](https://github.com/flavioferreiradev/Software-Measurement-and-Experimentation/pull/36)
foi integrado à `main` no commit `ef5ceb7`. A Issue #35 parte dessa versão e
consome o JSON versionado. As menções abaixo a PR aberto e bloqueio da CI
registram o estado histórico anterior ao merge; o estado atual da entrega
visual está no README e na Issue #35.

A entrega estatística de Luidi foi desenvolvida na branch
`codex/lab04s02-luidi-34`, sobre a main `19308d8`, e passou por validação local
e auditoria externa aprovada. Sua publicação foi autorizada por Luidi.
O resultado da integração é acompanhado na
[Issue #34](https://github.com/flavioferreiradev/Software-Measurement-and-Experimentation/issues/34)
e no [PR #36](https://github.com/flavioferreiradev/Software-Measurement-and-Experimentation/pull/36).
Flávio deve começar a integração visual na main que contém
essa entrega e seguir a sua própria
[Issue #35](https://github.com/flavioferreiradev/Software-Measurement-and-Experimentation/issues/35).

**Status no momento do handoff:** o PR #36 estava aberto, com a CI impedida de iniciar
por bloqueio de cobrança da conta no GitHub Actions. O merge ainda não ocorreu,
portanto a main ainda não contém esta contribuição. Os artefatos estão publicados
na branch `codex/lab04s02-luidi-34`; a pendência externa e as execuções estão em
`validacao_s02.md`. Não iniciar a integração a partir da main antiga supondo
que ela já contém o JSON S02.

## Entrega estatística pronta

- Q1: erro tipo I, 10.000 amostras por situação sob p=0,05.
- Q2: seis níveis de p, começando no nulo; 10.000 amostras por célula.
- Q3: referência n=200 versus amostra pequena n=42, com qualificação explícita
  da aproximação normal. Total: 12 células e 120.000 amostras.
- Fluxos reproduzíveis por n/p, ambos os testes sobre as mesmas contagens.
- Taxas, contagens, histogramas, limiares, ICs Monte Carlo e confronto teórico.
- Contrato separado da S01; G1/G2 e seus dados permanecem intactos.

## Como reproduzir e ler

Enquanto o merge estiver bloqueado, é possível validar os arquivos publicados
em uma branch local de revisão, sem alterar a #35:

```bash
git fetch origin
git switch -c revisao-lab04s02-34 origin/codex/lab04s02-luidi-34
cd Laboratorio4
python -m venv .venv
```

Ativar o ambiente e usar os comandos de instalação/reprodução abaixo. Essa
revisão não substitui a aprovação da CI nem a integração do PR #36.

Após confirmar o merge da #34, atualizar a main e criar a branch da #35:

```bash
git switch main
git pull --ff-only
git switch -c codex/lab04s02-flavio-35
cd Laboratorio4
python -m venv .venv
```

Ativar `.venv\Scripts\Activate.ps1` no PowerShell ou
`source .venv/bin/activate` no Linux/macOS. Instalar as dependências e conferir
os resultados e testes antes de alterar o dashboard:

```bash
python -m pip install -r requirements.txt
python -m src.run_experiments
python -m pytest -q
```

O primeiro comando gera os três arquivos novos `results/experiments_s02.*`
e `results/experiments_s02_summary.md`. Não executar `src.collect` ou
sobrescrever `demo_s01.json`. O teste pode usar `--basetemp` local conforme
README caso o Temp do Windows esteja sem acesso.

Consumir principalmente **`results/experiments_s02.json`**,
`schema_version="1.0.0"`. O CSV é uma projeção tabular adicional. O formato e
um exemplo mínimo de leitura estão em `contrato_integracao_s02.md`.

## Dados para G3/G4

**G3**: `g3.row_ids` seleciona as duas linhas de erro tipo I (p=p₀).
Usar `tests.z.rejection_rate` e `tests.binomial_exact.rejection_rate` por
`scenario_id`; linha de referência em `g3.nominal_rate=0.05`.
ICs opcionais: `mc_ci95_wilson`. As probabilidades teóricas estão em
`theoretical_rejection_rate` e não devem substituir a referência nominal.

**G4**: `g4.row_ids` seleciona as 12 células. X=`delta` em proporção;
Y=`tests.<teste>.rejection_rate`. Identificar situação e teste em quatro séries,
mantendo os dois testes no mesmo gráfico. O ponto Δ=0 é o mesmo do G3.
As duas séries n=200 coincidem neste protocolo; não deslocar os dados para
produzir separação artificial.

## Trabalho que continua com Flávio

- Construir G3/G4 e integrar ao dashboard, preservando o padrão visual G1/G2.
- Incluir textos claros de interpretação, unidades e incerteza Monte Carlo.
- Realizar a inferência dos dados reais, sua tabela e interpretação.
- Criar as seções finais do dashboard e a conclusão geral.
- Validar visualmente o dashboard, consolidar documentação e entrega do grupo.

Nenhuma dessas atividades visuais/finais faz parte da entrega da #34. Para
abrir o dashboard existente, usar `streamlit run dashboard/app.py`. A #35
continua sob responsabilidade do Flávio e não é encerrada pela integração da #34.

## Limitações para explicar junto aos gráficos

O exato é conservador em n=42 pela discretização. O Z rejeita mais sob
alternativas, mas também excede o nível nominal sob H₀. Em n=200 ambos têm
região K≥16; isso explica taxas iguais, sem implicar p-valores idênticos ou
equivalência universal. As diferenças pequenas das estimativas são afetadas
por erro Monte Carlo; os intervalos são da simulação, não dos dados reais.

As simulações usam Bernoulli iid em todas as situações. Q3 testa amostra
pequena/aproximação insuficiente, não dependência temporal ou sobredispersão.
Os artefatos não contêm inferência nova sobre o CSV real.
