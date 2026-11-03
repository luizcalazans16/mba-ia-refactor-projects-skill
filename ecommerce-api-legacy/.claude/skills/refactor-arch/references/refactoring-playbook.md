# Playbook de Refatoração (Fase 3)

Cada padrão (PB-xx) resolve um ou mais anti-patterns do catálogo (AP-xx). Os exemplos mostram Python/Flask e Node/Express; para outras stacks aplique a mesma ideia com o idioma local.

Ordem recomendada: PB-01 → PB-02/04/05/06 → PB-03/08 → PB-07/09/10 → PB-11/12 → PB-13/14/15.

---

## PB-01 — Extrair configuração e segredos para módulo de config (AP-01, AP-11)

**Antes**
```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.config["DEBUG"] = True
app.run(host="0.0.0.0", port=5000, debug=True)
```
**Depois** — `src/config/settings.py`
```python
import os, secrets

def _bool(name, default=False):
    return os.environ.get(name, str(default)).lower() in ("1", "true", "yes")

class Settings:
    def __init__(self):
        self.SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)  # efêmera em dev
        self.DEBUG = _bool("FLASK_DEBUG", False)
        self.HOST = os.environ.get("HOST", "127.0.0.1")
        self.PORT = int(os.environ.get("PORT", "5000"))
        self.DATABASE_PATH = os.environ.get("DATABASE_PATH", "loja.db")
        self.CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")
```
```python
# app.py (raiz) — entry point fino
from src.app import create_app
app = create_app()
if __name__ == "__main__":
    s = app.config["SETTINGS"]
    app.run(host=s.HOST, port=s.PORT, debug=s.DEBUG)
```
**Node**
```js
// Antes (utils.js)
const config = { dbPass: "senha_super_secreta_prod_123", paymentGatewayKey: "pk_live_123", port: 3000 };
// Depois (src/config/index.js)
module.exports = Object.freeze({
  port: Number(process.env.PORT) || 3000,
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',   // sem default real
  dbPath: process.env.DB_PATH || ':memory:',
});
```
Documente as variáveis em um `.env.example` (sem valores reais). Segredo sem default de produção: gere um efêmero em dev ou falhe ao subir em produção.

---

## PB-02 — Parametrizar queries (AP-02)

**Antes**
```python
cursor.execute("SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'")
query += " AND (nome LIKE '%" + termo + "%')"
```
**Depois**
```python
cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
clauses, params = ["1=1"], []
if termo:
    clauses.append("(nome LIKE ? OR descricao LIKE ?)")
    params += [f"%{termo}%", f"%{termo}%"]
cursor.execute(f"SELECT {COLUNAS} FROM produtos WHERE {' AND '.join(clauses)}", params)
```
Só fragmentos **constantes** (nomes de colunas fixos) podem ser interpolados; valores sempre como parâmetro.
**Node:** `db.get("SELECT * FROM users WHERE email = ?", [email])`.

---

## PB-03 — Quebrar God Class / God File por responsabilidade (AP-03, AP-15)

**Antes** (`AppManager.js`)
```js
class AppManager {
  constructor() { this.db = new sqlite3.Database(':memory:'); }
  initDb() { /* CREATE TABLE + seeds */ }
  setupRoutes(app) { app.post('/api/checkout', (req, res) => { /* SQL + pagamento + log */ }); }
}
```
**Depois**
```
src/database/connection.js   → abre o banco e expõe get/all/run com Promise
src/database/schema.js       → CREATE TABLE + seed
src/models/UserModel.js      → findByEmail, create, deleteCascade
src/models/CourseModel.js    → findActiveById
src/controllers/CheckoutController.js → fluxo de checkout
src/routes/checkoutRoutes.js → app.post('/api/checkout', ...)
src/createApp.js             → instancia e liga tudo
```
Para `models.py` monolítico (Python): um arquivo por entidade em `src/models/`, com um único mapeador `row → dict` por entidade (remove a duplicação de dicionários).
```python
# Antes: o mesmo dict de 8 campos repetido em 3 funções
# Depois
PRODUTO_COLUNAS = "id, nome, descricao, preco, estoque, categoria, ativo, criado_em"
def _to_dict(row): return dict(row) if row else None
```

---

## PB-04 — Hash de senha seguro (AP-04)

