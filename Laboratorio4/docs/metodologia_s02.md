# Lab04S02 — protocolo executado da Issue #34

Esta entrega implementa somente os experimentos e o contrato estatístico de
LuidiC. A primeira etapa foi validada exclusivamente no ambiente local, sem
publicação. Após aprovação da auditoria externa, Luidi autorizou a publicação
vinculada à Issue #34. O protocolo, a implementação estatística e os resultados
aprovados são preservados integralmente nesse processo.

## Base e preservação

Main consultada em 10/11/2026, commit
`19308d8f905c50a05b962f0fdb56b842001bbd8a` (inclui o dashboard G1/G2 do Flávio).
Branch de implementação e publicação: `codex/lab04s02-luidi-34`.
O manifesto `s02_preservacao_s01.json` registra os SHA256 de 30 arquivos
preexistentes do Lab04, incluindo dados, resultados, código, testes e dashboard.
A única edição de arquivo preexistente é a adição de instruções S02 ao README.
Não há nova coleta nem acesso aos datasets dos Labs 01–03.

## Perguntas e parâmetros fixados

P4: Z para proporção sem correção de continuidade × binomial exato, alternativa
à direita. H₀: p≤0,05; H₁: p>0,05; p₀=0,05; α=0,05;
rejeição somente com **p-valor < α**, preservando a regra da S01.

| Pergunta | Execução |
|---|---|
| Q1 | 10.000 amostras iid sob p=p₀ por situação; estimar erro tipo I |
| Q2 | 10.000 por situação e p∈{0,05; 0,075; 0,10; 0,125; 0,15; 0,20}; estimar rejeições |
| Q3 | Repetir Q1/Q2 nas situações n=200 e n=42 e comparar a aproximação |

Δ=p−p₀ em **proporção**: {0; 0,025; 0,05; 0,075; 0,10; 0,15}.
O ponto Δ=0 de Q2 é a própria linha Q1, sem executar outro conjunto ou contar
duas vezes suas repetições. É erro tipo I, não poder sob uma alternativa.
São 12 células, **120.000 amostras independentes** e 240.000 decisões
(dois testes por amostra).

| Situação | n | n·p₀ | n·(1−p₀) | Interpretação |
|---|---:|---:|---:|---|
| reference_n200 | 200 | 10 | 190 | Referência no limite da regra prática de 10 |
| small_n42 | 42 | 2,1 | 39,9 | Aproximação normal questionável; tamanho do CSV real |

A Q3 modifica o tamanho amostral e a qualidade da aproximação normal; não
introduz correlação, outliers, sobredispersão nem mudança da lei Bernoulli.
O modelo binomial iid continua válido nas duas situações. Não apresentar
n=42 como situação de pressupostos bem atendidos, nem a regra de 10 como
garantia de exatidão da aproximação em n=200.

## Gerador e equivalência da otimização

Gerar diretamente K~Binomial(n,p), que tem a mesma distribuição da soma de
n variáveis Bernoulli(p) independentes. Os dois testes da S01 dependem apenas
de (n,K,p₀,α); portanto não é necessário materializar 120.000 vetores binários.
Isso preserva a distribuição do experimento. A sequência sorteada não precisa
ser idêntica à de chamadas sucessivas ao gerador Bernoulli da S01.

Para cada vetor K, calcular p̂=K/n, Z=(p̂−p₀)/√[p₀(1−p₀)/n],
pZ=norm.sf(Z) e pExato=binom.sf(K−1,n,p₀). A cauda exata inclui K observado.
O mesmo vetor de 10.000 contagens é usado nos dois testes. Vetorização não
aplica aproximação ao teste binomial. Os testes automatizados confrontam
**todas** as contagens possíveis de n=42 e n=200 com `test_proportion` da
S01, além de outros parâmetros e igualdade p-valor=α.

## Semente e fluxos

Seed raiz=42. Cada célula usa:

```python
fraction = Fraction(str(float(p)))
entropy = [42, n, fraction.numerator, fraction.denominator]
rng = numpy.random.default_rng(numpy.random.SeedSequence(entropy))
counts = rng.binomial(n, p, size=10000)
```

