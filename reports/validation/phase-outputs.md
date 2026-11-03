# Saídas das Fases 1 e 3 (execução da skill `refactor-arch`)

A saída completa da Fase 2 de cada projeto está em `reports/audit-project-{1,2,3}.md`. Este arquivo guarda os blocos impressos nas Fases 1 e 3.

---

## Projeto 1 — code-smells-project

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python 3
Framework:     Flask 3.1.1
Dependencies:  flask-cors 5.0.1
Database:      SQLite (driver sqlite3 cru, arquivo loja.db, schema + seed criados no boot)
Domain:        E-commerce API (produtos, usuários, pedidos, itens de pedido, relatório de vendas)
Architecture:  Monolítica — 4 arquivos sem separação de camadas; models.py é God File (SQL + regras de 4 domínios),
               controllers.py mistura HTTP e fluxo, app.py mistura rotas, SQL administrativo e bootstrap
Entry point:   app.py (start: python app.py)
Source files:  4 files analyzed (~780 lines)
DB tables:     produtos, usuarios, pedidos, itens_pedido
Endpoints:     19 (GET /, GET /health, GET|POST /produtos, GET /produtos/busca, GET|PUT|DELETE /produtos/<id>,
               GET|POST /usuarios, GET /usuarios/<id>, POST /login, GET|POST /pedidos, GET /pedidos/usuario/<id>,
               PUT /pedidos/<id>/status, GET /relatorios/vendas, POST /admin/reset-db, POST /admin/query)
================================
```

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
app.py                         (entry point → src.app.create_app)
src/
├── app.py                     (composition root)
├── config/settings.py
├── database.py
├── errors.py
├── models/       produto_model.py, usuario_model.py, pedido_model.py, admin_model.py
├── controllers/  produto_, usuario_, pedido_, relatorio_, sistema_, admin_controller.py
├── views/        produto_routes.py, usuario_routes.py, pedido_routes.py, sistema_routes.py
├── services/     password_service.py, notification_service.py
├── middlewares/  error_handler.py, admin_auth.py
└── utils/validators.py

## Findings addressed
F01 SQL Injection          → todas as queries parametrizadas; filtros dinâmicos por lista de cláusulas fixas (PB-02)
F02 Admin sem proteção     → X-Admin-Token (desabilitado sem ADMIN_TOKEN); /admin/query só SELECT em conexão read-only (PB-06)
F03 Credenciais hardcoded  → src/config/settings.py + .env.example; SECRET_KEY efêmera em dev (PB-01)
F04 Senha em texto puro    → werkzeug hash; login verifica em código; migração de senhas legadas (PB-04)
F05 Exposição de dados     → senha fora das leituras públicas; health sem secret/debug/db_path (PB-05)
F06 God File               → models/controllers/views por domínio (PB-03)
F07 HTTP misturado ao fluxo→ views finas + controllers sem Flask (PB-07)
F08 Conexão global         → conexão por request via flask.g + teardown (PB-08)
F09 Acoplamento            → create_app injeta models/serviços nos controllers (PB-08)
F10 Pedido sem transação   → validação prévia + `with db:` atômico (PB-09)
F11 Config insegura        → FLASK_DEBUG/HOST/PORT/CORS_ORIGINS via ambiente, debug off por padrão (PB-01)
F12 N+1                    → pedidos em 2 queries com LEFT JOIN; relatório em 1 query de agregação (PB-10)
F13 Validação              → src/utils/validators.py único para create/update, com checagem de tipo (PB-11)
F14 Tratamento de erro     → AppError + error handler central, envelope {"erro", "sucesso": false} (PB-12)
F15 Duplicação             → um mapeador por entidade; listagem de pedidos com filtro opcional (PB-03)
F16 Efeitos colaterais     → NotificationService injetado (PB-07)
F17 Magic numbers          → FAIXAS_DESCONTO, CATEGORIAS_VALIDAS, STATUS_PEDIDO_VALIDOS... (PB-14)
F18 print                  → logging (PB-14)
F19 Código morto           → imports e SELECT 1 removidos (PB-14)
F20 Nomes                  → produto_id/usuario_id/pedido_id, sem sombrear builtins (PB-14)
Deferred: autenticação de usuários nas rotas de escrita (decisão de produto)

## Contract changes
- GET /usuarios[/<id>] sem o campo "senha"; GET /health sem secret_key/debug/db_path
- /admin/* exige X-Admin-Token; /admin/query aceita apenas SELECT
- respostas de erro sempre com "sucesso": false; PUT /pedidos/<id>/status de pedido inexistente → 404

## Validation
  ✓ Application boots without errors (python app.py)
  ✓ All 22 baseline endpoints respond correctly (22/22) — JSON completo idêntico, exceto /health
  ✓ No remaining occurrences of fixed anti-patterns (SQL concatenado, print, global, senha em resposta)
================================
```

