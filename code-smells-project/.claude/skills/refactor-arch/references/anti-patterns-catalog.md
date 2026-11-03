# Catálogo de Anti-patterns (Fase 2)

Cada entrada tem: **ID**, **severidade padrão**, **o que é**, **sinais de detecção** (padrões concretos de busca, por linguagem) e **playbook** (transformação correspondente em `refactoring-playbook.md`).

## Escala de severidade

| Nível | Critério |
|---|---|
| **CRITICAL** | Falha grave de segurança ou arquitetura: expõe dados sensíveis, permite execução arbitrária, credenciais no código, ou viola completamente a separação de responsabilidades (God Class com DB + regras + rotas). |
| **HIGH** | Violação forte de MVC/SOLID que dificulta muito manutenção e testes: regra de negócio presa em rotas/controllers, acoplamento sem DI, estado global mutável, escrita multi-etapa sem transação, configuração insegura. |
| **MEDIUM** | Padronização, duplicação, performance moderada: N+1, validação ausente/duplicada, tratamento de erro inadequado, APIs deprecated. |
| **LOW** | Legibilidade: magic numbers, nomes ruins, `print` como log, código morto, condicionais verbosas. |

Ajuste de nível só com justificativa no finding (ex.: N+1 em endpoint chamado a cada request de listagem pode subir para HIGH; SQL injection em script offline pode descer para HIGH).

## Como buscar

Use busca textual (`grep -rn`) com os padrões abaixo **e** leitura do arquivo para confirmar o contexto. Um match de regex não é finding até você confirmar a linha. Sempre reporte `arquivo:linha` ou `arquivo:linha_inicial-linha_final`.

---

## CRITICAL

### AP-01 — Hardcoded Credentials / Secrets
Segredos (chaves, senhas, tokens, API keys, connection strings com senha) escritos no código-fonte.
- **Python:** `SECRET_KEY\s*=\s*['"]`, `app.config\[['"]SECRET_KEY['"]\]\s*=\s*['"]`, `password\s*=\s*['"]`, `email_password`, `api_key\s*=\s*['"]`
- **JS/TS:** objetos `config = { ...Pass: "...", ...Key: "..." }`, `pk_live_`, `sk_live_`, `secret:\s*['"]`
- **Geral:** strings com `senha`, `secret`, `token`, `key`, `pwd`, `pass` atribuídas a literais; segredo **devolvido em resposta** (ex.: `health` retornando `secret_key`) agrava o finding.
- **Playbook:** PB-01.

### AP-02 — SQL Injection (query por concatenação/interpolação)
Entrada externa concatenada em SQL.
- **Python:** `execute\(\s*["'].*["']\s*\+`, `execute\(f["']`, `"... WHERE id = " + str(`, `% (` em SQL, `.format(` em SQL.
- **JS/TS:** template strings com `${` dentro de `SELECT|INSERT|UPDATE|DELETE`, `"... " + req.` em query.
- **Não é finding:** placeholders (`?`, `%s`, `:name`, `$1`) com parâmetros separados; métodos do ORM.
- **Playbook:** PB-02.

### AP-03 — God Class / God File
Um arquivo/classe concentra roteamento + regra de negócio + acesso a dados (+ config/validação/formatação) de vários domínios.
- **Sinais:** classe "Manager"/"Helper"/"App" com `initDb` + `setupRoutes` + SQL; arquivo `models.py` com SQL e regras de 3+ entidades; arquivo > ~300 linhas com 3+ responsabilidades (R/B/D/C/V/F/I, ver `project-analysis.md` §7); rotas definidas dentro de métodos de classe de dados.
- **Playbook:** PB-03.

### AP-04 — Armazenamento inseguro de senha
Senha em texto puro, hash rápido sem salt (MD5/SHA1/SHA256 puro) ou "criptografia" caseira (base64, loops).
- **Python:** `hashlib.md5(`, `hashlib.sha1(`, coluna `senha`/`password` inserida direto do request, comparação `senha = '...'` em SQL.
- **JS/TS:** `Buffer.from(pwd).toString('base64')`, funções tipo `badCrypto`, `createHash('md5'|'sha1')` em senha.
- **Playbook:** PB-04.

### AP-05 — Exposição de dados sensíveis
Senhas/hashes, segredos, números de cartão ou chaves retornados em respostas ou escritos em logs.
- **Sinais:** `to_dict()`/serializer incluindo `password`/`senha`; `SELECT *` de usuários devolvido sem filtrar; `console.log`/`print` com `card`, `cc`, `password`, chave de gateway; mensagens de erro com `str(e)` vazando SQL/stack para o cliente (agravante).
- **Playbook:** PB-05.