**Antes**
```python
self.password = hashlib.md5(pwd.encode()).hexdigest()
```
```js
function badCrypto(pwd) { let h = ""; for (let i=0;i<10000;i++) h += Buffer.from(pwd).toString('base64').substring(0,2); return h.substring(0,10); }
```
**Depois (Python — sem dependência nova, `werkzeug` já vem com Flask)**
```python
from werkzeug.security import generate_password_hash, check_password_hash
def set_password(self, pwd): self.password = generate_password_hash(pwd)
def check_password(self, pwd): return check_password_hash(self.password, pwd)
```
**Depois (Node — `node:crypto`)**
```js
const crypto = require('node:crypto');
function hashPassword(pwd) {
  const salt = crypto.randomBytes(16).toString('hex');
  return `scrypt$${salt}$${crypto.scryptSync(pwd, salt, 64).toString('hex')}`;
}
function verifyPassword(pwd, stored) {
  const [, salt, hash] = stored.split('$');
  return crypto.timingSafeEqual(Buffer.from(hash, 'hex'), crypto.scryptSync(pwd, salt, 64));
}
```
Login nunca compara senha em SQL: busque pelo e-mail e verifique o hash em código. Se já houver hashes legados (MD5/texto puro), verifique no formato antigo uma vez e re-hasheie no login bem-sucedido.

---

## PB-05 — Não expor dados sensíveis + token assinado (AP-05, AP-12)

**Antes**
```python
def to_dict(self): return {..., 'password': self.password}
return jsonify({..., "secret_key": "minha-chave-super-secreta-123", "debug": True})
```
```js
console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`);
```
**Depois**
```python
def to_dict(self): return {"id": self.id, "name": self.name, "email": self.email, "role": self.role, ...}  # sem password
```
```js
logger.info(`Processando pagamento cartão final ${card.slice(-4)}`);
```
**Token assinado sem dependência nova (Flask → `itsdangerous`)**
```python
# Antes
'token': 'fake-jwt-token-' + str(user.id)
# Depois — src/services/token_service.py
from itsdangerous import URLSafeTimedSerializer
class TokenService:
    def __init__(self, secret_key): self._s = URLSafeTimedSerializer(secret_key, salt="auth")
    def issue(self, user_id): return self._s.dumps({"uid": user_id})
    def verify(self, token, max_age=3600): return self._s.loads(token, max_age=max_age)
```
Mantenha o **nome do campo** (`token`) para não quebrar clientes.

---

## PB-06 — Proteger ou isolar endpoints perigosos (AP-06)

**Antes**
```python
@app.route("/admin/query", methods=["POST"])
def executar_query():
    cursor.execute(request.get_json()["sql"])