---

## Projeto 2 — ecommerce-api-legacy

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      JavaScript (Node.js 22, CommonJS)
Framework:     Express ^4.18.2
Dependencies:  sqlite3 ^5.1.6
Database:      SQLite em memória (driver sqlite3 com callbacks; schema + seed no boot)
Domain:        LMS com checkout (usuários, cursos, matrículas, pagamentos, logs de auditoria)
Architecture:  God class — AppManager concentra conexão, schema, seed, rotas e regras; utils.js com config e estado global
Entry point:   src/app.js (start: npm start)
Source files:  3 files analyzed (~180 lines)
DB tables:     users, courses, enrollments, payments, audit_logs
Endpoints:     3 (POST /api/checkout, GET /api/admin/financial-report, DELETE /api/users/:id)
================================
```

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
src/
├── app.js                 (entry point, npm start)
├── createApp.js           (composition root)
├── config/index.js
├── errors.js
├── database/   connection.js (Promises + transaction()), schema.js
├── models/     UserModel, CourseModel, EnrollmentModel, PaymentModel, AuditLogModel
├── controllers/CheckoutController, ReportController, UserController
├── routes/index.js        (View)
├── services/   paymentGateway, passwordHasher, cache, logger
└── middlewares/errorHandler, asyncHandler, requireAdminToken

## Findings addressed
F01 Credenciais hardcoded → config/index.js via process.env, sem defaults reais; .env.example (PB-01)
F02 God class             → database/models/controllers/routes/services (PB-03)
F03 Senha insegura        → scrypt + salt (node:crypto); sem senha padrão (hash inutilizável) (PB-04)
F04 Cartão/chave em log   → log só com os 4 últimos dígitos, sem chave (PB-05)
F05 Relatório sem proteção→ requireAdminToken (X-Admin-Token) (PB-06)
F06 Sem transação/órfãos  → db.transaction(); deleção em cascata; pagamento decidido antes de escrever (PB-09)
F07 Crash por tipo        → parseCheckoutRequest valida tipos; async/await + middleware de erro (PB-11, PB-12)
F08 Estado global         → InMemoryCache injetado e limitado (PB-08)
F09 Regra no handler/DI   → CheckoutController com dependências por construtor (PB-07, PB-08)
F10 N+1                   → uma query com LEFT JOINs (PB-10)
F11 Erros ignorados       → driver promisificado + asyncHandler + errorHandler central (PB-12)
F12 Efeitos colaterais    → auditoria e cache chamados pelo controller via dependências (PB-07)
F13 Nomes                 → desestruturação usr→name, eml→email, card→cardNumber... (contrato mantido) (PB-14)
F14 console.log           → logger com níveis (PB-14)
F15 Código morto          → totalRevenue, dbUser, dbPass, smtpUser removidos (PB-14)
F16 Magic                 → APPROVED_CARD_PREFIX, PAYMENT_STATUS, constantes do hasher (PB-14)
F17 Callback hell         → async/await (PB-15)
Deferred: autorização em DELETE /api/users/:id (exige modelo de autenticação)

## Contract changes
- GET /api/admin/financial-report exige X-Admin-Token (api.http atualizado)
- DELETE /api/users/:id remove matrículas/pagamentos e responde "Usuário deletado" (404 se não existir)
- card precisa ser string numérica (antes: número derrubava o processo)

## Validation
  ✓ Application boots without errors (npm start)
  ✓ All 8 baseline endpoints respond correctly (8/8)
  ✓ No remaining occurrences of fixed anti-patterns (console.log de cartão, globalCache, badCrypto, segredos)
================================
```

