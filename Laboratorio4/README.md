# Laboratório 04 — entrega final

O [trabalho de Luidi na Issue #30](https://github.com/flavioferreiradev/Software-Measurement-and-Experimentation/issues/30)
fornece dados reais, cenário P4, previsão inicial, gerador Bernoulli, teste Z,
binomial exato e o contrato G1/G2. O [trabalho do Flávio na Issue #31](https://github.com/flavioferreiradev/Software-Measurement-and-Experimentation/issues/31)
acrescenta os gráficos e o dashboard inicial da S01. A implementação da
[Issue #34](https://github.com/flavioferreiradev/Software-Measurement-and-Experimentation/issues/34)
acrescenta os experimentos Q1/Q2/Q3 e o contrato G3/G4. A
[Issue #35](https://github.com/flavioferreiradev/Software-Measurement-and-Experimentation/issues/35)
integra G3/G4, a inferência dos dados reais e as sete seções do dashboard.
A apresentação oral encerra a entrega do grupo.

Repositório: [Software-Measurement-and-Experimentation](https://github.com/flavioferreiradev/Software-Measurement-and-Experimentation).
Project existente: [Kanban #3](https://github.com/users/flavioferreiradev/projects/3).

## Dashboard Next.js — execução local e Vercel

O dashboard público agora é uma aplicação Next.js com App Router e exportação
estática. Dentro de `Laboratorio4/`, com Node.js 26.x:

```bash
npm ci
npm run dev
```

Abra `http://localhost:3000`. Para conferir exatamente o artefato que será
publicado, execute `npm run build`; os arquivos finais ficam em `out/`. A página
usa `results/demo_s01.json` e `results/experiments_s02.json`; no build, valida
o SHA256 e a auditoria de `data/real_ci.csv` e recalcula os dois p-valores reais.
Não precisa de API, token, banco de dados ou processo Python em produção.

**Publicar na Vercel:** importe este repositório e defina **Root Directory**
como `Laboratorio4`. O `vercel.json` seleciona o preset **Other**, executa
`npm ci` e `npm run build` e publica a pasta estática `out`. Não há variáveis
de ambiente. A versão final já está na `main`. Se o projeto foi criado antes
desta correção com preset Next.js e Output Directory `out` no painel, faça um
novo deploy da `main`: o `vercel.json` atualizado substitui essas opções.
GitHub Actions e Vercel são processos independentes; o bloqueio de cobrança
da CI não impede o build local.

Os gráficos G1–G4, o comparador interativo e as sete seções são gerados a
partir dos contratos versionados. O painel é estático: escolher n ou p mostra
pontos já simulados, sem executar uma nova simulação no navegador.

## Instalação do protocolo científico (Python)

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

## Reprodução integral por comando único (após instalação)

Dentro de `Laboratorio4`, com ambiente ativo:

```bash
python -m src.run_all
```

O comando valida o CSV e sua auditoria, reproduz a demonstração S01 com seed
42, executa as 12 células Q1/Q2/Q3 com 10.000 amostras cada e aplica os dois
testes ao CSV real. Escreve em `.pytest-tmp/lab04-full/`:

- `s01/`: contrato G1/G2, amostra simulada e interpretação da demonstração;
- `s02/`: JSON/CSV de G3/G4 e resumo das 120.000 amostras;
- `real_analysis.json`: estatísticas e p-valores calculados do CSV real.

Funciona sem rede, token ou nova coleta. A saída separada protege os snapshots
oficiais versionados em `results/`; o dashboard usa esses snapshots e recalcula
a inferência real diretamente de `data/real_ci.csv`. Para escolher outra pasta,
use `python -m src.run_all --output CAMINHO`.

## Dashboard Streamlit anterior (preservado para comparação)

Dentro de `Laboratorio4/`, com o ambiente ativo:

```bash
streamlit run dashboard/app.py
```

O navegador abrirá o endereço local informado pelo Streamlit. Essa versão
permanece no repositório para preservar a validação anterior; o dashboard de
publicação e apresentação está em Next.js. No Windows, execute o mesmo comando
no PowerShell com `.venv` ativado; no Linux/macOS, use o mesmo comando após
`source .venv/bin/activate`.

As sete seções são **Cenário**, **Os dados (G1)**, **Como os testes funcionam
(G2)**, **Erro tipo I (G3)**, **Poder (G4)**, **Dados reais** e **Conclusão**.
G2 permanece identificado como exemplo *simulado*; a tabela da seção 6 é
recalculada do CSV *real*. Veja [dashboard/README.md](dashboard/README.md)
para a arquitetura da versão Streamlit preservada.

Interface reutilizável (para não sobrescrever a demonstração oficial):

```bash
python -m src.run_demo --n 60 --p 0.08 --seed 42 --output .pytest-tmp/exemplo
```

`generate_sample(n, p, seed=42)` e `test_proportion(sample, p0=0.05, alpha=0.05)`
estão em `src/statistics.py`. `python -m src.run_demo` e
`python -m src.run_experiments` continuam disponíveis separadamente; não rode
`src.collect` para reproduzir a entrega.

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

A suíte cobre estatística, contratos S01/S02, preservação dos dados, gráficos
G1–G4, inferência do CSV real, execução integral e página Streamlit offline.
`npm ci && npm run build` valida adicionalmente a versão Next.js e gera o
artefato estático de publicação.
O workflow está configurado para Windows e Ubuntu com Python 3.12. A situação
da CI e a validação local da entrega final estão em
[docs/validacao_dashboard_final.md](docs/validacao_dashboard_final.md).
Registros anteriores: [S01 estatística](docs/validacao.md),
[S01 dashboard](docs/validacao_dashboard.md) e
[S02 experimentos](docs/validacao_s02.md).

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
  src/           coleta, estatística, experimentos e run_all.py
  results/       snapshots oficiais S01 e S02
  docs/          auditoria, cenário, previsão, contrato, validação e handoff
  tests/         estatística, integridade e integração offline
  dashboard/     aplicação Streamlit, G1–G4, inferência real e estilos
  app/           página e estilos Next.js (dashboard de publicação)
  components/    gráficos SVG e interações React
  lib/           contratos e análise do CSV real no build
  package.json   comandos e dependências Next.js
  vercel.json    configuração de saída estática para Vercel
  requirements.txt
  pytest.ini
```

- [Auditoria inicial](docs/auditoria_inicial.md)
- [Cenário e metodologia](docs/cenario_metodologia.md)
- [Previsão anterior à simulação](docs/previsao_inicial.md)
- [Contrato de integração v1](docs/contrato_integracao.md)
- [Handoff para Flávio](docs/handoff_flavio.md)
- [Validação do dashboard S01](docs/validacao_dashboard.md)
- [Contrato S02 para G3/G4](docs/contrato_integracao_s02.md)
- [Validação do dashboard final](docs/validacao_dashboard_final.md)

## S02 — Q1, Q2 e Q3 (Issue #34)

Entrega estatística publicada pelo
[PR #36](https://github.com/flavioferreiradev/Software-Measurement-and-Experimentation/pull/36).
O [handoff da Issue #35](docs/handoff_flavio_s02.md) documenta o contrato
consumido pelo dashboard.

Status de integração: [PR #36](https://github.com/flavioferreiradev/Software-Measurement-and-Experimentation/pull/36)
integrado à `main` em 11/11/2026. O registro de bloqueio de cobrança em
[docs/validacao_s02.md](docs/validacao_s02.md) descreve o estado da CI durante
a publicação da contribuição de Luidi; não representa o estado atual do merge.

Após a instalação, dentro de `Laboratorio4/`, um comando executa todo o protocolo:

```bash
python -m src.run_experiments
```

São 10.000 amostras por combinação de n∈{200,42} e
p∈{0,05;0,075;0,10;0,125;0,15;0,20}, com seed raiz 42 e fluxos identificados
por n/p. Total: 120.000 amostras; ambos os testes recebem as mesmas contagens.
O ponto nulo é reutilizado em Q1 e na origem da curva Q2. Q3 compara as duas
situações; n=42 tem aproximação normal questionável.

O comando é offline e não reescreve nenhum artefato S01. Acrescenta:

- `src/experiments.py` e `src/run_experiments.py`: núcleo e CLI da S02;
- `results/experiments_s02.json`: contrato principal G3/G4, 12 células;
- `results/experiments_s02.csv`: taxas e contagens em 24 linhas por teste;
- `results/experiments_s02_summary.md`: resultados e confronto com a teoria;
- `tests/test_experiments.py` e `tests/test_s02_contract.py`: 53 testes novos;
- documentação e manifesto de preservação em `docs/`.

As 24 taxas são confrontadas com probabilidades binomiais teóricas. ICs Wilson
e erros-padrão descrevem a incerteza Monte Carlo. Os limiares de rejeição são
K≥16 nos dois testes em n=200; em n=42, K≥5 no Z e K≥6 no exato. As diferenças
de poder devem ser lidas junto às diferenças de erro tipo I.

```bash
python -m pytest -q
```

Em caso de restrição ao Temp do Windows, usar o diretório local descartável
descrito na seção de validação. A entrega estatística da #34 ampliou a suíte
de 76 para 129 testes; a integração visual da #35 acrescenta mais quatro.

- [Metodologia S02 e limitações](docs/metodologia_s02.md)
- [Contrato S02 v1 para G3/G4](docs/contrato_integracao_s02.md)
- [Handoff S02 para Flávio](docs/handoff_flavio_s02.md)
- [Relatório de validação e checklist #34](docs/validacao_s02.md)

## Dashboard final e análise real (Issue #35)

G3 mostra as taxas de erro tipo I sob H₀: em n=200, Z e exato rejeitaram
4,19% das amostras; em n=42, Z rejeitou 5,77% e exato 1,95%, frente ao nível
nominal de 5%. G4 mostra quatro séries por teste e situação. No efeito de
+5 p.p. (`p=10%`), as rejeições foram 85,58% para ambos em n=200, e 41,02%
para Z contra 23,74% para o exato em n=42. O ponto de efeito zero é Q1;
as barras de erro de G3 representam incerteza Monte Carlo, não dos dados reais.

A seção de dados reais lê novamente o CSV validado: quatro falhas em 42
execuções, p̂=9,52% e efeito observado de +4,52 p.p. O Z resulta em
p=0,089283 e o exato em p=0,156893; nenhum rejeita H₀ a 5%. Essa conclusão
não demonstra que a taxa cumpre a meta. O binomial exato é recomendado para
falhas raras e amostra pequena se controlar o erro tipo I é prioritário,
reconhecendo seu conservadorismo e menor poder. A amostra temporal e a possível
dependência entre execuções limitam inferências sobre todo o projeto fonte.

O [roteiro oral](docs/apresentacao_final.md) resume a apresentação de até
7 minutos e os pontos que cada integrante precisa saber explicar. O dashboard
é a entrega visual principal; estas notas são apoio interno.
