================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python 3 + Flask 3.0.0 (Flask-SQLAlchemy 3.1.1 / SQLAlchemy 2.x, SQLite, flask-cors 4.0.0)
Files:   15 analyzed | ~1160 lines of code
Date:    2026-11-03

## Summary
CRITICAL: 3 | HIGH: 4 | MEDIUM: 6 | LOW: 4

## Findings

### F01 [CRITICAL] Credenciais hardcoded
Catalog: AP-01
File: app.py:13
      services/notification_service.py:7-10
Description: `SECRET_KEY = 'super-secret-key-123'` e as credenciais SMTP (`email_user = 'taskmanager@gmail.com'`, `email_password = 'senha123'`) estão no código-fonte.
Impact: Quem lê o repositório obtém a chave de assinatura da aplicação e acesso à conta de e-mail.
Recommendation: `config/settings.py` lendo `SECRET_KEY`, `SMTP_*` do ambiente; serviço recebe a config por injeção (PB-01).

### F02 [CRITICAL] Hash de senha com MD5 sem salt
Catalog: AP-04
File: models/user.py:27-32
Description: `set_password` usa `hashlib.md5(pwd.encode()).hexdigest()`; `check_password` compara com `==`.
Impact: MD5 sem salt é revertido por rainbow tables em segundos (ex.: o hash de `1234` do seed é público); comparação não é constant-time.
Recommendation: `werkzeug.security.generate_password_hash/check_password_hash`, com migração transparente dos hashes MD5 no próximo login (PB-04).

### F03 [CRITICAL] Hash de senha exposto nas respostas
Catalog: AP-05
File: models/user.py:16-25
      routes/user_routes.py:33
      routes/user_routes.py:85
      routes/user_routes.py:129
      routes/user_routes.py:209
