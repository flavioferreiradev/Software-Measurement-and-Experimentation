# Relatório de validação — Lab04S02 / Issue #34

Validação inicial: 10/11/2026. Responsável: LuidiC. Base: main
`19308d8f905c50a05b962f0fdb56b842001bbd8a`.
Branch: `codex/lab04s02-luidi-34`. A árvore inicial estava limpa.
A primeira etapa ocorreu apenas localmente, sem commits novos, push, PR,
merge ou atualização da Issue #34/Project. Esse registro é histórico.
Após aprovação da auditoria externa, Luidi autorizou a publicação e integração
da sua contribuição. As evidências locais abaixo são mantidas; a seção
"Publicação e rastreabilidade" registra a entrega correspondente no GitHub.

## Implementação e arquivos

A implementação acrescenta execução offline de Q1, Q2 e Q3, vetorizada por
contagens binomiais suficientes, com fluxos reproduzíveis por n/p e aplicação
pareada dos dois testes. A S01 mantém os mesmos dados, código, testes, G1/G2 e
contrato. Nenhum arquivo de outro laboratório foi alterado.

| Arquivo relativo a Laboratorio4 | Alteração |
|---|---|
| `README.md` | Editado para acrescentar comandos, limites e links da S02 |
| `src/experiments.py` | Novo: protocolo, RNG, testes vetorizados, teoria e incerteza MC |
| `src/run_experiments.py` | Novo: CLI offline e exportações JSON/CSV/Markdown |
| `results/experiments_s02.json` | Novo: 12 células, metadados e contrato G3/G4 |
| `results/experiments_s02.csv` | Novo: 24 linhas por célula/teste |
| `results/experiments_s02_summary.md` | Novo: resultados efetivamente executados |
| `tests/test_experiments.py` | Novo: equivalência com S01, fronteiras, RNG e teoria |
| `tests/test_s02_contract.py` | Novo: estrutura, taxas, CLI, reprodução e preservação |
| `docs/metodologia_s02.md` | Novo: protocolo e limites científicos |
| `docs/contrato_integracao_s02.md` | Novo: contrato v1, unidades e leitura mínima |
| `docs/handoff_flavio_s02.md` | Novo: arquivos, comandos e fronteira de responsabilidade |
| `docs/s02_preservacao_s01.json` | Novo: hashes de 30 arquivos S01 preservados |
| `docs/validacao_s02.md` | Novo: este relatório, evidências e checklist |

São 12 arquivos novos e um preexistente modificado. Dependências, workflow CI,
dashboard e contratos/resultados S01 não foram modificados. As dependências
visuais já declaradas foram instaladas apenas na `.venv` local para executar
os testes preexistentes; não foram acrescentadas dependências ao requirements.

## Execuções e resultados

Ambiente: Windows, Python 3.13.3, NumPy 2.4.2, SciPy 1.17.1, pytest 8.4.2,
Streamlit 1.52.2 e Plotly 6.5.0. Dentro de `Laboratorio4/`, ambiente ativo:

```bash
python -m src.run_experiments
```

Seed raiz=42, 10.000 repetições por célula, 12 células e 120.000 amostras.
Ambos os testes são executados sobre o mesmo vetor de contagens em cada célula.

### Q1 — erro tipo I

| n | Teste | Rejeições/10000 | Taxa MC | Probabilidade teórica | IC MC 95% Wilson |
|---:|---|---:|---:|---:|---|
| 200 | Z | 419 | 0,0419 | 0,044355629 | [0,038146; 0,046006] |
| 200 | Exato | 419 | 0,0419 | 0,044355629 | [0,038146; 0,046006] |
| 42 | Z | 577 | 0,0577 | 0,057277894 | [0,053297; 0,062442] |
| 42 | Exato | 195 | 0,0195 | 0,017432006 | [0,016969; 0,022400] |

O confronto não assume que cada teste tem taxa teórica de exatamente 5%.
As quatro contagens nulas pertencem aos intervalos binomiais de aceitação
simultânea: [373,518], [373,518], [492,656] e [130,222], respectivamente.
O critério Bonferroni cobre todas as 24 estimativas com erro familiar ≤1%.
As 24/24 comparações ficaram compatíveis, incluindo as alternativas Q2.

### Q2 — frequência de rejeição por efeito

| p | Δ (proporção) | Z n=200 | Exato n=200 | Z n=42 | Exato n=42 |
|---:|---:|---:|---:|---:|---:|
| 0,05 | 0 | 0,0419 | 0,0419 | 0,0577 | 0,0195 |
| 0,075 | 0,025 | 0,4289 | 0,4289 | 0,2110 | 0,0940 |
| 0,10 | 0,05 | 0,8558 | 0,8558 | 0,4102 | 0,2374 |
| 0,125 | 0,075 | 0,9837 | 0,9837 | 0,6200 | 0,4369 |
| 0,15 | 0,10 | 0,9990 | 0,9990 | 0,7719 | 0,6118 |
| 0,20 | 0,15 | 1,0000 | 1,0000 | 0,9416 | 0,8719 |

