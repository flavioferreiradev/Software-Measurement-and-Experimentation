# Contrato estatístico S02 v1.0.0 — G3/G4

Produtor: `python -m src.run_experiments`, Issue #34 (LuidiC).
Consumidor: trabalho posterior do Flávio. Este contrato é um documento/arquivo
separado do G1/G2; os nomes e significados do JSON S01 permanecem intactos.

## Reprodução e arquivos

Dentro de `Laboratorio4/`, ambiente do projeto ativo:

```bash
python -m src.run_experiments
```

Não requer rede, token ou nova coleta. Lê o CSV e metadados já congelados da
S01, para validar sua integridade e n=42, e grava **somente** estes arquivos:

- `results/experiments_s02.json`: contrato principal, 12 linhas/células.
- `results/experiments_s02.csv`: forma tabular, 24 linhas (uma por célula/teste).
- `results/experiments_s02_summary.md`: resultados e confronto teórico legíveis.

O CLI aceita `--output`, `--seed` e `--repetitions` para testes exploratórios.
A entrega oficial usa seed=42 e repetitions=10000. Não substituir os artefatos
oficiais por execução exploratória. Exemplo separado:

```bash
python -m src.run_experiments --repetitions 100 --seed 7 --output .pytest-tmp/s02-smoke
```

## Estrutura do JSON

| Campo de topo | Conteúdo e unidade |
|---|---|
| `schema_version` | String `1.0.0`, versão própria da S02 |
| `scope` | S02 Q1/Q2/Q3, Issue #34 |
| `protocol` | p₀, α, seed, repetições, níveis de p, definição/unidade do efeito, RNG, pareamento e reutilização do nulo |
| `source_s01` | Caminho/hash do CSV S01 e n=42; uso apenas do tamanho |
| `scenarios` | Duas situações: reference_n200 e small_n42, contagens esperadas e limiares críticos |
| `rows` | Uma linha por situação × p, 12 linhas sem duplicar o ponto nulo |
| `g3` | IDs das duas linhas sob H₀, campo y e taxa nominal 0,05 |
| `g4` | IDs das 12 linhas, campo x, campo y e definição das séries |
| `mc_validation` | Método, erro familiar máximo 0,01 e 24 comparações |
| `software` | Versões de Python, NumPy e SciPy |

Cada item de `scenarios` inclui `id`, `label_pt`, `n`, `role`, `n_source`,
`expected_failures_h0`, `expected_successes_h0`, a regra prática normal e o
booleano `normal_rule_of_thumb_met`. `rejection_rules.<test>.critical_k` é o
primeiro inteiro que rejeita (null representa região vazia); `rule` descreve
a cauda. Aqui, n=200 rejeita em K≥16 nos dois testes; n=42 rejeita em K≥5 no
Z e K≥6 no exato. N=42 é explicitamente a situação de amostra pequena.

## Campos de cada linha de `rows`

| Campo | Tipo / significado |
|---|---|
| `id` | String única e estável, baseada na situação e fração de p |
| `scenario_id` | Referência ao `id` de `scenarios` |
| `n` | Inteiro; execuções de CI por amostra |
| `p` | Probabilidade geradora de falha; não é p-valor |
| `delta` | p−p₀, em proporção; ×100 apenas para exibir pontos percentuais |
| `estimand` | `type_i_error` em p=p₀; `power` em p>p₀ |
| `used_by` | Q1/Q2/Q3 no nulo; Q2/Q3 nas alternativas |
| `repetitions` | Inteiro 10000 na entrega oficial |
| `stream_entropy` | `[seed,n,p_numerador,p_denominador]`, inteiros para SeedSequence |
| `counts_sha256` | SHA256 da sequência K codificada em uint32 little-endian |
| `counts_histogram` | Lista de n+1 inteiros: índice k contém a frequência de K=k; soma=10000 |
| `tests` | Objetos `z` e `binomial_exact`, sobre as mesmas repetições |
| `paired_decisions` | Contagens `neither`, `z_only`, `exact_only`, `both`; soma=10000 |