### AP-06 — Endpoint perigoso sem proteção
Endpoints administrativos ou destrutivos acessíveis sem autenticação/autorização: execução de SQL arbitrário, reset de banco, deleção em massa, relatórios financeiros.
- **Sinais:** rotas `/admin/*`, `cursor.execute(dados["sql"])`, `DELETE FROM <tabela>` sem `WHERE` em rota, ausência de qualquer verificação de identidade antes de ação destrutiva.
- **Playbook:** PB-06.

---

## HIGH

### AP-07 — Fat Controller / regra de negócio na camada HTTP
Handlers de rota que validam, calculam, consultam o banco e formatam resposta no mesmo bloco.
- **Sinais:** handler de rota com > ~30 linhas; `Model.query`/SQL dentro da função decorada com `@route`/`app.post`; cálculos de domínio (descontos, status, totais, "overdue") no handler; notificações disparadas da rota.
- **Playbook:** PB-07.

### AP-08 — Estado global mutável / singleton de conexão compartilhada
Variáveis de módulo modificadas em runtime e compartilhadas entre requests/threads.
- **Python:** `global <nome>` em funções; conexão única `sqlite3.connect(..., check_same_thread=False)` guardada em variável global.
- **JS/TS:** `let cache = {}` / `let total = 0` exportados e mutados; objetos singletons mutáveis exportados.
- **Playbook:** PB-08.

### AP-09 — Acoplamento forte / ausência de injeção de dependência
Camadas importam e instanciam concretamente suas dependências (banco, gateways, serviços), impossibilitando substituição em testes.
- **Sinais:** `get_db()` global chamado dentro de cada função de model; `new Database()` no construtor da classe de domínio; serviço instanciado dentro do handler; controllers importando o módulo de conexão diretamente.
- **Playbook:** PB-08 (composition root) + PB-07.

### AP-10 — Escrita multi-etapa sem transação / integridade referencial quebrada
Operações que fazem vários `INSERT/UPDATE/DELETE` relacionados sem transação, ou deleções que deixam registros órfãos.
- **Sinais:** sequência de `execute`/`db.run` com `commit` só no final mas sem `rollback` em erro; `return` no meio de um loop de escrita; `DELETE FROM users` sem tratar `enrollments`/`payments`; ausência de `FOREIGN KEY`/cascade.
- **Playbook:** PB-09.

### AP-11 — Configuração insegura para produção
`debug=True` fixo, `DEBUG = True` em config, servidor de desenvolvimento exposto em `0.0.0.0` com debug, CORS liberado para qualquer origem sem configuração.
- **Sinais:** `app.run(debug=True`, `app.config["DEBUG"] = True`, `CORS(app)` sem `origins`.
- **Playbook:** PB-01.

### AP-12 — Autenticação falsa / token previsível
Tokens de sessão não assinados ou derivados de dados previsíveis.
- **Sinais:** `'fake-jwt-token-' + str(user.id)`, token = id/email em base64, ausência de assinatura/expiração.
- **Playbook:** PB-05 (seção token assinado).

---

## MEDIUM

### AP-13 — Queries N+1 / consultas redundantes
Consulta ao banco dentro de loop sobre resultado de outra consulta; múltiplas consultas de contagem que poderiam ser um `GROUP BY`.
- **Python:** `for ... in rows:` seguido de `cursor.execute(`/`Model.query.get(`/`.filter_by(` no corpo; acesso a relationship lazy (`len(u.tasks)`) em loop; sequência de `.filter_by(status=...).count()` para cada valor.
- **JS/TS:** `forEach`/`for` com `db.get`/`db.all`/`await repo.find` dentro; callbacks aninhados por registro.
- **Playbook:** PB-10.

### AP-14 — Validação ausente, inconsistente ou duplicada
Entrada não validada (tipos, faixas, obrigatórios) ou a mesma validação copiada em vários handlers.
- **Sinais:** `dados["campo"]` sem checagem; `priority < 1` sem validar tipo (`TypeError` vira 500); blocos `if "nome" not in dados` repetidos entre create/update; regex de e-mail repetida; listas de status válidos repetidas; função de validação existente e não usada.
- **Playbook:** PB-11.

### AP-15 — Duplicação de lógica de domínio (DRY)
Mesma regra implementada em vários lugares (ex.: cálculo de "atrasado" repetido em 5 handlers ignorando `Task.is_overdue()`; mapeamento row→dict copiado em toda função).
- **Sinais:** blocos de 5+ linhas idênticos ou quase; método de model existente reimplementado inline.
- **Playbook:** PB-11 / PB-03.

### AP-16 — Tratamento de erro inadequado
`except:` nu, `except Exception` que engole o erro, `str(e)` devolvido ao cliente, `try/except` copiado em todo handler, callbacks que ignoram `err`, ausência de handler central (404/500 em formatos diferentes).
- **Python:** `except:\s*$`, `except Exception as e:\s*return jsonify\({"erro": str\(e\)`.
- **JS/TS:** `(err) => {` sem uso de `err`; `if (err) return res.status(500).send(...)` repetido; ausência de middleware `(err, req, res, next)`.
- **Playbook:** PB-12.

