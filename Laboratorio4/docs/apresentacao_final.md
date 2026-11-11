# Apoio para apresentação oral — Lab04

O dashboard é a entrega principal. Este roteiro serve para ensaiar **até 7 minutos**; os dois integrantes devem dominar o trabalho completo e responder pelo menos quatro perguntas cada na rodada do professor.

| Tempo sugerido | Quem | Fala apoiada no dashboard |
|---|---|---|
| 0:00–0:50 | Flávio | Pergunta: taxa de falhas do CI acima da meta pedagógica de 5%? Fonte, 42 execuções reais e H₀/H₁. |
| 0:50–1:45 | Luidi | Por que comparar Z aproximado e binomial exato; previsão registrada antes da simulação. |
| 1:45–2:35 | Flávio | G1/G2: dados reais versus exemplo simulado e como as caudas geram p-valores diferentes. |
| 2:35–3:40 | Luidi | Protocolo Q1–Q3: 10.000 repetições por célula, seis valores de p, n=200 versus n=42, mesma amostra para os dois testes. |
| 3:40–4:40 | Flávio | G3: em n=42, erro tipo I do Z=5,77% e do exato=1,95%; em n=200, ambos=4,19%. A linha de 5% é nominal. |
| 4:40–5:35 | Luidi | G4: em p=10%, poder 41,02% versus 23,74% em n=42; n=200 coincide em 85,58% porque os limiares críticos são iguais. |
| 5:35–6:20 | Flávio | CSV real: 4/42, p̂=9,52%, efeito +4,52 p.p.; p-valores Z=0,089283 e exato=0,156893, sem rejeição a 5%. |
| 6:20–7:00 | Ambos | Recomendação condicional: exato para amostra pequena/falha rara se controle do erro tipo I importa; mais dados ajudam no poder; dependência temporal exige rever o modelo. |

## Perguntas para ensaiar

**Luidi**

1. **Por que simular sob p=5%?** É a fronteira de H₀ e permite estimar a frequência de rejeição incorreta (erro tipo I) para este teste unilateral.
2. **Por que gerar K diretamente?** Para dados iid Bernoulli, a soma de n observações segue Binomial(n,p); os dois testes dependem de n e K. Cada célula tem fluxo aleatório reproduzível.
3. **O que Q3 viola?** Em n=42, n·p₀=2,1 fica abaixo da regra prática para a aproximação normal do Z. A simulação não viola independência nem altera a distribuição Bernoulli.
4. **Por que o exato tem erro tipo I abaixo de 5%?** K é discreto: o próximo limiar inteiro permitido para rejeição produz uma cauda sob H₀ de apenas cerca de 1,74% em n=42.

**Flávio**

1. **O Z é melhor por ter mais poder em n=42?** Não se pode comparar só a detecção; ele também supera 5% de erro tipo I nesse cenário. O exato controla o limite nominal, mas é conservador.
2. **Por que as curvas n=200 coincidem?** Neste protocolo ambos rejeitam para K≥16; as decisões são iguais nas amostras pareadas. Isso não significa p-valores iguais nem equivalência em outros n.
3. **9,52% observado prova que a meta foi ultrapassada?** Não. A diferença de +4,52 p.p. é descritiva; ambos os p-valores reais são ≥0,05. Não rejeitar H₀ também não prova cumprimento da meta.
4. **Quando a recomendação mudaria?** Com n maior e aproximação avaliada, Z pode ser usado; se execuções forem dependentes ou p variar no tempo, nenhum dos dois testes iid deve ser aplicado sem rever o modelo.

As outras perguntas podem explorar coleta, exclusão de cancelamentos, α, efeito, intervalo Monte Carlo, semente e limites de generalização. Respostas curtas de aproximadamente 30 segundos deixam tempo para a rodada inteira.
