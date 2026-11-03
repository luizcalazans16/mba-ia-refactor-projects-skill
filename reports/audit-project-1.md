================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python 3 + Flask 3.1.1 (sqlite3 driver cru, flask-cors 5.0.1)
Files:   4 analyzed | ~780 lines of code
Date:    2026-11-03

## Summary
CRITICAL: 6 | HIGH: 5 | MEDIUM: 5 | LOW: 4

## Findings

### F01 [CRITICAL] SQL Injection
Catalog: AP-02
File: models.py:28
      models.py:47-50
      models.py:57-61
      models.py:68
      models.py:92
      models.py:109-111
      models.py:126-129
      models.py:140
      models.py:148-151
      models.py:155-166
      models.py:174
      models.py:188
      models.py:192
      models.py:220
      models.py:224
      models.py:279-281
      models.py:289-297
Description: Praticamente todas as queries concatenam valores do request na string SQL (`"SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"`, `" AND (nome LIKE '%" + termo + "%' ..."`).
Impact: Confirmado em execução: `POST /login` com `email = x' OR '1'='1` e `senha = x' OR '1'='1` autentica como o usuário Admin. Qualquer campo de texto permite ler, alterar ou apagar dados.
Recommendation: Placeholders `?` com parâmetros em todas as queries; montar filtros dinâmicos com lista de cláusulas fixas + lista de parâmetros (PB-02).

### F02 [CRITICAL] Endpoints administrativos destrutivos sem proteção
Catalog: AP-06
File: app.py:47-57
      app.py:59-78
Description: `POST /admin/reset-db` apaga todas as tabelas e `POST /admin/query` executa **qualquer SQL** recebido no corpo (`cursor.execute(query)`), ambos sem autenticação.
Impact: Qualquer cliente pode destruir o banco ou extrair todas as senhas (`SELECT * FROM usuarios`) com uma requisição.
Recommendation: Desabilitar por padrão e exigir token de administrador vindo do ambiente (`X-Admin-Token` comparado com `hmac.compare_digest`); restringir `/admin/query` a um único `SELECT` (PB-06).

### F03 [CRITICAL] Credenciais hardcoded
Catalog: AP-01
File: app.py:7
      controllers.py:289
Description: `SECRET_KEY` fixo como `'minha-chave-super-secreta-123'` no código, e repetido literalmente na resposta do health check.
Impact: Chave versionada no git permite forjar sessões/assinaturas; trocar a chave exige deploy de código.
Recommendation: Módulo `config/settings.py` lendo `SECRET_KEY` do ambiente (chave efêmera aleatória em dev) (PB-01).

### F04 [CRITICAL] Senhas armazenadas e comparadas em texto puro
Catalog: AP-04
File: database.py:75-83
      models.py:122-131
      models.py:109-111
Description: O seed grava `admin123`, `123456`, `senha123` em claro; `criar_usuario` insere a senha recebida sem hash; o login compara a senha dentro do SQL.
Impact: Qualquer vazamento (ver F02, F05) expõe as senhas reais dos clientes, que costumam ser reutilizadas em outros serviços.
Recommendation: `werkzeug.security.generate_password_hash`/`check_password_hash` (já instalado com Flask); login busca por e-mail e verifica o hash em código (PB-04).

### F05 [CRITICAL] Exposição de dados sensíveis nas respostas
Catalog: AP-05
File: models.py:83
      models.py:99
      controllers.py:285-289
Description: `GET /usuarios` e `GET /usuarios/<id>` devolvem o campo `senha`; `GET /health` devolve `secret_key`, `debug`, `db_path` e `ambiente`.
Impact: Senhas de todos os usuários e a chave da aplicação ficam públicas para qualquer cliente.
Recommendation: Remover `senha` dos dicionários de usuário e os campos internos do health check (PB-05).

### F06 [CRITICAL] God File — `models.py` concentra dados e regras de 4 domínios
Catalog: AP-03
File: models.py:1-314
      app.py:1-88
Description: Um único arquivo contém SQL, mapeamento row→dict, validação de estoque, cálculo de total do pedido, regras de desconto do relatório e busca, para produtos, usuários, pedidos e relatórios. `app.py` mistura roteamento, endpoints administrativos com SQL e bootstrap.
Impact: Impossível testar regras isoladamente; qualquer mudança em um domínio toca o arquivo de todos; não há onde colocar uma regra nova sem aumentar o acoplamento.
Recommendation: Separar em `src/models/<entidade>_model.py`, `src/controllers/<dominio>_controller.py`, `src/views/<dominio>_routes.py` e composition root `src/app.py` (PB-03).

