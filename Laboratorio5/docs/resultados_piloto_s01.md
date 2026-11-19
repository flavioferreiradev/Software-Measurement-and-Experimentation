# Lab05S01 — validação e resultados do piloto

O piloto foi executado em 18/11/2026 pelo comando único do README. Os arquivos
brutos e os metadados estão versionados em `results/pilot_s01/`. Esta coleta
verifica a viabilidade do método; **não é a análise conclusiva do Lab05**.

## Protocolo executado

- 3 pares de bancos gerados independentemente, 20.000 pedidos iniciais por
  banco, 1.000 clientes, semente-base `20261118`;
- 2 blocos por par, com 30 consultas por bloco e 100 inserções em lote;
- mesma tabela, registros, clientes consultados e inserções em cada par;
- ordem das condições alternada, aquecimento igual, respostas comparadas;
- Python 3.15.2, SQLite 3.53.4, macOS 26.7.3 arm64; `journal_mode=DELETE`,
  `synchronous=FULL`, cache configurado em 2.000 KiB.

`EXPLAIN QUERY PLAN` confirmou a manipulação: a condição sem índice fez
`SCAN orders` e usou uma árvore temporária para a ordenação; a condição com
índice fez `SEARCH orders USING INDEX idx_customer_created (customer_id=?)`.
O script verificou igualdade dos resultados das consultas e contagem final de
20.200 linhas nos dois bancos de cada par. As três sementes e hashes dos dados
iniciais estão em `metadata.json`.

## Observações descritivas

| Métrica | Sem índice | Com índice | Leitura do piloto |
|---|---:|---:|---|
| Mediana por consulta | 0,4621 ms | 0,0140 ms | Cerca de 33 vezes menor com índice nesta carga. |
| p95 por consulta | 1,0978 ms | 0,0285 ms | A cauda das consultas medidas também foi menor. |
| Mediana por inserção em lote | 0,00785 ms | 0,02411 ms | Cerca de 3,1 vezes maior com índice neste piloto. |
| Tamanho mediano do banco | 421.888 bytes | 786.432 bytes | Aumento de 364.544 bytes, ou 86,4%. |

Foram medidas 180 consultas por condição, mas elas pertencem a **apenas três
pares independentes de bancos**. As inserções somam somente seis lotes por
condição. Portanto, não interpretamos as 180 latências como tamanho amostral
independente, nem calculamos p-valores conclusivos a partir deste piloto.
Os tempos são sensíveis a cache, sistema operacional e carga concorrente.

## Decisão para a próxima sprint

O piloto mostrou que os dois tratamentos produzem respostas iguais, acionam
planos de consulta diferentes e têm efeitos mensuráveis nas três dimensões
propostas. O script também executou sem erro uma repetição de teste com 50 mil
linhas, 50 consultas por bloco, três blocos e 500 inserções por bloco, o que
apoia a viabilidade do volume previsto para a S02. Antes da coleta final,
fixaremos a versão do SQLite e o protocolo, executaremos os pares independentes
sem carga concorrente intencional e analisaremos efeitos **por par**.

O ganho de consulta observado é válido para esta consulta e esta distribuição
sintética de clientes. O custo de armazenamento é proporcionalmente grande
porque o banco piloto é pequeno; não deve ser projetado como 86,4% para bancos
de outros tamanhos. O impacto em aplicações reais dependerá de volume de
leituras e escritas, hardware, cache e padrão dos dados.