### AP-17 — Uso de APIs deprecated
Chamadas marcadas como obsoletas pela linguagem/biblioteca na versão em uso. Sempre informe a API moderna equivalente.

| Stack | API deprecated | Equivalente moderno | Desde |
|---|---|---|---|
| Python ≥ 3.12 | `datetime.utcnow()` / `datetime.utcfromtimestamp()` | `datetime.now(timezone.utc)` (ou `.replace(tzinfo=None)` se o banco guarda naive UTC) | 3.12 |
| Python ≥ 3.12 | adaptadores padrão de data do `sqlite3` | adaptadores explícitos / ISO strings | 3.12 |
| SQLAlchemy ≥ 2.0 | `Model.query.get(id)` / `Query.get()` | `db.session.get(Model, id)` | 2.0 |
| SQLAlchemy ≥ 2.0 | `engine.execute()`, `session.query(...)` em código novo | `session.execute(select(...))` | 2.0 |
| Flask ≥ 2.3 | `@app.before_first_request`, `app.config['ENV']`, `FLASK_ENV`, `flask.json.JSONEncoder` | inicialização no factory, `--debug`, `app.json` provider | 2.3 |
| Werkzeug ≥ 2.1 | `safe_str_cmp` | `hmac.compare_digest` | 2.1 |
| Node | `new Buffer(x)` | `Buffer.from(x)` / `Buffer.alloc(n)` | 6+ |
| Node | `url.parse()` | `new URL()` | 11+ |
| Node | `fs.exists()` | `fs.existsSync()` / `fs.promises.access()` | 1+ |
| Node | `crypto.createCipher()` | `crypto.createCipheriv()` | 10+ |
| Express 4 | `req.param()`, `res.send(status, body)`, `res.json(status, obj)`, pacote `body-parser` separado | `req.params/query/body`, `res.status(s).send()`, `express.json()` | 4.x |

- **Confirmação em runtime:** `python -W default app.py` / `node --trace-deprecation app.js` e exercitar os endpoints.
- Se nenhuma API deprecated for encontrada, declarar no relatório: "Deprecated APIs: none detected (checked: <lista>)".
- **Playbook:** PB-13.

### AP-18 — Efeitos colaterais acoplados ao fluxo HTTP
Envio de e-mail/SMS/push, cache e auditoria executados inline no handler (geralmente via `print`), sem abstração de serviço.
- **Sinais:** `print("ENVIANDO EMAIL...")` em controller; `smtplib` instanciado na rota; `logAndCache` chamado no meio do callback de pagamento.
- **Playbook:** PB-07 (extrair service) + PB-08.

---

## LOW

### AP-19 — Magic numbers / strings
Literais com significado de negócio espalhados: limites de desconto (`10000`, `0.1`), faixas de prioridade (`1..5`), listas de status/categorias/roles, porta, tamanho mínimo de senha.
- **Sinais:** números ≠ 0/1 em condicionais de regra de negócio; listas literais repetidas.
- **Playbook:** PB-14.

### AP-20 — Nomenclatura ruim
Identificadores de 1–3 letras fora de loops curtos (`u`, `e`, `p`, `cid`, `cc`), nomes que mentem (`badCrypto`, `AppManager`), mistura de idiomas/convenções.
- **Playbook:** PB-14. *Contrato de API (nomes de campos JSON) não muda — renomeie só variáveis internas.*

### AP-21 — `print`/`console.log` como logging
Logs sem nível, sem estrutura, e às vezes com dado sensível.
- **Sinais:** `print(` / `console.log(` em código de aplicação (fora de scripts CLI como seed).
- **Playbook:** PB-14.

### AP-22 — Código morto / imports não usados
Imports, variáveis, funções e constantes nunca referenciados; funções utilitárias reimplementadas em outro lugar.
- **Sinais:** `import os, sys, json` sem uso; constantes definidas e ignoradas; export de variável nunca lida (`totalRevenue`).
- **Ferramentas:** `python -m pyflakes`, `npx eslint --rule no-unused-vars:error` (se disponíveis); senão busca manual por cada nome importado.
- **Playbook:** PB-14.

### AP-23 — Condicionais verbosas / aninhamento excessivo
`if cond: return True else: return False`; 3+ níveis de `if` aninhados para uma regra simples; callback hell (4+ níveis) em JS.
- **Playbook:** PB-15.

---

## Checklist de cobertura da auditoria

Antes de fechar o relatório, confirme que verificou explicitamente: AP-01, AP-02, AP-04, AP-05, AP-06 (segurança) · AP-03, AP-07, AP-08, AP-09, AP-10 (arquitetura) · AP-13 (performance) · AP-17 (deprecated) · AP-14/15/16 (qualidade) · AP-19–23 (legibilidade).