### F07 [HIGH] Camada HTTP misturada com o fluxo da aplicação
Catalog: AP-07
File: controllers.py:1-292
Description: Cada função de `controllers.py` lê `request`, valida, chama o model, imprime notificações e monta `jsonify` com status — não há separação entre View (rota/serialização) e Controller (fluxo). `health_check` executa SQL direto (controllers.py:264-292).
Impact: Regras não podem ser reutilizadas nem testadas sem um request Flask; o mesmo bloco `try/except`/`jsonify` se repete em 17 funções.
Recommendation: Views finas em `src/views/` e controllers sem dependência de Flask, que recebem dados puros e lançam exceções de domínio (PB-07).

### F08 [HIGH] Conexão global mutável compartilhada entre threads
Catalog: AP-08
File: database.py:4-10
Description: `db_connection` global criada uma única vez com `check_same_thread=False` e reutilizada por todas as requisições/threads; o caminho do banco é fixo (`db_path = "loja.db"`).
Impact: Requisições concorrentes compartilham o mesmo cursor/transação (commits e leituras se misturam); impossível apontar para outro banco em testes.
Recommendation: Conexão por requisição via `flask.g` + `teardown_appcontext`, caminho vindo da config (PB-08).

### F09 [HIGH] Acoplamento forte sem injeção de dependência
Catalog: AP-09
File: models.py:1
      models.py:5
      controllers.py:2-3
      controllers.py:266
      app.py:3-4
Description: Cada função de model chama o `get_db()` global; controllers importam o módulo `models` e o banco diretamente; `app.py` importa o módulo `controllers` inteiro.
Impact: Não há como substituir banco ou serviços por dublês em testes; dependências implícitas escondem o fluxo.
Recommendation: Composition root (`create_app`) cria models/serviços e os injeta nos controllers (PB-08).

### F10 [HIGH] Criação de pedido sem transação
Catalog: AP-10
File: models.py:133-169
Description: `criar_pedido` insere o pedido, os itens e baixa o estoque em várias instruções sem tratamento de erro/rollback; a validação acessa `item["produto_id"]`/`item["quantidade"]` sem checar o formato.
Impact: Uma falha no meio do loop deixa pedido sem itens ou estoque baixado parcialmente; payload malformado vira erro 500.
Recommendation: Validar tudo antes e executar as escritas dentro de `with db:` (commit/rollback atômico) (PB-09).

### F11 [HIGH] Configuração insegura para produção
Catalog: AP-11
File: app.py:8
      app.py:9
      app.py:88
Description: `DEBUG = True` fixo, `app.run(host="0.0.0.0", debug=True)` e `CORS(app)` liberado para qualquer origem.
Impact: O debugger do Werkzeug exposto em 0.0.0.0 permite execução remota de código; stack traces vazam.
Recommendation: `FLASK_DEBUG`, `HOST`, `PORT` e `CORS_ORIGINS` via ambiente com defaults seguros (PB-01).

### F12 [MEDIUM] Queries N+1 e consultas redundantes
Catalog: AP-13
File: models.py:171-201
      models.py:203-233
      models.py:239-254
Description: Para cada pedido é feita uma query de itens e, para cada item, uma query do nome do produto (1 + N + N·M queries). O relatório de vendas executa 5 queries separadas de contagem/soma.
Impact: Listagem de pedidos degrada linearmente com o volume; relatório faz trabalho redundante.
Recommendation: Duas queries com `LEFT JOIN produtos` e agrupamento em memória; relatório com uma query de agregação (`COUNT`, `SUM`, `SUM(CASE ...)`) (PB-10).

### F13 [MEDIUM] Validação ausente, inconsistente e duplicada
Catalog: AP-14
File: controllers.py:26-54
      controllers.py:66-90
      controllers.py:169-170
      controllers.py:239-240
      models.py:139-146
Description: Criação e atualização de produto duplicam as checagens, mas a atualização não valida tamanho do nome nem categoria; tipos não são checados (`"preco": "abc"` → `TypeError` → 500); `login` e `atualizar_status_pedido` chamam `.get` em `None` quando o corpo não é JSON; itens do pedido não são validados.
Impact: Entradas inválidas viram 500 ou gravam dados inconsistentes (produto com categoria inválida via PUT).
Recommendation: Um validador por payload em `src/utils/validators.py`, reutilizado por create/update, checando tipo e faixa (PB-11).