A linha Δ=0 é erro tipo I reutilizado de Q1; demais linhas são poder.
As contagens inteiras, probabilidades teóricas, ICs e erros-padrão de todas as
linhas constam dos artefatos. Taxa observada 1,0000 não comprova poder exatamente
1; por exemplo, a probabilidade teórica de rejeição em n=200,p=0,20 é
aproximadamente 0,999999178 e o IC Wilson tem limite inferior menor que 1.

### Q3 — mudança de tamanho amostral

Em n=200 os testes compartilham K≥16, explicando decisões e taxas iguais nas
mesmas amostras. Os p-valores não precisam coincidir. Em n=42, o Z usa K≥5 e
o exato K≥6; há mais rejeições do Z sob H₀ e sob alternativas. A maior taxa
de detecção deve ser lida junto ao excesso de erro tipo I do Z.

n=42 tem n·p₀=2,1, portanto não é uma situação de boa aproximação normal.
n=200 tem n·p₀=10, no limite da regra prática. Q3 não altera a independência
ou a distribuição Bernoulli: ela estuda a insuficiência da aproximação em n
pequeno, conforme a Issue. O exato conserva o nível, mas é bastante conservador.

## Validações estatísticas e automatizadas

- Confronto da implementação vetorizada com `test_proportion` para todas as
  contagens de n=42 e n=200, além de n=30 e n=1 com outros p₀/α.
- Conferência dos dois lados dos limiares de rejeição e de igualdade p-valor=α.
- Cauda normal conferida com `math.erfc`; probabilidades de rejeição conferidas
  por soma independente de `math.comb` e pela lei binomial do SciPy.
- Validação de n, p, seed, repetições, amostras de contagem e parâmetros dos testes.
- Verificação de contagens zero/todas, região crítica vazia e proteção contra
  underflow de `K-1` em arrays unsigned.
- Fluxos estáveis perante reordenação de cenários, parâmetros/seed diferentes
  e mesma semente; ambas as decisões usam exatamente as mesmas contagens.
- Estrutura JSON, valores finitos, taxas em [0,1], contagens, histogramas,
  decisões conjuntas, valores teóricos e ICs coerentes.
- Uma linha nula por situação compartilhada por Q1/Q2/Q3 e pelos seletores G3/G4.
- CLI integral repetida em subprocessos; três exportações idênticas byte a byte.
- Execução sem token e com acesso à rede bloqueado no teste.
- Preservação automatizada dos cinco artefatos de dados/resultados S01.
  A auditoria adicional verifica os 30 arquivos preexistentes, inclusive o
  dashboard, sem impedir sua expansão futura pelo Flávio.

| Execução | Resultado |
|---|---|
| `python -m pytest tests/test_experiments.py tests/test_s02_contract.py -q --basetemp=.pytest-tmp/s02-first` | 53 passaram, zero falhas, 7,17 s |
| `python -m pytest -q --basetemp=.pytest-tmp/s02-full` | 129 passaram, zero falhas, 11,33 s; aviso de limpeza temporária do Streamlit no sandbox |
| `python -m pytest -q --basetemp=.pytest-tmp/s02-native` | **129 passaram, zero falhas/erros, 9,30 s**, execução local fora do sandbox, sem aviso de limpeza |
| `python -m pytest tests/test_s02_contract.py -q --basetemp=.pytest-tmp/s02-contract-final` | 10 passaram, zero falhas, 6,30 s; contrato final e proteção dos cinco artefatos S01 |
| `python -m pytest -q --basetemp=.pytest-tmp/s02-publicacao` | **129 passaram, zero falhas/erros, 8,47 s**, revalidação anterior à publicação autorizada |

O teste completo inclui os 76 testes anteriores, inclusive a execução offline
do dashboard S01, e os 53 novos. Não foram criados testes de gráficos G3/G4
porque esses gráficos não pertencem à tarefa de Luidi.
O `--basetemp` resolve a restrição do Temp deste Windows sem modificar
pytest.ini ou os testes antigos. Esse diretório é exclusivo de testes e
descartável: pytest pode limpá-lo. O comando padrão em um ambiente sem essa
restrição continua sendo `python -m pytest -q`.

## Reprodução e evidência de auditoria

O comando **padrão** `python -m src.run_experiments` também foi executado
consecutivamente duas vezes no diretório oficial. Os três arquivos resultantes
foram idênticos byte a byte, e os 30 arquivos preservados da S01 continuaram
com os mesmos hashes.

