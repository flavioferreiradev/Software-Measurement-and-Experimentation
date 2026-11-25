# Lab05S02 — protocolo congelado da coleta completa

**Registrado em 25/11/2026, antes da coleta completa.** Responsável pela
instrumentação, execução e validação: Flávio ([Issue #39](https://github.com/flavioferreiradev/Software-Measurement-and-Experimentation/issues/39)).
A análise posterior é responsabilidade do Luidi ([Issue #40](https://github.com/flavioferreiradev/Software-Measurement-and-Experimentation/issues/40)).

## Pergunta, unidade e variáveis

A pergunta e as hipóteses permanecem as da [proposta S01](proposta_s01.md):
o índice composto `(customer_id, created_at DESC)` melhora a latência de uma
consulta de pedidos recentes por cliente no SQLite? Qual o custo em escrita e
armazenamento? A **unidade independente de análise é o par de bancos** com a
mesma carga e semente; consultas e lotes dentro do par são submedições.

| Item fixado | Valor |
|---|---|
| SQLite | 3.53.4; o executor recusa outra versão |
| Ambiente da execução planejada | Python 3.15.2, macOS 26.7.3 arm64; versão e plataforma efetivas serão gravadas em `metadata.json` |
| Pares independentes | 20, com sementes `20261125 + 1009 × (par - 1)` |
| Dados iniciais | 50.000 pedidos sintéticos por banco, 2.500 clientes |
| Carga por par | 3 blocos; 50 clientes sorteados sem reposição e consultados em cada bloco; 500 inserções por bloco |
| Condições | Sem índice secundário; com `idx_customer_created ON orders(customer_id, created_at DESC)` |
| Consulta | `WHERE customer_id = ? ORDER BY created_at DESC LIMIT 20` com as mesmas colunas e clientes nas duas condições |
| PRAGMAs | `journal_mode=DELETE`, `synchronous=FULL`, `cache_size=-2000` |
| Ordem | Alternância da ordem de leitura por bloco e par; escrita em ordem inversa |
| Aquecimento | Verificação de igualdade e uma execução de todas as consultas nas duas condições antes do bloco cronometrado |
| Medição | `time.perf_counter_ns`; consulta inclui materialização do resultado; escrita inclui `executemany` e `commit` |

Serão **6.000 consultas cronometradas** (3.000 por condição) e **120 lotes de
escrita** (60 por condição). O desfecho primário para análise é a diferença
entre as medianas de latência de leitura das duas condições em cada par.
Desfechos secundários são o tempo de inserção por linha em cada par e os bytes
finais de cada banco. O tempo de construção do índice é registrado à parte.

## Regras de validação e exclusão

Não haverá exclusão de latências individuais por serem altas ou baixas. O
executor interrompe a coleta se os planos de consulta forem diferentes dos
esperados, se alguma resposta divergir, se a contagem final não corresponder
ou se o conteúdo final dos dois bancos tiver hashes diferentes. A validação
independente dos arquivos exigirá 20 pares completos, IDs e posições de
consulta iguais entre condições, durações positivas, metadados coerentes e
resumo recomputado a partir dos dados brutos. Uma coleta interrompida será
descartada **inteira** e repetida em diretório novo, com motivo registrado.

Os bancos são novos e temporários a cada par. A versão, configuração, sementes,
hashes iniciais e finais, planos, bytes e durações por observação serão
versionados. A coleta deve rodar sem outra carga intencional na mesma máquina.
Os dados são sintéticos; nenhum sistema de terceiros é submetido a carga.

## Comandos congelados

Na raiz do repositório, em um checkout com SQLite 3.53.4:

```bash
python3 Laboratorio5/src/run_full_s02.py
python3 Laboratorio5/src/validate_full_s02.py
```

Para uma reprodução, passar `--output-dir` apontando para **diretório vazio**
nos dois comandos. O script recusa sobrescrever o resultado versionado.
Mudanças de protocolo após este registro deverão ser descritas antes de nova
coleta; não misturaremos resultados de versões ou máquinas diferentes.
