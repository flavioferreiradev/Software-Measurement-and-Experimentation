# Resultados executados — Lab04S02 / #34

Seed=42; 10000 repetições por (n,p).
Δ=p−p₀ em proporção; p₀=0,05; α=0,05; rejeição estrita p-valor<α.

| Situação | p | Δ | Tipo | Rejeições Z | Taxa Z | Rejeições exato | Taxa exato |
|---|---:|---:|---|---:|---:|---:|---:|
| reference_n200 | 0.05 | 0 | type_i_error | 419 | 0.0419 | 419 | 0.0419 |
| reference_n200 | 0.075 | 0.025 | power | 4289 | 0.4289 | 4289 | 0.4289 |
| reference_n200 | 0.1 | 0.05 | power | 8558 | 0.8558 | 8558 | 0.8558 |
| reference_n200 | 0.125 | 0.075 | power | 9837 | 0.9837 | 9837 | 0.9837 |
| reference_n200 | 0.15 | 0.1 | power | 9990 | 0.9990 | 9990 | 0.9990 |
| reference_n200 | 0.2 | 0.15 | power | 10000 | 1.0000 | 10000 | 1.0000 |
| small_n42 | 0.05 | 0 | type_i_error | 577 | 0.0577 | 195 | 0.0195 |
| small_n42 | 0.075 | 0.025 | power | 2110 | 0.2110 | 940 | 0.0940 |
| small_n42 | 0.1 | 0.05 | power | 4102 | 0.4102 | 2374 | 0.2374 |
| small_n42 | 0.125 | 0.075 | power | 6200 | 0.6200 | 4369 | 0.4369 |
| small_n42 | 0.15 | 0.1 | power | 7719 | 0.7719 | 6118 | 0.6118 |
| small_n42 | 0.2 | 0.15 | power | 9416 | 0.9416 | 8719 | 0.8719 |

## Q1: confronto com a teoria

| n | Teste | Taxa simulada | Probabilidade teórica | IC MC 95% (Wilson) | Compatível MC* |
|---:|---|---:|---:|---|---|
| 200 | z | 0.0419 | 0.044355629 | [0.038146, 0.046006] | True |
| 200 | binomial_exact | 0.0419 | 0.044355629 | [0.038146, 0.046006] | True |
| 42 | z | 0.0577 | 0.057277894 | [0.053297, 0.062442] | True |
| 42 | binomial_exact | 0.0195 | 0.017432006 | [0.016969, 0.022400] | True |

*Confronto por intervalos binomiais exatos de contagem, com Bonferroni para 24 estimativas e erro familiar máximo de 1%: 24/24 compatíveis.

As diferenças pequenas podem ser ruído Monte Carlo; a probabilidade teórica usa a região de rejeição real de cada teste.
n=42 tem n·p₀=2,1 e aproximação normal inadequada pela regra prática. n=200 tem n·p₀=10, no limite da regra.
A Q3 compara essas duas situações; em ambas o modelo gerador continua binomial iid.
O binomial exato pode ser conservador pela discretização. Comparar poder exige considerar o erro tipo I realizado.
G3/G4, inferência dos dados reais e conclusão geral pertencem ao Flávio.