O gerador utilizado é PCG64 (registrado no JSON). Exemplo: n=200, p=0,075
usa `[42,200,3,40]`; n=42, p=0,05 usa `[42,42,1,20]`. As identidades derivam
dos parâmetros, sem `hash()` aleatório do Python ou dependência da ordem dos
laços. SeedSequence separa os fluxos com probabilidade de colisão desprezível;
não representa prova matemática de independência de um PRNG.

Cada linha registra a entropia, o histograma de K e SHA256 da sequência
ordenada codificada em inteiros unsigned de 32 bits little-endian. Isso permite
regenerar e conferir todas as repetições sem versionar arquivos volumosos.
O histograma e as contagens conjuntas de decisões permitem auditar as taxas
dos dois testes e seu pareamento. Fixar as versões NumPy/SciPy do requirements
para reprodução; diferenças no último bit de floats entre plataformas são
aceitas pelos testes com tolerância documentada.

## Confronto teórico e erro Monte Carlo

Enumerar K=0..n e identificar o menor K com p-valor<α em cada teste. As
regiões são caudas superiores; sua probabilidade sob o p gerador é calculada
pela **lei binomial exata**, inclusive para avaliar o teste Z aproximado.
Não se deve usar automaticamente 0,05 como a taxa teórica de nenhum teste.

- n=200: ambos rejeitam com K≥16; probabilidade sob H₀≈0,044355629.
- n=42: Z rejeita com K≥5, probabilidade≈0,057277894; exato com K≥6,
  probabilidade≈0,017432006.

Para cada uma das 24 estimativas (12 células × 2 testes), exportar:
taxa r/R; erro-padrão Monte Carlo estimado √[r/R·(1−r/R)/R]; IC95% Wilson
pontual; probabilidade teórica q; erro-padrão teórico √[q(1−q)/R]; diferença
simulação−teoria e intervalo de aceitação da contagem r~Binomial(R,q).

O confronto usa quantis exatos com caudas 0,01/(2·24) e Bonferroni: o risco
familiar de uma discrepância falsa nas 24 comparações é no máximo 1% sob os
geradores corretos. O critério foi codificado antes de confrontar os resultados;
seed e intervalos não foram ajustados para obter aprovação. Esse limite não
exige independência entre os resultados dos dois testes pareados.

Os IC95% Wilson são pontuais e descrevem **incerteza Monte Carlo**, não a
incerteza da taxa de falhas real de CI. Não exigir monotonicidade estrita das
taxas simuladas nem interpretar diferenças pequenas como evidência definitiva.
Se houver 10.000 rejeições, a taxa observada é 1, mas o IC Wilson continua
com limite inferior menor que 1; não afirmar poder populacional garantido.

## Resultados e limites da interpretação

As contagens e taxas efetivamente executadas estão em
`../results/experiments_s02_summary.md`, com todas as células em JSON/CSV.
Todas as 24 estimativas ficaram compatíveis com as probabilidades teóricas
pelo critério acima.

Em n=200, as taxas de rejeição coincidem em todas as linhas porque as regiões
críticas são iguais neste protocolo; os p-valores não são iguais em geral.
Em n=42, o Z tem maior frequência de rejeição e também erro tipo I acima do
nominal; o exato é conservador devido à discretização. A maior taxa do Z sob
alternativas não deve ser tratada como superioridade global sem considerar
essa diferença de calibração. A previsão da S01 é sustentada quanto à maior
proteção do nível pelo teste exato em n pequeno, mas ele fica bem abaixo de
5% e perde detecção; não se conclui que é sempre melhor ou mais próximo de 5%.

São duas situações, seis valores de p, um α e 10.000 repetições cada. O estudo
não avalia dependência temporal ou viés da coleta. Os dados reais fornecem
somente o tamanho n=42; sua inferência e a conclusão geral do dashboard são
responsabilidade do Flávio. Nenhum gráfico G3/G4 foi implementado aqui.

## Referências

- [Issue #34 e protocolo do grupo](https://github.com/flavioferreiradev/Software-Measurement-and-Experimentation/issues/34).
- [NumPy 2.4: SeedSequence e fluxos reproduzíveis](https://numpy.org/doc/2.4/reference/random/parallel.html).
- [SciPy: binomtest](https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.stats.binomtest.html).
- [SciPy: distribuição binomial e função de sobrevivência](https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.stats.binom.html).
