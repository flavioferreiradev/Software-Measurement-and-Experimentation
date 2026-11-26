# Lab05 — experimento com SQLite em operação

## Sprint 01

O estudo compara a mesma carga de consultas e inserções no SQLite com e sem um
índice composto em `(customer_id, created_at DESC)`. A [proposta e o método](docs/proposta_s01.md)
registram a pergunta, as sete categorias de pesquisa, as fontes de impacto e o
plano até a entrega final. Os [resultados do piloto](docs/resultados_piloto_s01.md)
explicam o alcance da primeira coleta.

### Executar a coleta piloto

Requer Python 3.10+ com o módulo padrão `sqlite3`. Não há dependências externas,
credenciais nem serviço remoto. A partir da raiz do repositório:

```bash
python3 Laboratorio5/src/run_pilot.py
```

O comando recria bancos temporários e grava em `Laboratorio5/results/pilot_s01/`:

- `read_timings.csv`: duração de cada consulta;
- `write_timings.csv`: duração de cada lote de inserção;
- `metadata.json`: versão, parâmetros, sementes, hashes dos dados, planos de
  consulta e tamanhos dos bancos;
- `summary.json`: estatísticas descritivas do piloto.

Os dados são sintéticos e não contêm informações pessoais. Os tempos variam com
CPU, sistema operacional, cache e versão do SQLite. Para reproduzir o *mesmo
ambiente* do resultado versionado, consulte `metadata.json`. Para verificar o
contrato e a geração determinística:

```bash
python3 -m unittest discover -s Laboratorio5/tests -v
```

O script aceita `--help` para alterar volume de dados, número de consultas,
blocos, repetições, inserções e diretório de saída. Não misture medições de
versões ou máquinas diferentes na análise.

## Sprint 02 — coleta completa

O [protocolo congelado](docs/protocolo_s02.md) fixa a configuração de 20 pares
independentes, SQLite 3.53.4, métricas e critérios de validação antes da coleta.
A [Issue #39](https://github.com/flavioferreiradev/Software-Measurement-and-Experimentation/issues/39)
é a entrega de coleta e validação; a
[Issue #40](https://github.com/flavioferreiradev/Software-Measurement-and-Experimentation/issues/40)
trata da análise dos dados e das ameaças à validade.

Para reproduzir a coleta completa em um ambiente com a versão indicada do
SQLite, use um **diretório vazio**. O executor recusa sobrescrever os dados
versionados:

```bash
python3 Laboratorio5/src/run_full_s02.py --output-dir /tmp/lab05-full-s02
python3 Laboratorio5/src/validate_full_s02.py --output-dir /tmp/lab05-full-s02
```

A coleta oficial versionada fica em `results/full_s02/`. O validador confere
metadados, pareamento, contagens, planos, durações, resumos e hashes de todos
os arquivos brutos, gerando `validation.json`. A execução e seus limites estão
registrados em `docs/coleta_s02.md`. Os tempos não serão idênticos em outra
máquina ou execução, mesmo com os mesmos dados e a mesma versão do SQLite.

### Sprint 02 — análise dos 20 pares

O [relatório final da S02](docs/resultados_s02.md) responde à pergunta,
apresenta o teste exato dos sinais pareado, tamanhos de efeito, intervalos e
as quatro ameaças à validade. Use a coleta já versionada, **sem refazê-la**:

```bash
python Laboratorio5/src/analyze_s02.py
python -m unittest discover -s Laboratorio5/tests -p test_analysis_s02.py -v
```

Requer apenas Python 3.10+, sem dependências externas ou exigência de versão
do SQLite local. O script revalida uma cópia temporária dos dados, confere os
hashes publicados e preserva a origem, inclusive em checkouts Windows/CRLF.
Os testes de análise não executam coleta. O diretório
[`results/analysis_s02/`](results/analysis_s02/) recebe a tabela por par,
descritivas, efeitos, teste, auditoria, tabelas Markdown e dois gráficos SVG.
O relatório detalha fórmulas, convenções e como rastrear os números aos brutos.
Use `--output-dir .pytest-tmp/lab05-analysis-check` para uma comparação em
diretório separado; consulte `--help` para os caminhos de entrada e saída.

A análise usa **n = 20 pares**, com 6.000 leituras como submedições. O ganho
mediano pareado de leitura foi 1,014261 ms por consulta (razão 78,1881), com
custo mediano de inserção 4,3015 vezes maior e arquivo 87,1698% maior.
Estes são resultados desta carga sintética nesta máquina, sem medição de
impacto real em produção.
