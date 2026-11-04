# Handoff para Flávio — Lab04S01

Responsáveis: [#30 LuidiC](https://github.com/flavioferreiradev/Software-Measurement-and-Experimentation/issues/30)
e [#31 flavioferreiradev](https://github.com/flavioferreiradev/Software-Measurement-and-Experimentation/issues/31).
Project: [Kanban #3](https://github.com/users/flavioferreiradev/projects/3).

## Ponto de partida

Partir da **main atualizada após o merge do PR da #30**. A branch de origem
é `codex/lab04s01-luidi`. Nenhuma alteração dos Labs 01–03 é necessária.

```bash
git switch main
git pull --ff-only
git switch -c codex/lab04s01-flavio
cd Laboratorio4
python -m venv .venv
```

Ativar `.venv\Scripts\Activate.ps1` no PowerShell ou
`source .venv/bin/activate` no Linux/macOS. Depois:

```bash
python -m pip install -r requirements.txt
python -m src.run_demo
python -m pytest -q
```

Se o Temp do Windows estiver sem acesso, usar o diretório local descartável
descrito no README. Após instalar, a reprodução inteira da parte estatística
ocorre com **um comando**: `python -m src.run_demo`, sem token ou rede.
Não executar `src.collect` para montar o dashboard: os dados estão congelados.

## Arquivos para consumir

1. `results/demo_s01.json`: **fonte principal**; versão 1.0.0, todos os valores
   de G1/G2, estatísticas, p-valores, decisões, interpretações e parâmetros.
2. `data/real_ci.csv` e `data/source_metadata.json`: rastreabilidade e método.
3. `results/simulated_sample.csv`: a primeira amostra gerada com seed 42.
4. `docs/cenario_metodologia.md` e `docs/previsao_inicial.md`: textos do cenário,
   limitações e previsão que podem ser resumidos no dashboard.
5. `docs/contrato_integracao.md`: tipos, unidades, chaves e instruções de desenho.

G1: histogramas reais e simulados com bins [-0.5,0.5,1.5], lado a lado,
sucesso=0 e falha=1. As duas amostras têm 38 sucessos e quatro falhas, mas
sequências distintas; não alterar dados para tornar o gráfico mais diferente.

G2: um painel Z com N(0,1) **aproximada**, crítico 1,644853627 e cauda desde
Z observado 1,345185418; outro painel com massas Binomial(42,0,05), região
crítica K≥6 e cauda inclusiva K≥4. O JSON traz suporte, pdf/pmf, máscaras e
áreas. O exato usa soma de massas; não aplicar aproximação normal.

## Critérios restantes da Issue #31

- [ ] Consumir os dados e resultados da #30.
- [ ] Construir G1 com histogramas reais/simulados.
- [ ] Construir G2 com os dois testes e suas distribuições sob H₀.
- [ ] Destacar regiões críticas e áreas dos p-valores, inclusive sobreposição.
- [ ] Aplicar cores consistentes por teste, títulos, legendas, unidades e escalas.
- [ ] Construir o dashboard inicial em `dashboard/` e integrar G1/G2 diretamente.
- [ ] Exibir cenário, H₀/H₁, α e interpretação, com textos curtos junto aos gráficos.
- [ ] Preparar a estrutura visual para expansão posterior, sem implementar S02.
- [ ] Exibir links do repositório e do Kanban no topo.
- [ ] Acrescentar dependências visuais e comando único de abertura no README.
- [ ] Executar testes funcionais, visuais e de integração.
- [ ] Conferir todos os critérios S01 do enunciado e consolidar o README.
- [ ] Criar commits e PR com referência à **#31** e publicar a entrega da S01.

Isso cobre o checklist integral da Issue do Flávio; ela permanece aberta.
Não falta implementação estatística de Luidi para criar esses gráficos.

## Limites e organização

O exemplo é simulado e não confirma H₀. p do gerador é 4/42; p₀ é a meta de
0,05. n·p₀=2,1 torna a aproximação normal questionável. Os dois testes supõem
independência/estabilidade; o exato não corrige viés temporal ou cancelamentos.
As conclusões de desempenho só serão avaliadas na S02.

Quando iniciar, mover #31 de To do para Doing, respeitando WIP configurado
3 (e a prática anterior de um cartão ativo por integrante). A API local não
tem escopo de Projects; o navegador autenticado permitiu os movimentos no
Project existente. Não criar outro quadro para contornar permissões.
