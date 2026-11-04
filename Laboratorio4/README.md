# Laboratório 04 — Sprint 01

O [trabalho de Luidi na Issue #30](https://github.com/flavioferreiradev/Software-Measurement-and-Experimentation/issues/30)
fornece dados reais, cenário P4, previsão inicial, gerador Bernoulli, teste Z,
binomial exato e o contrato G1/G2. O [trabalho do Flávio na Issue #31](https://github.com/flavioferreiradev/Software-Measurement-and-Experimentation/issues/31)
acrescenta os gráficos e o dashboard inicial da S01. Estudos Q1/Q2/Q3,
G3/G4 e apresentação pertencem às etapas posteriores.

Repositório: [Software-Measurement-and-Experimentation](https://github.com/flavioferreiradev/Software-Measurement-and-Experimentation).
Project existente: [Kanban #3](https://github.com/users/flavioferreiradev/projects/3).

## Instalação

Python 3.12 ou 3.13. A partir da raiz do repositório:

```powershell
cd Laboratorio4
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Linux/macOS: substituir a ativação por `source .venv/bin/activate`.
Dependências diretas fixadas: NumPy 2.4.2, SciPy 1.17.1, pytest 8.4.2,
Streamlit 1.52.2 e Plotly 6.5.0.
Não depende de arquivos, ambientes ou datasets dos outros laboratórios.

## Reprodução por comando único (após instalação)

Dentro de `Laboratorio4`, com ambiente ativo:

```bash
python -m src.run_demo
```

O comando valida o CSV e sua auditoria, estima p, gera **uma** amostra com
`default_rng(42)`, aplica ambos os testes e escreve:

- `results/demo_s01.json`: contrato G1/G2, parâmetros e resultados;
- `results/simulated_sample.csv`: a amostra da demonstração;
- `results/demo_interpretation.md`: tabela e interpretação.

Funciona sem rede e sem token. Não faz nova coleta. O dashboard usa diretamente
esses arquivos versionados.

## Abrir o dashboard por comando único

Dentro de `Laboratorio4/`, com o ambiente ativo:

```bash
streamlit run dashboard/app.py
```

O navegador abrirá o endereço local informado pelo Streamlit. O comando não
requer token, rede nem nova coleta. O topo contém links para o próprio
dashboard, o repositório e o GitHub Projects. No Windows, execute o mesmo
comando no PowerShell com `.venv` ativado; no Linux/macOS, use o mesmo comando
no terminal após `source .venv/bin/activate`.

As seções da S01 são **Cenário**, **Os dados (G1)** e **Como os testes funcionam
(G2)**. Os painéis G2 mostram p-valores da amostra *simulada*; os dados reais
são apresentados somente de forma descritiva nesta sprint. Veja
[dashboard/README.md](dashboard/README.md) para a arquitetura visual.

Interface reutilizável (para não sobrescrever a demonstração oficial):

```bash
python -m src.run_demo --n 60 --p 0.08 --seed 42 --output .pytest-tmp/exemplo
```

`generate_sample(n, p, seed=42)` e `test_proportion(sample, p0=0.05, alpha=0.05)`
estão em `src/statistics.py`. Não há laço de experimentos da S02.

## Dados e exemplo preservado

Fonte: [pytest-dev/pytest, workflow test](https://github.com/pytest-dev/pytest/actions/workflows/test.yml),
`push` em `main`, janela de criação 01/10/2026 a 04/11/2026 18:00 UTC.
Coleta em 04/11/2026, 18:47:46 UTC (15:47:46 em São Paulo).
Das 46 execuções concluídas, quatro canceladas foram excluídas. Permaneceram
**42 observações**, 38 sucessos e quatro falhas, sem IDs duplicados.
Cada URL verificável está em `data/real_ci.csv`; as 46 observações recebidas e
os descartes estão em `data/source_metadata.json`.

Gerador: n=42, p=4/42≈0,095238095, seed=42. Meta p₀=0,05, α=0,05,
H₀: p≤0,05, H₁: p>0,05. A amostra simulada teve quatro falhas; a coincidência
na contagem com a amostra real é casual — as sequências são diferentes.

| Teste na amostra simulada | Estatística | p-valor | Decisão |
|---|---:|---:|---|
| Z, sem correção de continuidade | 1,345185418 | 0,089282682 | Não rejeitar H₀ |
| Binomial exato | p̂=0,095238095; K=4 | 0,156892615 | Não rejeitar H₀ |

O exemplo não fornece evidência suficiente de taxa superior a 5%. Não rejeitar
não comprova H₀. Trata-se de uma amostra simulada; não é uma conclusão sobre
o projeto fonte nem uma comparação de poder dos testes.

## Validação

```bash
python -m pytest -q
```

Se o diretório temporário do Windows estiver sem permissão, crie um diretório
local e use um subdiretório **reservado e descartável** (pytest limpa `--basetemp`):

```powershell
New-Item -ItemType Directory -Force .pytest-tmp | Out-Null
python -m pytest -q --basetemp=.pytest-tmp/lab04-verification
```

Os 73 testes da implementação estatística passaram localmente na entrega da
#30. A suíte ampliada também cobre o contrato consumido pelos gráficos e a
execução offline da página Streamlit. Os testes anteriores cobrem entradas
inválidas, sementes, casos extremos, referências matemáticas
independentes, SciPy, classificação, deduplicação, CSV adulterado, contrato,
massas de probabilidade, regiões críticas e CLI offline.
O GitHub Actions executa a mesma suíte em Windows e Ubuntu com Python 3.12.
Evidência local em [docs/validacao.md](docs/validacao.md).
Validação dos gráficos e da página em
[docs/validacao_dashboard.md](docs/validacao_dashboard.md).

## Nova coleta opcional

```bash
python -m src.collect --output .pytest-tmp/nova_coleta
```

A API pública aceita requisições sem token. Opcionalmente use `GITHUB_TOKEN`
no ambiente para limite autenticado; nenhum token é gravado.
Evite substituir o CSV oficial: reexecuções podem mudar as tentativas mais
recentes. O snapshot versionado é a referência da entrega.

## Estrutura e documentação

```text
Laboratorio4/
  data/          real_ci.csv, source_metadata.json
  src/           collect.py, data.py, statistics.py, run_demo.py
  results/       demo_s01.json, simulated_sample.csv, demo_interpretation.md
  docs/          auditoria, cenário, previsão, contrato, validação e handoff
  tests/         estatística, integridade e integração offline
  dashboard/     aplicação Streamlit, gráficos e estilos da S01
  requirements.txt
  pytest.ini
```

- [Auditoria inicial](docs/auditoria_inicial.md)
- [Cenário e metodologia](docs/cenario_metodologia.md)
- [Previsão anterior à simulação](docs/previsao_inicial.md)
- [Contrato de integração v1](docs/contrato_integracao.md)
- [Handoff para Flávio](docs/handoff_flavio.md)
- [Validação do dashboard S01](docs/validacao_dashboard.md)
