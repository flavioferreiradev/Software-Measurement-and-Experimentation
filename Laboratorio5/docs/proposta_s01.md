# Lab05S01 — proposta do experimento com SQLite

**Responsável na S01:** Flávio · **Issue:** [#38](https://github.com/flavioferreiradev/Software-Measurement-and-Experimentation/issues/38) · **Estado:** proposta e piloto executados em 18/11/2026.

## 1. Software escolhido e aderência ao enunciado

O objeto de pesquisa é o **mecanismo SQLite executando operações SQL**, não o
repositório de seu código-fonte. O enunciado aceita software aberto rodado no
ambiente do grupo quando ele também é usado em produção.

| Critério | Evidência pública (acesso em 18/11/2026) |
|---|---|
| Real | O [site oficial](https://www.sqlite.org/) descreve SQLite como um mecanismo SQL autocontido, com documentação e downloads. |
| Em operação | O projeto lista usos em [aplicações e organizações conhecidas](https://www.sqlite.org/famous.html), como Adobe Lightroom, Firefox e aplicações da Apple. O [release 3.54.1](https://www.sqlite.org/releaselog/current.html) foi publicado em 16/10/2026. |
| Alto impacto | O projeto relata [bilhões de cópias implantadas](https://www.sqlite.org/mostdeployed.html) em celulares, computadores e aplicações. A estimativa de mais de um trilhão de bases ativas nessa página é uma estimativa do próprio projeto, não uma contagem auditada; não a usamos para extrapolar nossos resultados. |

No piloto, o `sqlite3` incluído no Python local usa SQLite **3.53.4**. A
[cronologia oficial](https://www.sqlite.org/chronology.html) mostra manutenção
da linha 3.53 com o patch 3.53.6 de 13/11/2026. A versão exata e a plataforma
estão em `results/pilot_s01/metadata.json`. Antes da coleta completa, a equipe
deve fixar uma versão para todas as medições e repetir o piloto caso a atualize.

**Critério externo a confirmar:** nenhum outro grupo da turma pode escolher o
mesmo software, conforme o enunciado. A escolha definitiva depende dessa
verificação com a turma/professor.

## 2. Pergunta e objetivo GQM

**Pergunta de pesquisa:** em uma carga transacional definida, um índice
composto `(customer_id, created_at DESC)` no SQLite reduz o tempo de consultas
recentes por cliente? Quanto ele custa em inserções e armazenamento?

**Objetivo GQM (template de Basili):** analisar o SQLite, com o propósito de
comparar o efeito operacional de um índice composto, com respeito à latência
de leitura, custo de inserção e espaço em disco, do ponto de vista de quem
mantém uma aplicação, no contexto de um banco local com pedidos sintéticos e
mesma carga executada nas duas configurações.

| Pergunta GQM | Métricas |
|---|---|
| O índice melhora a busca dos pedidos recentes de um cliente? | Mediana e p95 de tempo por consulta em ms; diferença e razão entre condições; plano de execução. |
| Qual é o custo nas escritas? | Tempo por linha em lote de inserção; diferença e razão entre condições. |
| Qual é o custo em armazenamento? | Bytes finais dos arquivos de banco; diferença absoluta e percentual. |

As durações e os bytes são medidas de escala de razão. Medianas, percentis,
diferenças e razões têm interpretação apropriada para essas escalas. O plano
de consulta é uma observação categórica usada para validar a manipulação.

## 3. Desenho experimental e coleta

- **Unidade experimental para análise:** um par novo de bancos gerados com a
  mesma semente de uma repetição independente. Consultas dentro de um par são
  submedições e não serão tratadas como réplicas independentes em testes.
- **Tratamentos:** A, tabela sem índice secundário; B, mesma tabela e linhas
  com índice composto em `(customer_id, created_at DESC)`. A chave primária é
  idêntica nas duas condições.
- **Carga:** consulta parametrizada `WHERE customer_id = ? ORDER BY created_at
  DESC LIMIT 20`, seguida de inserções em lote. Os clientes consultados e os
  registros inseridos são idênticos dentro de cada par.
- **Dados:** pedidos sintéticos de cinco campos; IDs de cliente uniformes,
  datas crescentes, valores monetários fictícios e status categórico. Semente
  fixa. Nenhum dado pessoal ou requisição a serviço de terceiros.
- **Controle:** mesma máquina, versão, esquema, dados, SQL e PRAGMAs
  (`journal_mode=DELETE`, `synchronous=FULL`, `cache_size=-2000`). A ordem A/B
  alterna por bloco e repetição; há aquecimento antes das medições. O script
  verifica igualdade das respostas e `EXPLAIN QUERY PLAN` em cada par.
- **Piloto S01:** 3 pares independentes de 20 mil linhas, 1.000 clientes,
  30 consultas por bloco, 2 blocos e 100 inserções por bloco. Resultados brutos
  e metadados versionados em `results/pilot_s01/`.
- **Coleta completa prevista para S02:** 20 pares independentes de 50 mil
  linhas, 2.500 clientes, 50 consultas por bloco, 3 blocos e 500 inserções por
  bloco. O volume poderá ser ajustado antes da coleta completa se o piloto de
  escala mostrar duração excessiva ou efeito de piso de resolução do relógio;
  qualquer alteração será registrada antes da análise.

O gerador e a instrumentação estão em `src/run_pilot.py`. O comando único está
no README. As medições usam `time.perf_counter_ns` e incluem a execução SQL e
a materialização dos resultados em Python, igual nas duas condições. O tempo
de construção do índice é registrado separadamente; não faz parte da latência
das consultas.

## 4. Hipóteses e plano de análise

Para a pergunta principal, seja `Dᵣ` a mediana de leitura sem índice menos a
mediana com índice **dentro de cada par independente**. Planejamos
**H₀: mediana(Dᵣ) ≤ 0** e **H₁: mediana(Dᵣ) > 0**. A S02 reportará as diferenças por
par, uma estimativa de efeito em ms e em razão, intervalos de confiança e um
teste pareado apropriado para a distribuição observada, se justificável. O
piloto não é usado para declarar significância.

Para escrita e armazenamento, reportaremos efeitos absolutos e relativos com
intervalos por repetição. Também mostraremos mediana e p95 descritivos das
submedições, sem usar cada consulta como observação independente. Planos de
consulta e igualdade de resultados são critérios de validade da comparação.
Uma análise de sensibilidade poderá variar a proporção de leituras/escritas,
mas seu volume será declarado como **cenário**, não como tráfego real medido.

## 5. Sete categorias da pesquisa — classificação inicial

| Categoria | Classificação e justificativa |
|---|---|
| Natureza | **Aplicada:** a decisão sobre criar um índice é uma escolha prática de configuração de software. |
| Objetivo | **Explicativo e comparativo:** estimar como a presença do índice altera leituras e seus custos associados sob uma carga definida. |
| Abordagem | **Quantitativa:** durações, bytes, planos e efeitos numéricos. |
| Procedimento | **Experimento computacional local:** manipulamos a configuração do índice e mantemos o restante da carga igual. |
| Tempo | **Transversal com medições repetidas:** pares e blocos são executados em uma janela de estudo; não acompanhamos uma população ao longo de meses. |
| Controle | **Controlado com ruído de sistema:** fixamos versão, dados e SQL, mas agendamento do sistema, cache e hardware ainda podem influenciar tempos. |
| Nível de evidência | **Experimental para a carga e o ambiente medidos:** permite inferência causal local sobre a manipulação do índice se o controle funcionar; generalização para aplicações reais é limitada. |

Esta é uma classificação provisória a revisar à luz dos resultados e dos
termos usados na Aula 8.

## 6. Ética, validade e impacto até a entrega final

| Ameaça à validade | Mitigação planejada |
|---|---|
| Conclusão | Não usar as 180 consultas do piloto como 180 réplicas independentes; ampliar pares na S02, reportar efeito e incerteza. |
| Interna | Alternar a ordem A/B, aquecer ambos, registrar ambiente e controlar sementes; não executar outras cargas intencionais durante a coleta. |
| Construto | A consulta e os dados sintéticos representam apenas um padrão de uso; medir também o custo de escrita e de disco para evitar conclusão unilateral. |
| Externa | Uma máquina, versão e carga sintética não representam todos os dispositivos e aplicativos; apresentar cenários de volume sem afirmar ganho observado em produção. |

Não há participantes, dados pessoais nem tráfego dirigido a terceiros. Para
S03, o impacto pode ser expresso por um cenário explícito, por exemplo: tempo
economizado em `N` leituras menos o tempo adicional em `M` inserções, junto ao
custo em bytes. `N` e `M` deverão ser rotulados como hipóteses de volume se
não vierem de fonte pública. A ampla implantação do SQLite justifica a
relevância do tema, mas **não** multiplica o efeito local por bilhões de
dispositivos.

## 7. Entregas por sprint

- **S01:** evidências do software, pergunta, GQM, sete categorias iniciais,
  método, plano de análise, script e coleta piloto validada.
- **S02:** coleta completa com protocolo fechado, dados brutos versionados,
  estatísticas, tamanho do efeito e ameaças à validade revisadas.
- **S03:** implicações para usuários/empresas sob cenários fundamentados,
  categorias revisadas, conclusão, limitações e rascunho do documento e da
  apresentação.
- **Final:** documento e apresentação de até 10 minutos, no formato escolhido
  pelo grupo.
