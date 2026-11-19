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