```
**Depois** — a rota continua existindo, mas desabilitada por padrão e protegida por token de admin vindo do ambiente; consultas restritas a leitura.
```python
def require_admin_token(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        expected = current_app.config["SETTINGS"].ADMIN_TOKEN
        given = request.headers.get("X-Admin-Token", "")
        if not expected or not hmac.compare_digest(given, expected):
            raise ForbiddenError("Acesso negado")
        return view(*args, **kwargs)
    return wrapper

@admin_bp.post("/admin/query")
@require_admin_token
def executar_query(): return jsonify(admin_controller.run_read_only_query(request.get_json()))
```
Se o endpoint não tiver nenhum uso legítimo, remova-o e registre em "Contract changes". Autenticação geral de usuários é decisão de produto → "Deferred".

---

## PB-07 — Extrair controller (fluxo/regras) e service (efeitos colaterais) da rota (AP-07, AP-09, AP-18)

**Antes**
```python
def criar_pedido():
    dados = request.get_json()
    ...validações...
    resultado = models.criar_pedido(usuario_id, itens)
    print("ENVIANDO EMAIL: Pedido ...")
    print("ENVIANDO SMS: ...")
    return jsonify({...}), 201
```
**Depois**
```python
# src/views/pedido_routes.py  (View: só HTTP)
@bp.post("/pedidos")
def criar_pedido():
    resultado = controller().criar(request.get_json(silent=True))
    return jsonify({"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}), 201

# src/controllers/pedido_controller.py  (Controller: fluxo)
class PedidoController:
    def __init__(self, pedido_model, notification_service):
        self.pedidos, self.notifier = pedido_model, notification_service
    def criar(self, dados):
        usuario_id, itens = validar_pedido(dados)          # lança ValidationError
        resultado = self.pedidos.criar(usuario_id, itens)  # lança ValidationError p/ estoque
        self.notifier.pedido_criado(resultado["pedido_id"], usuario_id)
        return resultado
```
**Node**
```js
// routes/checkoutRoutes.js
router.post('/api/checkout', asyncHandler(async (req, res) => {
  const result = await checkoutController.checkout(req.body);
  res.status(200).json(result);
}));
```

---

## PB-08 — Eliminar estado global e injetar dependências via composition root (AP-08, AP-09)

**Antes**
```python
db_connection = None
def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect(db_path, check_same_thread=False)
```
```js
let globalCache = {}; let totalRevenue = 0;
module.exports = { globalCache, totalRevenue };
```
**Depois**
```python
# src/database.py — uma conexão por request
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["SETTINGS"].DATABASE_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None: db.close()

def init_app(app):
    app.teardown_appcontext(close_db)
```
```js
// services/cache.js — instância injetada, sem estado de módulo
class InMemoryCache { constructor() { this.store = new Map(); } set(k, v) { this.store.set(k, v); } get(k) { return this.store.get(k); } }
// createApp.js
const cache = new InMemoryCache();
const checkoutController = new CheckoutController({ ..., cache });
```

---

## PB-09 — Transações e integridade referencial (AP-10)

**Antes**
```js
db.run("INSERT INTO enrollments ...", function () {
  db.run("INSERT INTO payments ...", function () { /* se falhar, matrícula fica órfã */ });
});
app.delete('/api/users/:id', (req, res) => db.run("DELETE FROM users WHERE id = ?", [id], ...));
```
**Depois**
```js
async transaction(work) {
  await this.run('BEGIN');
  try { const r = await work(); await this.run('COMMIT'); return r; }
  catch (err) { await this.run('ROLLBACK'); throw err; }
}
await db.transaction(async () => {
  const enrollmentId = await enrollments.create(userId, courseId);
  await payments.create(enrollmentId, course.price, 'PAID');
  await auditLogs.create(`Checkout curso ${courseId} por ${userId}`);
});
// deleção sem órfãos
await db.transaction(async () => {
  await payments.deleteByUser(id); await enrollments.deleteByUser(id); await users.delete(id);
});
```
**Python (sqlite3)**
```python
with db:  # commit automático, rollback em exceção
    cur = db.execute("INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)", (uid, total))
    ...
```
Valide tudo (existência, estoque) **antes** de começar a escrever.

---

## PB-10 — Eliminar N+1 com JOIN / agregação (AP-13)

**Antes**
```python
for row in pedidos:
    cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"]))
    for item in cursor2.fetchall():
        cursor3.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"]))
```
**Depois** — 2 queries no total, montagem em memória
```python
pedidos = db.execute("SELECT id, usuario_id, status, total, criado_em FROM pedidos").fetchall()
itens = db.execute("""
    SELECT i.pedido_id, i.produto_id, i.quantidade, i.preco_unitario,
           COALESCE(p.nome, 'Desconhecido') AS produto_nome
    FROM itens_pedido i LEFT JOIN produtos p ON p.id = i.produto_id
""").fetchall()
por_pedido = defaultdict(list)
for i in itens: por_pedido[i["pedido_id"]].append({...})
```
**SQLAlchemy** — `select(Task).options(joinedload(Task.user), joinedload(Task.category))`; contagens: `select(Task.status, func.count()).group_by(Task.status)`.
**Node** — um único `SELECT ... FROM courses c LEFT JOIN enrollments e ... LEFT JOIN users u ... LEFT JOIN payments p ...` e agrupamento em JS.

---

## PB-11 — Centralizar validação e regras duplicadas (AP-14, AP-15)

**Antes** — mesmas checagens copiadas em create/update; regra "overdue" em 5 handlers
```python
if t.due_date:
    if t.due_date < datetime.utcnow():
        if t.status != 'done' and t.status != 'cancelled':
            task_data['overdue'] = True
```
**Depois**
```python
# models/task.py — a regra mora na entidade
def is_overdue(self, now=None):
    now = now or utcnow()
    return bool(self.due_date and self.due_date < now and self.status not in CLOSED_STATUSES)

# utils/validators.py — um validador por payload, usado por create e update
def validate_task_payload(data, partial=False) -> dict:
    if not isinstance(data, dict): raise ValidationError("Dados inválidos")
    ...
```
Validar **tipo** antes de comparar (`isinstance(priority, int)`), para não transformar entrada ruim em 500.

---

## PB-12 — Error handling centralizado (AP-16)

**Antes**
```python
def listar_produtos():
    try: ...
    except Exception as e:
        return jsonify({"erro": str(e)}), 500   # repetido em 15 handlers
```
**Depois** — `src/middlewares/error_handler.py`
```python
class AppError(Exception):
    status = 500
    def __init__(self, message, status=None):
        super().__init__(message); self.message = message
        if status: self.status = status
class ValidationError(AppError): status = 400
class NotFoundError(AppError): status = 404

def register_error_handlers(app):
    @app.errorhandler(AppError)
    def _app_error(err): return jsonify({"erro": err.message, "sucesso": False}), err.status
    @app.errorhandler(Exception)
    def _unexpected(err):
        app.logger.exception("Erro inesperado")
        return jsonify({"erro": "Erro interno do servidor", "sucesso": False}), 500
```
Use o **envelope de erro original** do projeto. Para HTTPException do framework (404 de rota inexistente, 405), devolva o próprio status.
**Express**
```js
module.exports = (err, req, res, next) => {
  if (err instanceof AppError) return res.status(err.status).send(err.message);
  console.error(err); res.status(500).send('Erro interno');
};
```

---

## PB-13 — Substituir APIs deprecated (AP-17)

```python
# Antes
from datetime import datetime
created_at = db.Column(db.DateTime, default=datetime.utcnow)
task = Task.query.get(task_id)
# Depois
from src.utils.time import utcnow          # datetime.now(timezone.utc).replace(tzinfo=None)
created_at = db.Column(db.DateTime, default=utcnow)
task = db.session.get(Task, task_id)
```
```js
// Antes                      // Depois
new Buffer(pwd)               Buffer.from(pwd)
url.parse(req.url)            new URL(req.url, 'http://localhost')
```
Mantenha a semântica de armazenamento: se o banco guarda datetime *naive* em UTC, continue gravando naive (comparar aware com naive gera `TypeError`).

---

## PB-14 — Higiene: constantes, nomes, logging, código morto (AP-19, AP-20, AP-21, AP-22)

```python
# Antes
if faturamento > 10000: desconto = faturamento * 0.1
elif faturamento > 5000: desconto = faturamento * 0.05
print("Produto criado com ID: " + str(id))
import os, sys, json, time   # sem uso
# Depois
DESCONTO_POR_FAIXA = ((10000, 0.10), (5000, 0.05), (1000, 0.02))   # config/settings.py
desconto = next((fat * taxa for limite, taxa in DESCONTO_POR_FAIXA if fat > limite), 0)
logger.info("Produto criado com ID %s", produto_id)
```
```js
// Antes
let u = req.body.usr; let e = req.body.eml; let cc = req.body.card;
// Depois — o contrato (usr/eml/card) continua, só os nomes internos melhoram
const { usr: name, eml: email, pwd: password, c_id: courseId, card: cardNumber } = req.body;
```

---

## PB-15 — Simplificar condicionais e achatar callbacks (AP-23)

```python
# Antes
def is_admin(self):
    if self.role == 'admin':
        return True
    else:
        return False
# Depois
def is_admin(self): return self.role == "admin"
```
```js
// Antes: 5 níveis de callback
db.get(q1, a, (e, course) => { db.get(q2, b, (e, user) => { db.run(q3, c, function () { ... }) }) })
// Depois
const course = await courses.findActiveById(courseId);
const user = await users.findByEmail(email);
```

---

## Mapa rápido AP → PB

| AP | PB | | AP | PB |
|---|---|---|---|---|
| AP-01 Credenciais | PB-01 | | AP-13 N+1 | PB-10 |
| AP-02 SQL Injection | PB-02 | | AP-14 Validação | PB-11 |
| AP-03 God Class | PB-03 | | AP-15 Duplicação | PB-11, PB-03 |
| AP-04 Senha insegura | PB-04 | | AP-16 Erros | PB-12 |
| AP-05 Exposição de dados | PB-05 | | AP-17 Deprecated | PB-13 |
| AP-06 Endpoint perigoso | PB-06 | | AP-18 Efeitos colaterais | PB-07, PB-08 |
| AP-07 Fat controller | PB-07 | | AP-19 Magic numbers | PB-14 |
| AP-08 Estado global | PB-08 | | AP-20 Nomes | PB-14 |
| AP-09 Acoplamento | PB-08, PB-07 | | AP-21 print/log | PB-14 |
| AP-10 Transação | PB-09 | | AP-22 Código morto | PB-14 |
| AP-11 Config insegura | PB-01 | | AP-23 Condicionais | PB-15 |
| AP-12 Token falso | PB-05 | | | |
