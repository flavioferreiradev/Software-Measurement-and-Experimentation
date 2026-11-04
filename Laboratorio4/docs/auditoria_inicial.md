# Auditoria inicial — 04/11/2026

Antes das alterações de implementação foram lidas visualmente todas as sete
páginas de `Lab04.pdf`, pois o PDF não tem texto extraível. O P4 da página 2
prevê exatamente Z para proporção × binomial exato e CI com meta de 5%.
As páginas 3–4 delimitam S01 (dados, cenário, gerador, exemplo, G1/G2 no
dashboard) e S02 (Q1/Q2/Q3 e G3/G4). Páginas 6–7 exigem semente fixa,
execução por comando único, assignees e referência à Issue nos commits.

## Repositório e padrões

- Árvore inicial limpa, branch `codex/lab03-rotulos-luidi`, HEAD `e2a6ccc`.
- `main` local em `f4ce847`, oito commits atrás do remoto já conhecido.
- API confirmou a main atual `4865e5d7fa1b0e4d3bae40278d147984bc172f0f`.
  A nova branch `codex/lab04s01-luidi` parte desse commit, sem integrar a
  branch antiga. O endereço remoto antigo `flaviojuniordev` foi atualizado
  para o nome confirmado pela API: `flavioferreiradev`.
- Nenhum `AGENTS.md` encontrado na árvore rastreada.
- Lab01: mineração GitHub, scripts Python, relatórios, CSV/JSON, interfaces
  desktop/web e snapshots de Projects.
- Lab02: scripts e módulos Python, `requirements.txt`, pytest, katas, dados,
  análises e interface web. Há starters intencionalmente incompletos.
- Lab03: pacote modular `pipeline`, CLI `python -m pipeline`, pytest,
  configurações, coleta REST/GraphQL, CI próprio e documentação de métodos.
  Janela até 30/09/2026. A main atual inclui análises e relatório final.
- Mantido o padrão de pasta própria, módulos pequenos, dados versionados,
  requisitos, testes offline, documentação em português e GitHub Actions
  filtrado por caminhos. Lab04 não importa código nem dados anteriores.
- Histórico combina commits antigos sem Issue e commits recentes como
  `feat(#25)`/`feat(#28)`; todos os novos commits usarão `#30`.

## Issues e organização

Consultadas as Issues anteriores (1, 3–4, 6–7, 9–14, 16–17, 20–21, 24–25,
27–28). A divisão por integrante e a responsabilidade independente são
consistentes com o pedido. A busca anterior à criação não encontrou Lab04.
Criadas exatamente #30 (LuidiC) e #31 (flavioferreiradev), com os checklists
solicitados e identificador Lab04S01 no título e corpo.

Project identificado pela navegação do próprio repositório:
[Kanban #3](https://github.com/users/flavioferreiradev/projects/3).
Ambas as Issues foram adicionadas pelo workflow automático do Project.
A #30 foi movida para Doing e a #31 para To do antes da implementação.
O limite configurado observado de Doing é **3**, com **1** cartão em execução;
o relatório antigo sugeria 2. Nenhuma configuração ou cartão alheio foi alterado.
Mesmo o limite antigo mais restrito é respeitado.

O conector GitHub permite leitura, mas a criação de Issues respondeu 403
`Resource not accessible by integration`. A operação foi concluída pela API
REST com a credencial existente do Git. A consulta GraphQL de Projects
respondeu `INSUFFICIENT_SCOPES`: a credencial não tem `read:project`/`project`.
O navegador já autenticado permitiu gerenciar os cartões; não foi criado outro
Project, solicitado token novo ou ampliada permissão.

## Independência

Nova consulta à API em janela posterior à do Lab03, de um único workflow.
Nenhum dataset, resultado, arquivo ou código dos Labs 01–03 foi modificado.
O arquivo de previsão foi commitado antes da geração da amostra simulada:
`b70549b` (`docs(#30): registra cenario P4 e previsao anterior a simulacao`).
