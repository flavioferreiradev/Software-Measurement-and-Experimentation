# Previsão anterior à simulação — P4

Registro feito antes de escrever/executar o gerador e de observar a amostra
simulada. Este arquivo será commitado separadamente com referência à Issue #30.
Não será reescrito para acomodar o exemplo obtido.

Pergunta: a proporção de execuções de CI com falha supera a meta de 5%?
H₀: p ≤ 0,05; H₁: p > 0,05; α = 0,05; unilateral à direita.

Esperamos que o binomial exato controle melhor o nível nominal em amostras
pequenas com falha rara: ele usa a cauda Binomial(n, 0,05), sem aproximação
normal. A natureza discreta pode torná-lo conservador. O Z usa variância sob H₀,
sem correção de continuidade; quando n·p₀ é pequeno, a aproximação de sua cauda
pode ser inadequada. Com amostras maiores esperamos maior concordância.
Isso não prevê qual teste terá menor p-valor em um exemplo particular, nem
garante maior poder do exato. Uma demonstração isolada não mede erro tipo I
ou poder: essa comparação fica para a S02.

## Decisões de coleta anteriores à inspeção de resultados

Fonte escolhida: pytest-dev/pytest, workflow `test`
(`.github/workflows/test.yml`, id 22158026), eventos `push` em `main`.
Escolha por ser uma suíte de testes de software pública, com histórico
suficiente; não foi feita consulta às falhas para escolher o projeto.
O workflow de psf/requests foi consultado como candidato, mas não seus runs.

Janela fechada de criação: 2026-10-01T00:00:00Z até 2026-11-04T18:00:00Z,
posterior à janela do Lab03 (encerrada em 30/09). Nenhum dataset anterior será
lido pela implementação do Lab04.

Selecionar as 60 execuções válidas mais recentes na janela, em ordem
decrescente de `(created_at, id)`, sem escolher pelos resultados. Se a janela
contiver entre 30 e 59 válidas, usar todas; se menos de 30, interromper e registrar
uma ampliação de janela antes de coletar novamente. `success` = 0;
`failure` ou `timed_out` = 1 (timeout significa que a rotina não cumpriu a
validação). Canceladas, skipped, neutral, action_required, stale e outras
conclusões não determinantes ficam fora do denominador e são auditadas.
Uma observação por run.id, na tentativa mais recente disponível pela API;
tentativas anteriores não são unidades adicionais.

Gerador: Bernoulli(p empírico), n igual ao CSV real, `default_rng(42)`.
O p empírico será k/n observado; p₀ = 0,05 é a meta fixa e não será estimado.
Preservar a primeira amostra gerada, mesmo sem significância ou divergência.

Limitações previstas: seleção temporal por conveniência, reruns podem ocultar
falhas anteriores, alterações na suíte/infraestrutura, dependência entre commits
e falhas de infraestrutura. O modelo iid Bernoulli é uma simplificação; a meta
é pedagógica e não uma política declarada pelo projeto fonte.