Description: `User.to_dict()` inclui `password`, e é usado em `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e `POST /login`.
Impact: Combinado com F02, qualquer cliente obtém o hash MD5 de qualquer usuário e recupera a senha. Confirmado em execução.
Recommendation: Remover `password` de `to_dict()` (PB-05).

### F04 [HIGH] Regras de negócio, validação e queries dentro das rotas (sem camada de controller)
Catalog: AP-07
File: routes/task_routes.py:11-63
      routes/task_routes.py:85-154
      routes/task_routes.py:156-223
      routes/user_routes.py:42-90
      routes/user_routes.py:92-132
      routes/report_routes.py:12-101
      routes/report_routes.py:103-155
Description: O projeto tem `models/`, `routes/`, `services/` e `utils/`, mas toda a lógica vive nas rotas: validação campo a campo, consultas ORM, cálculo de "atrasada", estatísticas e serialização manual. `services/` e `utils/` existem mas não são usados (ver F14).
Impact: Rotas de 50–90 linhas, impossíveis de testar sem request HTTP; a separação de pastas é só aparente.
Recommendation: Introduzir `controllers/` (task, user, report, category) com o fluxo e as regras; rotas viram adaptadores HTTP finos (PB-07).

### F05 [HIGH] Token de autenticação falso e previsível
Catalog: AP-12
File: routes/user_routes.py:210
Description: O login devolve `'fake-jwt-token-' + str(user.id)` — sem assinatura nem expiração.
Impact: Qualquer cliente fabrica o token de qualquer usuário trocando o número.
Recommendation: Token assinado e com expiração via `itsdangerous` (já é dependência do Flask), mantendo o campo `token` (PB-05).

### F06 [HIGH] Ausência de autenticação/autorização e escalada de privilégio
Catalog: AP-06
File: routes/user_routes.py:52
      routes/user_routes.py:71-72
      routes/user_routes.py:119-122
      routes/user_routes.py:134-151
Description: Nenhuma rota exige identificação. O `role` vem do corpo do `POST /users`, então qualquer cliente cria um usuário `admin` (confirmado em execução); qualquer cliente altera papéis ou apaga usuários com todas as suas tasks.
Impact: O campo `role` não protege nada; dados podem ser apagados anonimamente.
Recommendation: Definir política de autenticação (token do F05 + checagem de papel) para rotas de escrita. Exige decisão de produto sobre quem pode fazer o quê — registrar como **Deferred** na Fase 3, sem quebrar os clientes atuais.

### F07 [HIGH] Configuração insegura e acoplada ao código
Catalog: AP-11
File: app.py:11
      app.py:15
      app.py:34
      app.py:30-31
Description: `debug=True` com `host='0.0.0.0'`, CORS liberado para qualquer origem, URI do banco fixa no código e `db.create_all()` executado no import do módulo (sem application factory).
Impact: Debugger do Werkzeug exposto na rede (execução remota de código); impossível criar a app com outra config para testes.
Recommendation: Application factory `create_app(settings)` com config do ambiente e defaults seguros (PB-01, PB-08).

### F08 [MEDIUM] Queries N+1 e contagens redundantes
Catalog: AP-13
File: routes/task_routes.py:41-57
      routes/task_routes.py:275-287
      routes/user_routes.py:12-24
      routes/report_routes.py:15-28
      routes/report_routes.py:53-68
      routes/report_routes.py:157-165
Description: `GET /tasks` faz 2 queries extras por task (usuário e categoria); `GET /users` dispara o lazy-load de `u.tasks` por usuário; o resumo faz 13 `count()` separados + 1 query por usuário; `GET /categories` faz 1 `count()` por categoria; `/tasks/stats` carrega todas as tasks em memória para contar as atrasadas.
Impact: O número de queries cresce com o volume de dados em todos os endpoints de listagem e relatório.
Recommendation: `joinedload` para relações; `GROUP BY` com `func.count`/`case` para as contagens; filtro de atrasadas em SQL (PB-10).

### F09 [MEDIUM] Uso de APIs deprecated
Catalog: AP-17
File: models/task.py:15-16
      models/task.py:52
      models/user.py:14
      models/category.py:11
      routes/task_routes.py:31
      routes/task_routes.py:42
      routes/task_routes.py:51
      routes/task_routes.py:67
      routes/user_routes.py:29
      routes/report_routes.py:35
      utils/helpers.py:38
      seed.py:66-74
Description: `datetime.utcnow()` (deprecated no Python 3.12) em 22 pontos e `Model.query.get()` (legado no SQLAlchemy 2.0, emite `LegacyAPIWarning`) em 16 pontos — lista completa na seção Deprecated APIs. Confirmado com `python -W default app.py`.
Impact: Avisos a cada request hoje; quebra quando as APIs forem removidas.
Recommendation: Helper `utcnow()` (UTC naive, compatível com o que o SQLite guarda) e `db.session.get(Model, id)` (PB-13).

### F10 [MEDIUM] Validação ausente ou incompleta gerando erro 500
Catalog: AP-14
File: routes/task_routes.py:113
      routes/task_routes.py:182
      routes/task_routes.py:261
      routes/task_routes.py:264
      routes/task_routes.py:166-170
      routes/report_routes.py:177-180
      routes/report_routes.py:196-202
      routes/user_routes.py:124-125
Description: `priority` não tem o tipo verificado (`"priority": "2"` → `TypeError` → 500, confirmado); `int(priority)`/`int(user_id)` na busca → `ValueError` → 500 (confirmado com `?priority=abc`); `title` não string quebra `len()`; cor de categoria não é validada (`is_valid_color` existe e não é usado); `active` aceita qualquer tipo.
Impact: Entrada inválida vira erro interno e dados inconsistentes no banco.
Recommendation: Validadores únicos em `utils/validators.py` que checam tipo e faixa, usados por create e update (PB-11).

### F11 [MEDIUM] Lógica de domínio duplicada
Catalog: AP-15
File: routes/task_routes.py:30-39
      routes/task_routes.py:71-80
      routes/task_routes.py:283-287
      routes/user_routes.py:171-180
      routes/report_routes.py:33-43
      routes/report_routes.py:132-135
      routes/task_routes.py:17-28
      routes/user_routes.py:61
      routes/user_routes.py:106
      routes/task_routes.py:110
      routes/task_routes.py:177
Description: A regra "task atrasada" é reescrita 6 vezes, ignorando `Task.is_overdue()` (models/task.py:50-60); a serialização da task é copiada à mão em vez de usar `to_dict()`; a regex de e-mail e a lista de status aparecem repetidas (e também em `utils/helpers.py`, sem uso).
Impact: Alterar uma regra exige caçar cópias; as cópias já divergem (mensagens de erro diferentes entre create e update).
Recommendation: A regra fica no model (`Task.is_overdue`), a serialização em `to_dict`, validação e constantes em um lugar só (PB-11, PB-14).

### F12 [MEDIUM] Tratamento de erros inadequado
Catalog: AP-16
File: routes/task_routes.py:62
      routes/task_routes.py:137
      routes/task_routes.py:204
      routes/task_routes.py:236
      routes/user_routes.py:130
      routes/user_routes.py:149
      routes/report_routes.py:186
      routes/report_routes.py:207
      routes/report_routes.py:221
      utils/helpers.py:46
      utils/helpers.py:49
      utils/helpers.py:88
Description: 12 `except:` nus engolem qualquer exceção (inclusive `KeyboardInterrupt`/`SystemExit`); não há error handler central — erros não tratados viram páginas HTML 500 enquanto o resto da API responde JSON.
Impact: Bugs mascarados e respostas de erro inconsistentes para os clientes.
Recommendation: Exceções de domínio + `register_error_handlers` com envelope `{"error": ...}`; rollback de sessão no handler (PB-12).

### F13 [MEDIUM] Responsabilidade no módulo errado (coesão)
Catalog: AP-03 (rebaixado a MEDIUM: o projeto já tem camadas; o problema é localizado)
File: routes/report_routes.py:157-223
Description: O CRUD completo de categorias está dentro do blueprint de relatórios (`report_bp`).
Impact: Quem procura as rotas de categoria não as encontra; mudanças em relatórios e categorias se misturam.
Recommendation: Blueprint e controller próprios para categorias (PB-03).

### F14 [LOW] Código morto e imports não usados
Catalog: AP-22
File: app.py:7
      routes/task_routes.py:7
      routes/user_routes.py:6
      routes/report_routes.py:7-8
      models/task.py:3
      models/task.py:38-48
      utils/helpers.py:2-7
      utils/helpers.py:9-116
      services/notification_service.py:4-48
Description: `os`, `sys`, `json`, `time`, `hashlib`, `math` importados sem uso; `Task.validate_status/validate_priority` nunca chamados; quase todo `utils/helpers.py` (validações, `process_task_data`, constantes) nunca é usado; `NotificationService` não é instanciado em lugar nenhum.
Impact: Falsa impressão de que existem validação e notificações centralizadas; ruído na leitura.
Recommendation: Remover o que não tem uso, e passar a usar de fato o que deveria ser central (validações, notificação) (PB-14).

### F15 [LOW] `print` como logging
Catalog: AP-21
File: routes/task_routes.py:149
      routes/task_routes.py:153
      routes/task_routes.py:219
      routes/task_routes.py:234
      routes/user_routes.py:83
      routes/user_routes.py:89
      routes/user_routes.py:147
      services/notification_service.py:21
      services/notification_service.py:24
      utils/helpers.py:39-41
Description: Logs via `print`, sem nível.
Impact: Logs não filtráveis em produção.
Recommendation: `logging` (PB-14).

### F16 [LOW] Magic numbers e strings
Catalog: AP-19
File: routes/task_routes.py:96-100
      routes/task_routes.py:113
      routes/user_routes.py:64
      routes/user_routes.py:115
      routes/user_routes.py:71
      routes/report_routes.py:45
      routes/report_routes.py:129
      routes/report_routes.py:180
Description: Limites de título (`3`, `200`), faixa de prioridade (`1`–`5`), senha mínima (`4`), roles, janela de 7 dias, "alta prioridade" (`<= 2`), cor padrão `#000000` espalhados como literais (as constantes de `utils/helpers.py:110-116` existem e não são usadas).
Impact: Regras de negócio escondidas e duplicadas.
Recommendation: Constantes em `config/settings.py` (PB-14).

