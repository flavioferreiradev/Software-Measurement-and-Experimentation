# Cenário P4 e metodologia da S01

## Pergunta e hipóteses

Uma equipe acompanha execuções de integração contínua para detectar degradação
da qualidade. Pergunta: **a proporção de execuções de CI com falha supera a meta
de 5%?** A meta é uma referência pedagógica; não é uma política declarada
pelo pytest.

- H₀: p ≤ p₀=0,05.
- H₁: p > p₀=0,05.
- α=0,05; teste unilateral à direita, pois interessa o excesso de falhas.
- Regra: rejeitar H₀ quando p-valor **<** α, conforme o enunciado.

As caudas são calculadas na fronteira p=p₀: a probabilidade de uma contagem
alta cresce com p, portanto essa fronteira é a referência menos favorável
para o nulo composto. A população de interesse é a rotina de CI no recorte
definido, não todos os projetos open-source.

## Observação real, fonte e critérios

Unidade: um `run.id` concluído do workflow `test`, id **22158026**, caminho
`.github/workflows/test.yml`, de `pytest-dev/pytest`, evento `push`, branch
`main`. A variável binária `failed` vale 0 para `success` e 1 para `failure`
ou `timed_out`. Timeout é falha operacional em cumprir a validação, mesmo sem
provar defeito no código.

Execuções `cancelled`, `skipped`, `neutral`, `action_required`, `stale` e outras
conclusões não determinantes são excluídas: não indicam de forma comparável o
resultado da validação concluída. Excluí-las pode introduzir viés; a amostra
estima a taxa **condicional às conclusões incluídas**, e não a taxa de todas
as tentativas iniciadas. Há quatro canceladas e nenhum timeout neste snapshot.

Recorte inclusivo de **criação** em UTC:
`2026-10-01T00:00:00Z .. 2026-11-04T18:00:00Z`. A coleta ocorreu em
04/11/2026 às 18:47:46 UTC (15:47:46 em São Paulo). Os IDs e URLs são as
referências primárias; `updated_at` não é tratado como término/duração.

Procedimento: consultar o endpoint de runs do workflow, com branch/evento/status
e janela fixos; paginar em lotes de 100; validar defensivamente os filtros;
deduplicar por `run.id`; classificar; ordenar `(created_at,id)` decrescente e
usar as últimas 60 válidas, ou todas quando existirem 30–59. O conjunto
recebido teve 46 runs; quatro canceladas foram auditadas e excluídas;
**42 válidas** foram usadas, sem escolher individualmente pela conclusão.
O período observado vai de 04/10/2026 05:01:13 UTC a 04/11/2026 08:34:45 UTC.

Uma execução reexecutada conta uma vez, na tentativa mais recente que a API
retornou na coleta. A história de tentativas anteriores não é usada. Por isso
nova coleta pode divergir mesmo na mesma janela; o CSV e a auditoria
versionados, com SHA256, definem a amostra congelada. O coletor não precisa
de token para a API pública e não persiste credenciais.

## Parâmetros empíricos e gerador

Há 38 sucessos e quatro falhas: n=42, k=4, p̂=4/42=0,09523809523809523.
Média da variável = p̂; variância do modelo Bernoulli ajustado =
p̂(1−p̂)=0,08616780045351473. A variância amostral com divisor n−1 também
é exportada na função de resumo; não é o erro-padrão usado pelo teste Z.

O gerador usa `numpy.random.default_rng(42).binomial(1,p,size=n)`, com n=42
e p=p̂ empírico. Cada Xᵢ segue Bernoulli(p), sob a simplificação de execuções
independentes e probabilidade constante; K=ΣXᵢ segue Binomial(n,p).
O p do gerador reproduz a frequência empírica; **p₀=0,05 é a meta fixa**.
O parâmetro populacional verdadeiro não é conhecido por observar p̂.

Foi preservada a primeira amostra simulada com essa semente, sem busca por
significância. Ela teve k=4 e n=42; a sequência difere da real, embora a
contagem coincida. Os resultados estão em `results/demo_interpretation.md`.
Não se aplicam ainda os testes ao CSV real como análise final, nem se executam
experimentos de erro tipo I, poder ou violação de pressupostos da S02.

## Testes e interpretação

Z: p̂=K/n, SE₀=√(p₀(1−p₀)/n), Z=(p̂−p₀)/SE₀,
p-valor=Pr[N(0,1)≥Z], calculado por `scipy.stats.norm.sf`.
Sem correção de continuidade. n·p₀=2,1 e n·(1−p₀)=39,9;
a regra prática de pelo menos 10 em ambas as contagens não é atendida.
O teste é implementado para comparação, mas a cauda normal pode aproximar
mal a distribuição discreta real de Z nessa situação.

Exato: `scipy.stats.binomtest(k,n,p=0.05,alternative="greater")`;
p-valor=Σ de j=K a n de C(n,j)p₀ʲ(1−p₀)ⁿ⁻ʲ, sem aproximação normal.
A estatística retornada pelo SciPy é p̂; o G2 pode usar a contagem equivalente
K, que também é exportada. Ambos dependem do modelo binomial iid; o exato
não remove vieses da coleta nem dependência temporal. É uma comparação de
aproximação versus cálculo exato dentro do modelo binomial, não de um teste
paramétrico com outro livre de pressupostos.

No exemplo, Z=1,345185418 (p=0,089282682) e binomial p=0,156892615:
ambos não rejeitam H₀. Isso não confirma que p≤5% e não mede o desempenho
relativo dos testes. O p-valor é uma cauda sob o modelo nulo, não a
probabilidade de H₀ ser verdadeira.

A previsão anterior à simulação está em `previsao_inicial.md` e no commit
`b70549b`. Sua avaliação científica permanece para S02.

## Limitações

Amostra temporal por conveniência de um workflow, pequena e não aleatória.
Commits relacionados podem criar autocorrelação; versões do workflow,
dependências, indisponibilidade de rede e infraestrutura podem alterar p.
Reruns e exclusão de canceladas podem ocultar problemas. Falha de CI não
equivale necessariamente a defeito do produto. A taxa empírica tem incerteza;
não generalizar para outros workflows/projetos. Bernoulli iid é uma
simplificação deliberada, não um pressuposto empiricamente demonstrado.

## Referências verificáveis

- [Workflow fonte](https://github.com/pytest-dev/pytest/actions/workflows/test.yml).
- [GitHub REST: listar runs de workflow](https://docs.github.com/en/rest/actions/workflow-runs#list-workflow-runs-for-a-workflow).
- [SciPy binomtest](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.binomtest.html).
- [SciPy distribuição normal](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.norm.html).
- [NumPy Generator.binomial](https://numpy.org/doc/stable/reference/random/generated/numpy.random.Generator.binomial.html).