| Arquivo | SHA256 nas duas execuções |
|---|---|
| experiments_s02.json | `695bbbdb262572ab3ef520800f523aaf47ce63347823da4ead205b4492fcc7c3` |
| experiments_s02.csv | `3e046fd85c2ceb75da1881aca4d1d5b3f7316573c821dcee8511680cf035b863` |
| experiments_s02_summary.md | `56bd3a9bd4138f7ac9540fabf19416c309e619696a5843e90247461a05761b2e` |

Evidências locais adicionais em `.pytest-tmp/auditoria-s02/` (ignoradas pelo
Git): `reproducao.json`, `changes.patch` e `manifesto_diff.json`. O patch inclui
os arquivos novos, que não aparecem em um `git diff` comum enquanto não forem
adicionados ao índice. Na etapa inicial, nenhum arquivo foi adicionado ao índice.
Esse patch histórico antecede a revisão documental para publicação; o diff
definitivo é o do PR associado à #34.

Comandos para revisão no próprio checkout:

```bash
git status --short
git diff -- Laboratorio4/README.md
git diff --check
```

Para cada arquivo novo, `git diff --no-index -- /dev/null CAMINHO` gera o diff
de adição (no Windows, `NUL` é o equivalente). O patch salvo reúne essas adições
e a edição do README. A auditoria final também verifica que não há alterações
nos Labs 01–03, no dashboard ou em arquivos rastreados da S01 além do README.

## Problemas e limites

O único problema de execução observado foi a permissão de limpeza do Temp
virtualizado pelo sandbox. A execução nativa com temporário local passou sem
esse aviso. Não há falha estatística ou de integração pendente identificada.
Na validação inicial não foi executada CI remota, conforme a restrição daquela
etapa. A publicação autorizada utiliza o GitHub Actions do PR antes do merge.

O experimento limita-se às duas situações/seis valores definidos na Issue e
ao modelo binomial iid. Incerteza Monte Carlo, discretização e a diferença de
calibração entre testes estão explicitadas. A inferência dos dados reais,
G3/G4, as seções finais e a conclusão geral permanecem com Flávio.

## Checklist da Issue #34

- [x] Partir da main atualizada e preservar dados/artefatos da S01.
- [x] Q1: 10.000 amostras por situação sob p=p₀.
- [x] Q2: os seis valores de p, Δ correto e ponto nulo reutilizado.
- [x] Q3: n=200 versus n=42, com inadequação da aproximação claramente identificada.
- [x] Fluxos reproduzíveis por situação/p e mesmas repetições para ambos os testes.
- [x] Otimização por contagens conferida com a função S01, inclusive fronteiras.
- [x] Comando único offline de reprodução integral.
- [x] JSON com versão, parâmetros, situações, 12 linhas e contagens/taxas dos dois testes.
- [x] Contrato G3/G4, unidades e exemplo mínimo de leitura documentados.
- [x] Contrato G1/G2 e resultados S01 mantidos.
- [x] Testes úteis de estrutura, finitude, taxas, contagens e consistência Q1/Q2.
- [x] Taxas comparadas à teoria binomial, com erro Monte Carlo considerado.
- [x] Suíte completa local aprovada; comando, artefatos e limites registrados.
- [x] Handoff preparado, sem implementar atividades do Flávio.
- [ ] Commits e PR vinculados à #34: acompanhar em "Publicação e rastreabilidade".
- [ ] Publicar o contrato e o handoff pelo PR, para consumo na #35.

Os dois últimos itens foram adiados na etapa inicial e agora fazem parte do
fluxo de publicação autorizado. Não alteram a implementação estatística auditada.

## Publicação e rastreabilidade

A auditoria externa foi aprovada e a publicação da #34 autorizada por Luidi.
A entrega utiliza a branch `codex/lab04s02-luidi-34`, com commits vinculados à
Issue. O PR registra os resultados da CI e o commit de integração; a
[Issue #34](https://github.com/flavioferreiradev/Software-Measurement-and-Experimentation/issues/34)
e o [Kanban #3](https://github.com/users/flavioferreiradev/projects/3) registram
o status efetivo. A Issue #35 do Flávio permanece independente e não é alterada.

O JSON definitivo é `Laboratorio4/results/experiments_s02.json`; o contrato é
`Laboratorio4/docs/contrato_integracao_s02.md`; os comandos e responsabilidades
do Flávio estão em `Laboratorio4/docs/handoff_flavio_s02.md`.

Na revalidação de publicação, `python -m src.run_experiments` reproduziu os
três hashes registrados acima. Os sete arquivos aprovados de código, testes
e resultados S02 permaneceram idênticos à auditoria, assim como os 30 arquivos
preservados da S01. As mudanças posteriores à aprovação são documentais.
