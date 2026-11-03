# Refatoração Arquitetural Automatizada com a skill `refactor-arch`

Solução do desafio **Criação de Skills — Refatoração Arquitetural Automatizada** (MBA IA — Desenvolvimento de Software e Aplicações com IA). O enunciado original está no [repositório base](https://github.com/devfullcycle/mba-ia-refactor-projects-skill).

A skill `refactor-arch` para **Claude Code** audita e refatora um backend para MVC em 3 fases: análise da stack, auditoria com relatório e confirmação, e refatoração validada. Ela foi executada nos 3 projetos legados deste repositório (2 em Python/Flask e 1 em Node.js/Express).

| Entregável | Onde |
|---|---|
| Skill (SKILL.md + 6 arquivos de referência) | `*/.claude/skills/refactor-arch/` (cópia idêntica nos 3 projetos) |
| Relatórios de auditoria (saída da Fase 2) | [`reports/audit-project-1.md`](reports/audit-project-1.md), [`-2`](reports/audit-project-2.md), [`-3`](reports/audit-project-3.md) |
| Saídas das Fases 1 e 3 | [`reports/validation/phase-outputs.md`](reports/validation/phase-outputs.md) |
| Logs de validação (boot + endpoints) | [`reports/validation/`](reports/validation) |
| Código refatorado (saída da Fase 3) | `code-smells-project/`, `ecommerce-api-legacy/`, `task-manager-api/` |

---

## A) Análise Manual

Antes de escrever a skill, li os três projetos inteiros, subi cada aplicação e registrei uma *baseline* com uma requisição por endpoint. Também provoquei alguns dos problemas para confirmar que eram reais e não só suspeitas. Abaixo estão os problemas mais relevantes de cada projeto. Os relatórios completos (17–20 findings cada) estão em `reports/`.

### Projeto 1 — `code-smells-project` (Python/Flask, API de e-commerce)

| # | Severidade | Problema | Onde | Por que importa |
|---|---|---|---|---|
| 1 | CRITICAL | **SQL Injection** em praticamente todas as queries (concatenação de strings) | `models.py:28, 47-50, 109-111, 289-297…` | Confirmei: `POST /login` com `' OR '1'='1` autentica como **Admin**. Qualquer campo de texto permite ler ou alterar o banco. |
| 2 | CRITICAL | **Endpoints admin sem proteção**: `/admin/query` executa SQL arbitrário e `/admin/reset-db` apaga tudo | `app.py:47-78` | Um único request anônimo destrói o banco ou extrai todas as senhas. |
| 3 | CRITICAL | **Senhas em texto puro** e **devolvidas na API** (`GET /usuarios` retorna `senha`); `/health` devolve a `SECRET_KEY` | `database.py:75-83`, `models.py:83,99`, `controllers.py:285-289` | Vazamento direto de credenciais de todos os usuários e da chave da aplicação. |
| 4 | CRITICAL | **God File**: `models.py` concentra SQL e regras de 4 domínios (estoque, total do pedido, desconto…) | `models.py:1-314` | Não há como testar ou alterar um domínio sem tocar nos outros. |
| 5 | HIGH | **Conexão SQLite global** com `check_same_thread=False`, compartilhada entre threads | `database.py:4-10` | Requests concorrentes misturam transações; não dá para apontar para outro banco em testes. |
| 6 | HIGH | **Pedido sem transação**: insere pedido, itens e baixa estoque sem rollback | `models.py:133-169` | Uma falha no meio deixa pedido sem itens ou estoque baixado pela metade. |
| 7 | MEDIUM | **N+1**: 1 query por pedido + 1 por item para buscar o nome do produto | `models.py:171-233` | A listagem degrada linearmente com o volume de dados. |
| 8 | MEDIUM | **Validação duplicada e inconsistente** (create ≠ update; `"preco": "abc"` → 500) | `controllers.py:26-90` | Entrada inválida vira erro interno ou grava dados inconsistentes. |
| 9 | LOW | **Magic numbers** nas faixas de desconto (`10000`, `0.1`, …) e listas literais | `models.py:256-262` | Regra de negócio escondida no meio do código. |
| 10 | LOW | **`print` como log** (inclusive com e-mails de usuários) | `controllers.py` (11 pontos) | Sem nível nem filtragem em produção. |

### Projeto 2 — `ecommerce-api-legacy` (Node.js/Express, LMS com checkout)

| # | Severidade | Problema | Onde | Por que importa |
|---|---|---|---|---|
| 1 | CRITICAL | **Credenciais hardcoded** (`dbPass`, `paymentGatewayKey: "pk_live_…"`) | `src/utils.js:2-5` | Quem tem acesso ao repositório tem a senha do banco e a chave do gateway. |
| 2 | CRITICAL | **Número do cartão e chave do gateway no log** a cada checkout | `src/AppManager.js:45` | Violação direta de PCI-DSS. |
| 3 | CRITICAL | **God class `AppManager`**: conexão, schema, seed, rotas e todas as regras numa classe | `src/AppManager.js:4-139` | Nenhuma regra é testável isoladamente. |
| 4 | CRITICAL | **"Hash" caseiro** (`badCrypto` = base64 truncado) e senha padrão `"123456"` | `src/utils.js:17-23`, `AppManager.js:68` | As senhas são praticamente reversíveis; contas sem senha compartilham uma senha conhecida. |
| 5 | HIGH | **Um request derruba o servidor**: `"card": 4111` (número) → `TypeError` não capturado | `src/AppManager.js:46` | Confirmei: o processo Node encerra (DoS trivial). |
| 6 | HIGH | **Escritas sem transação** e `DELETE /users` deixa matrículas e pagamentos órfãos (a própria resposta admite) | `AppManager.js:50-62, 131-137` | Matrícula sem pagamento; o relatório financeiro mostra alunos "Unknown". |
| 7 | MEDIUM | **N+1** no relatório financeiro, coordenado por contadores manuais | `AppManager.js:83-127` | 1 + C + 2·E queries; a resposta pode nunca ser enviada se um callback falhar. |
| 8 | MEDIUM | **Erros ignorados** nos callbacks (`err` não verificado) | `AppManager.js:57, 92-93, 104-106, 133` | Falhas silenciosas e crashes. |
| 9 | LOW | **Nomes ruins**: `u`, `e`, `p`, `cid`, `cc`, `badCrypto`, `AppManager` | `AppManager.js:29-33` | O código fica difícil de ler. |
| 10 | LOW | **Código morto** (`totalRevenue`, `dbUser`, `smtpUser` nunca usados) e **callback hell** de 6 níveis | `utils.js:2-10`, `AppManager.js:37-77` | Ruído e fluxo difícil de seguir. |

### Projeto 3 — `task-manager-api` (Python/Flask, Task Manager com camadas parciais)

| # | Severidade | Problema | Onde | Por que importa |
|---|---|---|---|---|
| 1 | CRITICAL | **MD5 sem salt** para senhas | `models/user.py:27-32` | O hash é revertido em segundos com rainbow tables. |
| 2 | CRITICAL | **Hash da senha devolvido** em `GET /users/<id>`, `POST /users`, `PUT /users`, `POST /login` | `models/user.py:16-25` | Somado ao MD5, qualquer cliente recupera a senha de qualquer usuário. |
| 3 | CRITICAL | **`SECRET_KEY` e senha SMTP hardcoded** | `app.py:13`, `services/notification_service.py:7-10` | Segredos versionados no git. |
| 4 | HIGH | **Regra de negócio nas rotas** (sem controllers); `services/` e `utils/` existem mas não são usados | `routes/*.py` | A separação de camadas é só aparente: rotas de 50–90 linhas. |
| 5 | HIGH | **Token falso** `'fake-jwt-token-' + id` e qualquer um cria usuário `admin` via `POST /users` | `routes/user_routes.py:52, 210` | Confirmei a escalada de privilégio; o token é forjável trocando o número. |
| 6 | MEDIUM | **APIs deprecated**: `datetime.utcnow()` (22×) e `Query.get()` (16×, `LegacyAPIWarning`) | ver relatório | Gera avisos a cada request e vai quebrar quando as APIs forem removidas. |
| 7 | MEDIUM | **N+1**: 2 queries por task em `GET /tasks`; 13 `count()` + 1 query por usuário no resumo | `task_routes.py:41-57`, `report_routes.py:15-68` | Custo cresce com o volume de dados. |
| 8 | MEDIUM | **Regra "atrasada" reescrita 6×**, ignorando `Task.is_overdue()` | `task_routes.py:30-39…` | Cópias divergentes de uma mesma regra. |
| 9 | MEDIUM | **12 `except:` nus** e **validação que vira 500** (`"priority": "2"`, `?priority=abc`) | `routes/*.py`, `utils/helpers.py` | Confirmei os dois 500; erros são mascarados. |
| 10 | LOW | **Código morto**: quase todo `utils/helpers.py`, imports `os, sys, json, time, hashlib` | `utils/helpers.py`, `app.py:7` | Dá a falsa impressão de que a validação já está centralizada. |
| 11 | LOW | **Magic numbers** (`3`, `200`, `4`, `7` dias, prioridade `<= 2`) e `print` como log | `routes/*.py` | Regras de negócio espalhadas em literais. |

---

## B) Construção da Skill

### Estrutura

```
.claude/skills/refactor-arch/
├── SKILL.md                              # o "prompt": papel, fases, formatos de saída, regras invioláveis
└── references/
    ├── project-analysis.md               # Fase 1 — detecção de linguagem/framework/DB/domínio/arquitetura
    ├── anti-patterns-catalog.md          # Fase 2 — 23 anti-patterns (AP-01…AP-23) com sinais de detecção
    ├── report-template.md                # Fase 2 — formato obrigatório do relatório + exemplos bom/ruim
    ├── mvc-guidelines.md                 # Fase 3 — arquitetura-alvo, responsabilidades, árvore por stack
    ├── refactoring-playbook.md           # Fase 3 — 15 transformações (PB-01…PB-15) com antes/depois
    └── validation.md                     # Fases 1 e 3 — baseline, smoke test, diff, critérios de saída
```

### Decisões de design

- **SKILL.md enxuto, conhecimento nas referências.** O SKILL.md diz *o que fazer e em que ordem*; cada referência é carregada só na fase em que é necessária (tabela "quando ler" no topo). Isso mantém o contexto pequeno e permite evoluir o catálogo sem mexer no fluxo.
- **Formatos de saída fixos.** Os blocos `PHASE 1`, `ARCHITECTURE AUDIT REPORT` e `PHASE 3` são templates literais. Com isso o resultado sai comparável entre projetos e verificável pelo checklist.
- **IDs ligam tudo.** Cada anti-pattern tem um ID (`AP-xx`), e o catálogo aponta o padrão do playbook que o corrige (`PB-xx`). Cada finding do relatório recebe um `Fxx`, que o resumo da Fase 3 usa para dizer o que foi feito com ele. Assim é possível rastrear cada finding até a transformação aplicada.
- **Pausa obrigatória.** A Fase 2 é somente leitura e termina com `Proceed with refactoring (Phase 3)? [y/n]`. O relatório só é gravado depois do `y` (argumento `report=<caminho>`), e com `n` a skill oferece salvar apenas o relatório. O frontmatter usa `disable-model-invocation: true` para que a skill nunca seja disparada automaticamente: só por `/refactor-arch`.
- **Contrato público é inviolável.** As regras da Fase 3 mantêm rotas, métodos, status, nomes de campos, envelope de erro e comando de start. Exceções só por segurança, e cada uma é listada em "Contract changes".
- **Validação baseada em baseline, não em "parece funcionar".** A Fase 1 já sobe a aplicação e grava o comportamento de todos os endpoints. Na Fase 3 o mesmo script roda de novo e o `diff` precisa sair limpo.
- **Sem dependências novas.** O playbook prefere o que a stack já oferece: `werkzeug.security`, `itsdangerous`, `node:crypto`.
- **Decisões de produto não são automatizadas.** Exigir autenticação em todas as rotas quebraria clientes. Esse tipo de item vira "Deferred" com recomendação, em vez de ser aplicado.

### Anti-patterns do catálogo (23, com severidade distribuída)

| Severidade | Anti-patterns | Por que estão no catálogo |
|---|---|---|
| CRITICAL (6) | AP-01 Credenciais hardcoded · AP-02 SQL Injection · AP-03 God Class/File · AP-04 Senha insegura · AP-05 Exposição de dados sensíveis · AP-06 Endpoint perigoso sem proteção | Os problemas de maior dano, todos presentes em pelo menos um projeto |
| HIGH (6) | AP-07 Fat controller · AP-08 Estado global mutável · AP-09 Acoplamento sem DI · AP-10 Escrita sem transação/órfãos · AP-11 Config insegura (debug) · AP-12 Token falso | Violações de MVC/SOLID que impedem testes e geram inconsistência |
| MEDIUM (6) | AP-13 N+1 · AP-14 Validação · AP-15 Duplicação · AP-16 Tratamento de erro · **AP-17 APIs deprecated** · AP-18 Efeitos colaterais no handler | Performance e qualidade; AP-17 traz uma tabela de APIs obsoletas → equivalente moderno (Python, SQLAlchemy, Flask, Werkzeug, Node, Express) |
| LOW (5) | AP-19 Magic numbers · AP-20 Nomes ruins · AP-21 `print` como log · AP-22 Código morto · AP-23 Condicionais verbosas/callback hell | Legibilidade |

Cada entrada tem **sinais de detecção concretos** por linguagem (regex/padrões de grep e contexto a confirmar), seguindo a dica do enunciado: "query SQL dentro de loop for" em vez de "código ruim".

### Como garanti que a skill é agnóstica de tecnologia

1. **Heurísticas por manifesto, não por projeto.** `project-analysis.md` mapeia manifestos e assinaturas de código de 8 linguagens e 10+ frameworks.
2. **Sinais de detecção em mais de uma linguagem.** Cada anti-pattern traz padrões para Python e JS/TS, além de um sinal genérico.
3. **Arquitetura-alvo descrita por responsabilidade**, com árvores concretas para Flask e Express e uma tabela de equivalência para FastAPI, Django, NestJS, Spring e Go.
4. **Estratégias por nível de organização** (monolito, god class, camadas parciais), escolhidas na Fase 3 a partir do diagnóstico da Fase 1.
5. **Teste real em 2 stacks e 3 níveis de organização.** A mesma pasta, sem nenhuma alteração, foi copiada para os 3 projetos.

### Desafios encontrados e como resolvi

| Desafio | Solução |
|---|---|
| "Endpoints continuam funcionando" é subjetivo | Baseline + diff de status obrigatórios (`validation.md`). Nos projetos 1 e 3 fiz ainda a comparação **JSON completa** original × refatorado lado a lado. |
| Corrigir segurança sem quebrar o contrato (ex.: `/admin/query`) | Regra "exceções só por segurança, listadas em Contract changes" + PB-06: o endpoint continua existindo, mas desabilitado por padrão e protegido por `X-Admin-Token`, aceitando só `SELECT` em conexão read-only. |
| Envelopes de erro diferentes por projeto (`{"erro"}`, `{"error"}`, texto puro) | A guideline exige que o error handler central reproduza o envelope original de cada projeto. |
| Senhas legadas (texto puro / MD5) ao trocar o algoritmo de hash | O playbook PB-04 prevê migração transparente: verifica no formato antigo uma vez e re-hasheia no login bem-sucedido. |
| `datetime.utcnow()` → `datetime.now(timezone.utc)` quebra comparações com datetimes naive do SQLite | PB-13 manda manter a semântica de armazenamento (helper `utcnow()` que devolve UTC naive). |
| Projeto 3 já organizado: risco de "refatorar por estética" | `mvc-guidelines.md` traz a estratégia "camadas parciais": preservar a estrutura de pastas, adicionar só o que falta (controllers, config, middlewares) e corrigir o que está no lugar errado. |
| No projeto 2, um único request derrubava o processo, o que inviabilizava parte da baseline | Registrei o crash como finding HIGH. Depois da refatoração, o mesmo request retorna 400 e o servidor continua de pé. |
| Numeração de findings ficou inconsistente numa primeira versão do relatório 2 | Reforcei no template: "Summary deve bater com a contagem real", e IDs sequenciais `Fxx`. |

---

## C) Resultados

### Resumo das auditorias

| Projeto | Stack | Arquivos / linhas | CRITICAL | HIGH | MEDIUM | LOW | Total | Deprecated APIs |
|---|---|---|---|---|---|---|---|---|
| 1 — code-smells-project | Python + Flask 3.1.1 | 4 / ~780 | 6 | 5 | 5 | 4 | **20** | nenhuma (verificado com `python -W default`) |
| 2 — ecommerce-api-legacy | Node.js + Express 4 | 3 / ~180 | 5 | 4 | 3 | 5 | **17** | nenhuma (verificado com `node --trace-deprecation`) |
| 3 — task-manager-api | Python + Flask 3.0 + SQLAlchemy | 15 / ~1160 | 3 | 4 | 6 | 4 | **17** | `datetime.utcnow()` ×22, `Query.get()` ×16 |

Todos os problemas da Análise Manual aparecem nos relatórios gerados.

### Antes × depois

**Projeto 1** — monolito → MVC completo em `src/`

```
ANTES                         DEPOIS
app.py        (rotas+admin)   app.py                       # entry point fino (python app.py)
controllers.py (HTTP+fluxo)   src/app.py                   # create_app(): composition root
models.py     (God File)      src/config/settings.py       # env vars + constantes de negócio
database.py   (conexão global)src/database.py              # conexão por request (flask.g), schema, seed
                              src/models/      produto, usuario, pedido, admin
                              src/controllers/ produto, usuario, pedido, relatorio, sistema, admin
                              src/views/       produto_routes, usuario_routes, pedido_routes, sistema_routes
                              src/services/    password_service, notification_service
                              src/middlewares/ error_handler, admin_auth
                              src/utils/validators.py · src/errors.py
```

**Projeto 2** — God class → MVC em `src/` com DI por construtor

```
ANTES                         DEPOIS
src/app.js                    src/app.js            # entry point (npm start inalterado)
src/AppManager.js (tudo)      src/createApp.js      # composition root
src/utils.js (config+global)  src/config/index.js
                              src/database/         connection.js (Promises + transaction()), schema.js
                              src/models/           User, Course, Enrollment, Payment, AuditLog
                              src/controllers/      Checkout, Report, User
                              src/routes/index.js   # camada View
                              src/services/         paymentGateway, passwordHasher (scrypt), cache, logger
                              src/middlewares/      errorHandler, asyncHandler, requireAdminToken
```

**Projeto 3** — camadas parciais → camadas completas (estrutura de pastas preservada)

```
ANTES                                   DEPOIS
app.py (config fixa, create_all)        app.py                  # application factory create_app()
models/  task, user (MD5), category     models/                 # + acesso a dados (joinedload, GROUP BY), is_overdue, to_dict seguro
routes/  task, user, report(+categorias)routes/                 # finas; + category_routes, system_routes
services/notification_service (morto)   services/               # notification (config injetada, ligada à atribuição de task), token_service
utils/helpers.py (morto)                utils/                  # validators.py, time.py (utcnow)
—                                       config/settings.py · controllers/ (task, user, report, category)
—                                       middlewares/error_handler.py · errors.py
```

### Checklist de validação

| Item | Projeto 1 | Projeto 2 | Projeto 3 |
|---|:-:|:-:|:-:|
| **Fase 1** — Linguagem detectada corretamente | ✅ Python | ✅ JavaScript (Node 22) | ✅ Python |
| Framework detectado corretamente | ✅ Flask 3.1.1 | ✅ Express ^4.18.2 | ✅ Flask 3.0.0 + Flask-SQLAlchemy |
| Domínio descrito corretamente | ✅ E-commerce | ✅ LMS com checkout | ✅ Task Manager |
| Nº de arquivos condiz com a realidade | ✅ 4 | ✅ 3 | ✅ 15 |
| **Fase 2** — Relatório segue o template | ✅ | ✅ | ✅ |
| Cada finding com arquivo e linhas exatos | ✅ | ✅ | ✅ |
| Ordenado CRITICAL → LOW | ✅ | ✅ | ✅ |
| ≥ 5 findings | ✅ 20 | ✅ 17 | ✅ 17 |
| APIs deprecated (se aplicável) | ✅ verificado, nenhuma | ✅ verificado, nenhuma | ✅ 2 APIs, 38 ocorrências |
| Pausa e pede confirmação antes da Fase 3 | ✅ | ✅ | ✅ |
| **Fase 3** — Estrutura MVC | ✅ | ✅ | ✅ |
| Config extraída (sem hardcoded) | ✅ `src/config/settings.py` | ✅ `src/config/index.js` | ✅ `config/settings.py` |
| Models abstraem os dados | ✅ | ✅ | ✅ |
| Views/Routes separadas | ✅ `src/views/` | ✅ `src/routes/` | ✅ `routes/` |
| Controllers concentram o fluxo | ✅ | ✅ | ✅ |
| Error handling centralizado | ✅ | ✅ | ✅ |
| Entry point claro | ✅ `python app.py` | ✅ `npm start` | ✅ `python app.py` |
| Aplicação inicia sem erros | ✅ | ✅ | ✅ |
| Endpoints originais respondem corretamente | ✅ 22/22 | ✅ 8/8 | ✅ 29/29 |

### Logs das aplicações rodando após a refatoração

Os logs completos (boot + todas as requisições + diff com a baseline) estão em [`reports/validation/`](reports/validation). Trechos:

```
# Projeto 1 — python app.py
 * Serving Flask app 'src.app'
 * Debug mode: off
 * Running on http://127.0.0.1:5000
POST /login -> 200 {"dados":{"email":"joao@email.com","id":2,"nome":"João Silva","tipo":"cliente"},"mensagem":"Login OK","sucesso":true}
POST /pedidos -> 201 {"dados":{"pedido_id":1,"total":479.7},"mensagem":"Pedido criado com sucesso","sucesso":true}
$ diff de status vs baseline (código original)
sem diferenças: 22/22 requisições com o mesmo status
# provas das correções de segurança
SQLi login (' OR '1'='1)        -> 401   (antes: 200 como Admin)
GET /usuarios contém "senha"    -> 0 ocorrências
POST /admin/query sem token     -> 403
POST /admin/query DELETE ...    -> 400 "Apenas consultas SELECT são permitidas"
```

```
# Projeto 2 — npm start
[2026-11-03T23:18:11.705Z] INFO LMS API rodando na porta 3000
[2026-11-03T23:18:13.502Z] INFO Processando pagamento de 497 no cartão final 4444
POST /api/checkout -> 200 {"msg":"Sucesso","enrollment_id":2}
POST /api/checkout -> 400 Pagamento recusado
GET /api/admin/financial-report -> 200 [{"course":"Clean Architecture","revenue":997,...}]
DELETE /api/users/1 -> 200 Usuário deletado
sem diferenças: 8/8 requisições com o mesmo status
# "card": 4111 (número)          -> 400 Bad Request, servidor continua de pé (antes: processo encerrado)
```

```
# Projeto 3 — python seed.py && python app.py
Seed concluído com sucesso!
 * Running on http://127.0.0.1:5000
sem diferenças: 29/29 requisições com o mesmo status
# comparação JSON completa original × refatorado (21 requisições): 0 diferenças
#   (ignorando timestamps, hash de senha removido e formato do token)
POST /tasks {"priority":"2"}     -> 400 (antes: 500)
GET /tasks/search?priority=abc   -> 400 (antes: 500)
python -W default app.py         -> nenhum DeprecationWarning/LegacyAPIWarning
```

### Mudanças de contrato (todas por segurança)

| Projeto | Mudança |
|---|---|
| 1 | `GET /usuarios[/<id>]` não devolve mais `senha`; `/health` não devolve `secret_key`, `debug`, `db_path`; `/admin/*` exige `X-Admin-Token` e `/admin/query` aceita só `SELECT`; respostas de erro passam a incluir sempre `"sucesso": false`; `PUT /pedidos/<id>/status` de pedido inexistente retorna 404. |
| 2 | `GET /api/admin/financial-report` exige `X-Admin-Token`; `DELETE /api/users/:id` remove também matrículas e pagamentos e responde "Usuário deletado" (404 se não existir); `card` precisa ser string de dígitos. |
| 3 | Respostas de usuário não devolvem `password`; `token` do login agora é assinado (`itsdangerous`) com expiração. |

**Deferred (exige decisão de produto):** autenticação/autorização nas rotas de escrita dos projetos 1 e 3 (inclui a escalada de privilégio via `role` no `POST /users`) e no `DELETE /api/users/:id` do projeto 2.

### Observações sobre o comportamento em stacks diferentes

- **Monolito Python (P1):** a skill criou a árvore MVC completa. A maior parte do trabalho foi segurança (SQL injection em ~17 pontos) e quebrar o God File por entidade.
- **Node/Express (P2):** como a arquitetura-alvo é descrita por responsabilidade, ela se traduziu direto em classes com injeção por construtor. O ponto específico da stack foi promisificar o driver `sqlite3` e serializar as transações sobre a conexão única. O catálogo pegou um problema que só existe em JS: exceção dentro de callback derrubando o processo.
- **Python já em camadas (P3):** o diagnóstico "camadas parciais" levou a uma refatoração mais conservadora. A estrutura de pastas foi preservada, e a skill adicionou controllers, config e error handler, tirou categorias do blueprint de relatórios e reativou código que estava morto (validações, `NotificationService`). Foi o único projeto com APIs deprecated, o que exercitou a tabela AP-17.
- **APIs deprecated:** nos projetos 1 e 2 a skill não inventou achados. Declarou "none detected" e listou o que foi verificado, como pede o template.

### Como esta execução foi feita

As três execuções seguiram o `SKILL.md` passo a passo: Fase 1, Fase 2 com a pausa respondida com `y`, Fase 3 e validação. Quem executou foi o Claude (Opus 5.5), numa sessão agêntica baseada no Claude Code. O `claude` CLI daquele ambiente não conseguia autenticar, então não foi possível disparar `claude "/refactor-arch"` literalmente. Para reproduzir localmente, veja a seção D.

---

## D) Como Executar

### Pré-requisitos

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) instalado e autenticado (`claude --version`).
- Python 3.10+ (projetos 1 e 3) e Node.js 18+ (projeto 2), `curl` para os testes.

