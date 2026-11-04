# Contrato G1/G2 — versão 1.0.0

Consumidor: dashboard da Issue #31. Produtor: `python -m src.run_demo`, Issue
#30. Caminhos abaixo são relativos a `Laboratorio4/`. Não é necessário fazer
nova coleta ou modificar o código estatístico para criar os gráficos.

## Arquivos e estabilidade

| Arquivo | Formato | Uso |
|---|---|---|
| `data/real_ci.csv` | CSV UTF-8, vírgula, cabeçalho, LF | Uma linha por run válido, 42 linhas |
| `data/source_metadata.json` | JSON UTF-8 | Fonte, janela, data da coleta, SHA256 e auditoria de 46 runs |
| `results/simulated_sample.csv` | CSV UTF-8, `observation,failed` | Ordem 1..n e valores binários da demonstração |
| `results/demo_s01.json` | JSON UTF-8, sem NaN/infinito numérico | Contrato completo do dashboard |
| `results/demo_interpretation.md` | Markdown UTF-8 | Tabela e interpretação legível |

Mudança incompatível requer nova versão major de `schema_version`. Acréscimos
compatíveis podem usar minor. Não renomear/remover campos v1 ao criar gráficos.
O contrato é protegido por testes com comparação recursiva do JSON versionado,
incluindo valores numéricos (tolerância 10⁻¹² entre plataformas), CSV exportado,
massas, caudas, decisões e invariantes. Versões de software são registradas;
mudança de versão Python não altera o significado do contrato.

## CSV real

| Campo | Tipo lógico / unidade | Significado |
|---|---|---|
| `run_id` | inteiro positivo único | Identificador GitHub, nunca índice sequencial |
| `repository` | texto | `pytest-dev/pytest` |
| `workflow_id` | inteiro | 22158026 |
| `workflow_name` | texto | Nome retornado pela API |
| `head_branch` | texto | main |
| `event` | texto | push |
| `status` | texto | completed |
| `conclusion` | enum | success, failure ou timed_out |
| `failed` | inteiro binário | 0=success; 1=failure ou timed_out |
| `run_attempt` | inteiro ≥1 | Tentativa mais recente observada do mesmo run.id |
| `created_at`, `updated_at` | ISO 8601 UTC | Criação/atualização; não usar como duração |
| `head_sha` | 40 caracteres hexadecimais | Commit executado |
| `html_url` | URL pública | Link de verificação do run |

Não há campos ausentes nas observações incluídas. No `audit` do JSON de
metadados, `failed=null` representa conclusão excluída; `selection` informa
`included`, `excluded_conclusion` ou `outside_latest_60` (este último não ocorre
no snapshot). Esses registros excluídos não entram nos histogramas reais.

## JSON principal

| Campo | Conteúdo |
|---|---|
| `schema_version` | String `1.0.0` |
| `scope` | Limita o resultado à demonstração S01 |
| `scenario` | P4, pergunta, H₀/H₁, p₀, α, direção, codificação e unidade amostral |
| `source` | Repositório, workflow, branch, evento, janela, período observado, data e hash |
| `empirical` | n=42, k=4, p̂=4/42 e variância Bernoulli ajustada |
| `generator` | Bernoulli, API NumPy, n, p, seed e origem dos parâmetros |
| `g1` | Valores e contagens reais/simulados e bins comuns |
| `example` | Resumo da amostra simulada e ambos os testes |
| `g2` | Distribuições, suporte, densidade/massas, regiões críticas e caudas |
| `software` | Versões Python, NumPy e SciPy |

`example.n`, `example.k`, `example.p_hat` usam exatamente
`g1.simulated.values`. `example.effect_difference=p_hat-p0` está em proporção,
multiplicar por 100 apenas para exibir pontos percentuais. Não é inferência
final nos dados reais. `example.tests.z` e `.binomial_exact` contêm
`statistic_name`, `statistic`, `p_value`, `reject_h0` (booleano), `alternative`,
`alpha`, `p0` e `interpretation_pt`. O exato também fornece `count_statistic`.
O Z fornece `standard_error_h0`, contagens esperadas sob H₀ e aviso sobre a
regra prática de aproximação. Não recalcular decisões com p-valores arredondados.

## Construir G1

Usar `g1.real.values` e `g1.simulated.values`, lado a lado, com os mesmos
`bin_edges=[-0.5,0.5,1.5]`. Os dois intervalos representam sucesso (0) e falha
(1). `counts` já contém [sucessos,falhas]; também pode ser consumido diretamente
como frequências de cada classe. Eixo x: resultado binário; eixo y recomendado:
frequência relativa (counts/n), ou contagem de execuções com unidade explícita.
Usar mesma escala nos painéis e mostrar n, k e p. Não tratar os códigos 0/1
como tempos ou medidas contínuas. Para o exemplo, ambas as contagens são
[38,4]; não é erro de coleta, são duas sequências distintas.

## Construir G2 — Z

- Desenhar `g2.z.x` × `pdf` como curva da **aproximação N(0,1)**.
- Eixo x: Z, desvios-padrão; eixo y: densidade de probabilidade.
- Rejeição: `Z > critical_value`, crítico≈1,644853627.
- Área do p-valor: da estatística observada≈1,345185418 até +∞.
- `p_value_tail.area`≈0,089282682 e `critical_tail.area`=0,05 são as áreas
  analíticas. O limite de desenho da curva é finito: a área não termina no
  último ponto da grade. Se integrar numericamente para sombrear, inserir os
  limiares no traçado e indicar que a cauda continua até infinito.
- `finite_sample_null` fornece ainda o suporte **discreto real** do Z e suas
  massas sob Binomial(n,p₀), para uma sobreposição opcional. N(0,1) não é a
  lei exata de Z nesta amostra; explicitar essa limitação junto ao gráfico.

## Construir G2 — binomial exato

- Desenhar barras/stems em `k_support=0..n`, altura `pmf`, lei Binomial(n,p₀).
  Eixo x: número K de falhas; eixo y: massa de probabilidade (não densidade).
  Se preferir p̂ no eixo x, usar `p_hat_support`; as massas são as mesmas.
- Destacar barras onde `rejection_mask=true`: aqui **K≥6**.
- Destacar barras onde `p_value_mask=true`: aqui **K≥4**, incluindo K observado.
- `p_value_area`≈0,156892615 corresponde à soma dessas massas.
- `critical_area`≈0,017432006 corresponde à região crítica discreta, abaixo de
  0,05. Não forçar a região do exato a ter exatamente 5% nem usar curva normal.
- `critical_k=null` significa região de rejeição vazia (em configurações
  alternativas); nunca interpretar null como zero. `right_tail_inclusive`
  fornece Pr(K≥j) para cada j e permite conferir os limiares.

Os dois sombreamentos podem se sobrepor; usar hachuras/contornos ou legendas
que diferenciem região crítica e cauda do p-valor. A decisão do exemplo é
`reject_h0=false` nos dois testes. Não há valores fictícios ou placeholders.

## Consumo mínimo em Python

```python
import json
from pathlib import Path

lab_root = Path(__file__).resolve().parents[1]  # arquivo em dashboard/
payload = json.loads((lab_root / "results/demo_s01.json").read_text(encoding="utf-8"))
assert payload["schema_version"] == "1.0.0"
real = payload["g1"]["real"]["values"]
simulated = payload["g1"]["simulated"]["values"]
z_reference = payload["g2"]["z"]
exact_reference = payload["g2"]["binomial_exact"]
```