Em `tests.<test>`:

| Campo | Tipo / significado |
|---|---|
| `rejections` | Inteiro r, número de p-valores estritamente menores que α |
| `rejection_rate` | r/repetitions, em [0,1] |
| `mc_standard_error` | Erro-padrão Monte Carlo estimado da taxa, em proporção |
| `mc_ci95_wilson` | [inferior,superior], IC95% pontual Monte Carlo |
| `theoretical_rejection_rate` | Prₚ(K na região crítica do teste), calculada pela lei binomial exata |
| `theory_mc_standard_error` | √[q(1−q)/R], com q teórico |
| `mc_minus_theory` | Taxa simulada menos q, em proporção |
| `mc_validation_count_interval` | [mínimo,máximo] inteiro para r~Binomial(R,q), com ajuste Bonferroni |
| `mc_consistent_with_theory` | Booleano: r pertence ao intervalo anterior |

O histograma basta para recontar rejeições em cada região crítica. O hash e a
entropia permitem verificar também a ordem das 10.000 contagens regeneradas.
Não há NaN nem infinito numérico. Taxas/contagens não devem ser recalculadas
usando números arredondados na apresentação.

## G3 — erro tipo I

Selecionar `rows` pelos IDs em `g3.row_ids` (equivalente a
`estimand == "type_i_error"`). Agrupar por `scenario_id` e teste. Eixo y:
`tests.<test>.rejection_rate`; linha nominal horizontal em `g3.nominal_rate`
(0,05). Usar `scenarios[].label_pt` nos rótulos. Os intervalos MC podem ser
mostrados a partir de `mc_ci95_wilson`. Não trocar 5% nominal pela probabilidade
teórica realizada; são referências diferentes e ambas estão disponíveis.

## G4 — curvas por situação e efeito

Usar todas as linhas de `g4.row_ids`, ordenar por `delta`, traçar os dois
testes por situação. Eixo x: `delta` (proporção; opcionalmente ×100 para pp).
Eixo y: `tests.<test>.rejection_rate`. Há quatro séries: n=200/Z, n=200/exato,
n=42/Z e n=42/exato. Manter os dois testes no mesmo gráfico; distinguir
situação por estilo/painel e teste por cor consistente com G2/G3.
Isso é uma orientação de consumo; nenhum gráfico foi criado nesta entrega.

O ponto Δ=0 referencia a mesma linha do G3 e deve ser descrito como erro tipo
I. As taxas de n=200 coincidem porque os testes usam o mesmo limiar inteiro
neste protocolo. Não alterar dados para separar visualmente essas curvas.

## Leitura mínima (arquivo dentro de dashboard/)

```python
import json
from pathlib import Path

lab = Path(__file__).resolve().parents[1]
payload = json.loads((lab / "results/experiments_s02.json").read_text(encoding="utf-8"))
assert payload["schema_version"] == "1.0.0"
rows = {row["id"]: row for row in payload["rows"]}
g3_rows = [rows[key] for key in payload["g3"]["row_ids"]]
g4_rows = sorted((rows[key] for key in payload["g4"]["row_ids"]),
                 key=lambda row: (row["scenario_id"], row["delta"]))
for row in g4_rows:
    effect = row["delta"]
    z_rate = row["tests"]["z"]["rejection_rate"]
    exact_rate = row["tests"]["binomial_exact"]["rejection_rate"]
```

Mudança incompatível de nomes, tipos, unidades ou interpretação exige nova
versão major da S02. Os testes protegem versão, estrutura, resultados,
reprodução, dados S01, fronteiras e referências teóricas. O contrato G1/G2
continua na versão original e não foi ampliado nem reescrito.

O manifesto dos 30 arquivos S01 é evidência histórica da auditoria local.
O teste de preservação congela somente os cinco arquivos de dados/resultados
S01; ele permite que o Flávio amplie o código do dashboard na sua tarefa.
