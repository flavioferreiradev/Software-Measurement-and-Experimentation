# Validação local da implementação — 04/11/2026

Ambiente: Windows, Python 3.13.3, NumPy 2.4.2, SciPy 1.17.1, pytest 8.4.2.
Comandos executados dentro de `Laboratorio4`, usando `.venv/Scripts/python.exe`.

| Comando | Resultado |
|---|---|
| `python -m src.collect` | API: 46 runs, 42 incluídos, quatro cancelados excluídos, zero duplicidades |
| `python -m src.run_demo` | n=42, k=4; JSON, CSV simulado e interpretação produzidos offline |
| `python -m pytest -q` | 59 passaram; 14 erros de fixture por falta de acesso ao Temp do Windows |
| `python -m pytest -q --basetemp=.pytest-tmp/lab04-verification` | **73 passed**, zero falhas/erros, após criar o diretório pai local |

O diretório local usado é reservado a testes e ignorado pelo Git. Os erros
iniciais ocorreram antes do corpo dos testes de arquivos; não eram falhas de
cálculo. A suíte completa passou usando o Temp local. Não foi alterado nenhum
laboratório anterior para resolver a restrição do ambiente.

## Evidências protegidas pela suíte

- Mesma semente reproduz exatamente os valores de `default_rng(42)`.
- Entradas inválidas n/p/seed/amostras/p₀/α são rejeitadas.
- Amostras sem falhas e totalmente falhas geram caudas e decisões coerentes.
- p̂, Z e SE₀ conferem com fórmulas independentes; cauda normal confere com
  `math.erfc` e SciPy, e binomial confere com soma de `math.comb`, `binom.sf`
  e `binomtest`.
- Igualdade p-valor=α não rejeita: a regra é estritamente `<`.
- CSV é validado por hash, cabeçalho, tamanho, IDs únicos, classificação,
  branch/evento/workflow/status, datas, SHA, tentativa, URL e auditoria.
- Coletor é testado sem rede para filtros, cancelamentos, deduplicação e mínimo.
- JSON versionado confere com regeneração; bins, contagens, áreas analíticas,
  máscaras discretas e regiões críticas são consistentes.
- CLI executada em subprocesso exporta a mesma amostra, JSON e interpretação;
  exportações consecutivas são idênticas no mesmo ambiente.
- Alterações de parâmetros n/p/seed usam o mesmo núcleo sem modificar o CSV real.

## Revisão de escopo e publicação

O diff contém somente `Laboratorio4/` e `.github/workflows/lab04-tests.yml`.
Não inclui credenciais, `.venv`, caches ou resultados dos Labs 01–03.
O workflow do Lab04 executa pytest em Ubuntu e Windows com Python 3.12.
O resultado remoto da CI e o merge são verificáveis no PR ligado à Issue #30.
Gráficos, dashboard e estudos S02 não fazem parte deste diff.