### Executar a skill em cada projeto

A skill fica em `.claude/skills/refactor-arch/` dentro de cada projeto, então basta abrir o Claude Code na pasta do projeto:

```bash
# Projeto 1
cd code-smells-project
claude "/refactor-arch report=../reports/audit-project-1.md"

# Projeto 2
cd ../ecommerce-api-legacy
claude "/refactor-arch report=../reports/audit-project-2.md"

# Projeto 3
cd ../task-manager-api
claude "/refactor-arch report=../reports/audit-project-3.md"
```

- `report=` define onde o relatório da Fase 2 é salvo (padrão: `docs/refactor-arch/audit-report.md`).
- A skill **para** ao fim da Fase 2 com `Proceed with refactoring (Phase 3)? [y/n]`. Responda `y` para refatorar ou `n` para só salvar o relatório.
- Para rodar de novo sobre o código original: `git checkout 6d1ce62 -- <projeto>` (commit inicial do boilerplate).

### Validar que a refatoração funcionou

```bash
# Projeto 1 (porta 5000)
cd code-smells-project && pip install -r requirements.txt
ADMIN_TOKEN=dev-token python app.py
curl localhost:5000/health
curl -X POST localhost:5000/login -H 'Content-Type: application/json' \
     -d '{"email":"joao@email.com","senha":"123456"}'
curl -X POST localhost:5000/admin/query -H 'X-Admin-Token: dev-token' \
     -H 'Content-Type: application/json' -d '{"sql":"SELECT id, nome FROM produtos"}'

# Projeto 2 (porta 3000) — exemplos prontos em api.http
cd ecommerce-api-legacy && npm install
ADMIN_TOKEN=dev-token npm start
curl -X POST localhost:3000/api/checkout -H 'Content-Type: application/json' \
     -d '{"usr":"Ana","eml":"ana@x.com","pwd":"senha","c_id":2,"card":"4111222233334444"}'
curl localhost:3000/api/admin/financial-report -H 'X-Admin-Token: dev-token'

# Projeto 3 (porta 5000)
cd task-manager-api && pip install -r requirements.txt
python seed.py && python app.py
curl localhost:5000/tasks
curl localhost:5000/reports/summary
```

O procedimento completo usado pela skill (baseline → smoke test → `diff` de status → varredura dos anti-patterns corrigidos) está em [`references/validation.md`](code-smells-project/.claude/skills/refactor-arch/references/validation.md). Cada projeto tem um `.env.example` com as variáveis suportadas.
