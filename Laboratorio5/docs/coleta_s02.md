# Lab05S02 — execução e validação da coleta completa

**Responsável:** Flávio ([Issue #39](https://github.com/flavioferreiradev/Software-Measurement-and-Experimentation/issues/39)). **Data:** 25/11/2026. O [protocolo](protocolo_s02.md), executor e validador foram publicados **antes da coleta** no commit [`213ab15`](https://github.com/flavioferreiradev/Software-Measurement-and-Experimentation/commit/213ab15).

## Execução

Na raiz do repositório, com diretório `results/full_s02/` inicialmente vazio:

```bash
python3 Laboratorio5/src/run_full_s02.py
python3 Laboratorio5/src/validate_full_s02.py
```

A execução medida por `/usr/bin/time -p` levou **16,80 s** de tempo real. Não
foi iniciada outra carga intencional de medição em paralelo. O ambiente
registrado foi Python **3.15.2**, SQLite **3.53.4** e macOS **26.7.3 arm64**.
Os bancos temporários foram criados e destruídos a cada par.

## Integridade dos dados

O validador independente encerrou com `status: passed`. O arquivo
[`validation.json`](../results/full_s02/validation.json) contém os SHA-256 dos
quatro arquivos de origem; os dados permanecem em
[`results/full_s02/`](../results/full_s02/).

| Verificação | Resultado |
|---|---:|
| Pares independentes completos | 20 |
| Leituras cronometradas | 6.000; 3.000 por condição |
| Lotes de inserção cronometrados | 120; 60 por condição |
| Pedidos finais por banco | 51.500 |
| Sementes, hashes iniciais e finais distintos entre pares | 20 de cada |
| Plano sem índice | `SCAN orders` em todos os pares |
| Plano com índice | `SEARCH orders USING INDEX idx_customer_created` em todos os pares |
| Respostas e conteúdo final entre condições | Iguais em cada par |

O validador também conferiu a mesma sequência de clientes e contagens de
resposta nas duas condições, posições e blocos completos, durações positivas,
configuração, versão e resumo recomputado. Nenhum par nem observação foi
excluído. Não houve repetição de coleta.

## Diagnóstico descritivo da instrumentação

Estes números vêm do [`summary.json`](../results/full_s02/summary.json) e
resumem as **submedições agrupadas**. Eles ajudam a detectar problemas de
escala e não substituem a análise pareada da Issue #40.

| Métrica | Sem índice | Com índice |
|---|---:|---:|
| Mediana por consulta | 1,025625 ms | 0,012958 ms |
| p95 por consulta | 1,155167 ms | 0,015750 ms |
| Mediana por linha inserida em lote | 0,002374 ms | 0,009935 ms |
| Mediana do arquivo final | 1.085.440 bytes | 2.031.616 bytes |

O tempo mediano de construção do índice foi **12,650417 ms**, medido à parte.
Consultas do mesmo par compartilham banco, sistema e cache; **não** são 3.000
réplicas independentes por tratamento. O Luidi deverá usar os **20 pares** para
estimar efeitos, incerteza e testar a hipótese. Os resultados descrevem esta
carga sintética, esta versão e esta máquina; não medem desempenho em aplicações
de produção.