### F17 [LOW] Condicionais verbosas
Catalog: AP-23
File: models/user.py:34-38
      models/task.py:38-60
      routes/task_routes.py:30-39
Description: `if cond: return True else: return False` e 3 níveis de `if` aninhados para uma expressão booleana.
Impact: Leitura mais lenta, mais superfície para erro.
Recommendation: Retornar a expressão diretamente (PB-15).

## Deprecated APIs
| API | Location | Modern replacement |
|---|---|---|
| `datetime.utcnow()` (Python 3.12) | models/task.py:15, 16, 52 · models/user.py:14 · models/category.py:11 · routes/task_routes.py:31, 72, 215, 285 · routes/user_routes.py:172 · routes/report_routes.py:35, 42, 45, 71, 133 · utils/helpers.py:38 · services/notification_service.py:35 · seed.py:66, 67, 69, 70, 74 | `datetime.now(timezone.utc)` (`.replace(tzinfo=None)` para manter UTC naive no SQLite) |
| `Model.query.get()` (SQLAlchemy 2.0, `LegacyAPIWarning`) | routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227 · routes/user_routes.py:29, 94, 136, 155 · routes/report_routes.py:105, 192, 213 | `db.session.get(Model, id)` |

## Architecture Notes
Projeto com camadas parciais: `models/` é razoável (ORM com relationships), mas `routes/` concentra validação, regras, queries e serialização, enquanto `services/` e `utils/` são código morto. Não há controllers, config, error handler nem application factory. A refatoração proposta preserva a organização de pastas existente (sem mover tudo para `src/`), adiciona `config/`, `controllers/`, `middlewares/` e `errors.py`, transforma `app.py` em application factory, cria um blueprint próprio para categorias, corrige os models (hash, `to_dict`, `is_overdue`) e liga o `NotificationService` via injeção, com SMTP configurável.

================================
Total: 17 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y