### F14 [MEDIUM] Tratamento de erro repetido e vazando detalhes internos
Catalog: AP-16
File: controllers.py:10-12
      controllers.py:21-22
      controllers.py:60-62
      controllers.py:218-220
      controllers.py:291-292
      app.py:77-78
Description: Todas as 17 funções têm `try/except Exception as e: return jsonify({"erro": str(e)}), 500` (exemplos listados); não há handler central.
Impact: Mensagens do SQLite/Python (estrutura de tabelas, queries) vão para o cliente; formato de erro difícil de manter consistente.
Recommendation: Hierarquia `AppError` + `register_error_handlers` preservando o envelope `{"erro": ..., "sucesso": false}` (PB-12).

### F15 [MEDIUM] Duplicação de mapeamento e de funções inteiras
Catalog: AP-15
File: models.py:12-21
      models.py:31-40
      models.py:304-313
      models.py:79-86
      models.py:95-102
      models.py:171-201
      models.py:203-233
Description: O dicionário de produto (8 campos) é copiado 3 vezes, o de usuário 2 vezes, e `get_pedidos_usuario`/`get_todos_pedidos` são cópias quase idênticas.
Impact: Adicionar um campo exige editar vários lugares; divergências silenciosas.
Recommendation: Um mapeador por entidade e uma função de listagem de pedidos com filtro opcional (PB-03).

### F16 [MEDIUM] Efeitos colaterais (notificações) embutidos no handler
Catalog: AP-18
File: controllers.py:208-210
      controllers.py:247-250
Description: "Envio" de e-mail, SMS e push e notificações de status são `print` dentro do handler HTTP.
Impact: Não há como trocar por uma integração real nem desligar em testes; regra de notificação misturada ao fluxo HTTP.
Recommendation: `NotificationService` injetado no controller de pedidos (PB-07, PB-08).

### F17 [LOW] Magic numbers e listas literais
Catalog: AP-19
File: models.py:256-262
      controllers.py:47-54
      controllers.py:242
      app.py:88
Description: Faixas de desconto (`10000`, `5000`, `1000`, `0.1`, `0.05`, `0.02`), limites de nome (`2`, `200`), lista de categorias, lista de status e porta `5000` como literais.
Impact: Regra de negócio escondida no meio do código; mudar uma faixa exige caçar literais.
Recommendation: Constantes nomeadas em `src/config/settings.py` (PB-14).

### F18 [LOW] `print` usado como logging
Catalog: AP-21
File: controllers.py:8
      controllers.py:11
      controllers.py:57
      controllers.py:61
      controllers.py:106
      controllers.py:161
      controllers.py:179
      controllers.py:182
      controllers.py:219
      app.py:56
      app.py:83-86
Description: Logs via `print` sem nível nem contexto (inclui e-mails de usuários em tentativas de login).
Impact: Impossível filtrar/encaminhar logs em produção.
Recommendation: `logging.getLogger(__name__)` com níveis (PB-14).

### F19 [LOW] Imports não usados e código redundante
Catalog: AP-22
File: models.py:2
      database.py:2
      controllers.py:268
Description: `import sqlite3` em `models.py` e `import os` em `database.py` não são usados; `health_check` executa `SELECT 1` e descarta o resultado antes das contagens.
Impact: Ruído e falsa impressão de dependências.
Recommendation: Remover (PB-14).

### F20 [LOW] Nomenclatura ruim
Catalog: AP-20
File: controllers.py:56
      models.py:24
      models.py:187-193
Description: Variável/parâmetro `id` sombreando o builtin; cursores `cursor2`, `cursor3`; `prod`, `dados` genéricos.
Impact: Leitura mais difícil e risco de bugs por sombreamento.
Recommendation: Nomes descritivos (`produto_id`, `itens_cursor`) (PB-14).

## Deprecated APIs
None detected (checked: Flask 3.1 APIs usadas — `add_url_rule`, `jsonify`, `request.get_json`; `sqlite3` sem `detect_types`, portanto sem adaptadores de data deprecated; execução com `python -W default app.py` exercitando todos os endpoints não emitiu DeprecationWarning).

## Architecture Notes
Monolito em 4 arquivos sem separação de camadas: `models.py` é um God File com SQL e regras de 4 domínios, `controllers.py` mistura HTTP com fluxo e `app.py` mistura rotas, SQL administrativo e bootstrap, tudo sobre uma conexão global. A refatoração proposta cria `src/` com config, database (conexão por request), models por entidade, controllers sem Flask, views em blueprints, services (notificação/senha), error handler central e `create_app()` como composition root; `app.py` da raiz vira um entry point fino que mantém `python app.py`.

================================
Total: 20 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y