---

## Projeto 3 — task-manager-api

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python 3
Framework:     Flask 3.0.0
Dependencies:  flask-sqlalchemy 3.1.1, flask-cors 4.0.0, marshmallow 3.20.1 (não usado), requests 2.31.0 (não usado), python-dotenv 1.0.0 (não usado)
Database:      SQLite via SQLAlchemy ORM (sqlite:///tasks.db; seed por seed.py)
Domain:        Task Manager (tasks, usuários, categorias, relatórios de produtividade)
Architecture:  Camadas parciais — models/ (ORM), routes/ (blueprints com toda a lógica), services/ e utils/ não usados;
               sem controllers, config, error handler ou application factory
Entry point:   app.py (start: python seed.py && python app.py)
Source files:  15 files analyzed (~1160 lines)
DB tables:     users, tasks, categories
Endpoints:     22 (GET /, GET /health, GET|POST /tasks, GET|PUT|DELETE /tasks/<id>, GET /tasks/search, GET /tasks/stats,
               GET|POST /users, GET|PUT|DELETE /users/<id>, GET /users/<id>/tasks, POST /login,
               GET /reports/summary, GET /reports/user/<id>, GET|POST /categories, PUT|DELETE /categories/<id>)
================================
```

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure (estrutura existente preservada; novos módulos marcados com +)
app.py                       (application factory create_app + entry point)
seed.py
+ config/settings.py
database.py
+ errors.py
models/       task.py, user.py, category.py        (acesso a dados + regras da entidade)
+ controllers/ task_, user_, report_, category_controller.py
routes/       task_, user_, report_, + category_, + system_routes.py
services/     notification_service.py, + token_service.py
+ middlewares/error_handler.py
utils/        + validators.py, + time.py            (helpers.py removido: código morto)

## Findings addressed
F01 Credenciais hardcoded → config/settings.py (SECRET_KEY, SMTP_*) + .env.example (PB-01)
F02 MD5                   → werkzeug hash; MD5 legado verificado e migrado no login (PB-04)
F03 Hash exposto          → User.to_dict() sem password (PB-05)
F04 Lógica nas rotas      → controllers/ + rotas finas (PB-07)
F05 Token falso           → TokenService (itsdangerous, assinado, expira) (PB-05)
F06 Sem auth / escalada   → Deferred: exige política de autenticação (decisão de produto)
F07 Config insegura       → create_app(settings), debug off, host/porta/CORS via ambiente (PB-01, PB-08)
F08 N+1                   → joinedload; GROUP BY para contagens; atrasadas filtradas em SQL (PB-10)
F09 APIs deprecated       → utils/time.utcnow(); db.session.get(Model, id) (PB-13)
F10 Validação             → utils/validators.py com checagem de tipo (PB-11)
F11 Duplicação            → Task.is_overdue/to_dict únicos; constantes centralizadas (PB-11, PB-14)
F12 Erros                 → errors.py + middlewares/error_handler.py (envelope {"error"}, rollback) (PB-12)
F13 Categorias no lugar errado → routes/category_routes.py + CategoryController (PB-03)
F14 Código morto          → helpers.py e imports removidos; NotificationService ligado à atribuição de tasks (PB-14)
F15 print                 → logging (PB-14)
F16 Magic numbers         → config/settings.py (PB-14)
F17 Condicionais verbosas → expressões diretas (PB-15)

## Contract changes
- Respostas de usuário sem "password"; "token" do login agora é assinado (mesmo campo)

## Validation
  ✓ Application boots without errors (python seed.py && python app.py; sem warnings com -W default)
  ✓ All 29 baseline endpoints respond correctly (29/29) — JSON completo idêntico ao original em 21/21 requisições comparadas
  ✓ No remaining occurrences of fixed anti-patterns (datetime.utcnow, Query.get, except:, print, md5 em hash novo)
================================
```
