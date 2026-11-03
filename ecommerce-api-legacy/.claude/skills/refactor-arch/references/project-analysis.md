# Análise de Projeto — Heurísticas (Fase 1)

Objetivo: em poucos minutos, descrever com evidência **o que** é o projeto, **como** ele roda e **como** está organizado. Toda afirmação do resumo da Fase 1 deve vir de um arquivo que você leu.

## 1. Detecção de linguagem

Procure, nesta ordem, os manifestos na raiz (e em um nível abaixo):

| Manifesto / sinal | Linguagem | Observações |
|---|---|---|
| `requirements.txt`, `pyproject.toml`, `setup.py`, `Pipfile`, `poetry.lock` | Python | versão mínima: `python_requires`, `[project] requires-python`, `.python-version` |
| `package.json` | JavaScript / TypeScript | TS se houver `tsconfig.json` ou deps `typescript`/`ts-node`; versão do Node em `engines.node` ou `.nvmrc` |
| `go.mod` | Go | |
| `pom.xml`, `build.gradle(.kts)` | Java / Kotlin | |
| `Gemfile` | Ruby | |
| `composer.json` | PHP | |
| `*.csproj`, `*.sln` | C# | |
| `Cargo.toml` | Rust | |

Sem manifesto? Use a extensão predominante dos arquivos-fonte (`*.py`, `*.js`, `*.ts`...) e reporte "manifesto ausente" como finding LOW.

## 2. Detecção de framework (e versão)

Leia a versão **do manifesto** (pin exato ou range). Confirme pelo código:

| Framework | Dependência | Assinatura no código |
|---|---|---|
| Flask | `flask` | `Flask(__name__)`, `@app.route`, `Blueprint(`, `app.add_url_rule` |
| FastAPI | `fastapi` | `FastAPI()`, `@app.get`, `APIRouter` |
| Django | `django` | `settings.py`, `urls.py`, `INSTALLED_APPS` |
| Express | `express` | `require('express')`/`import express`, `app.get(`, `express.Router()` |
| NestJS | `@nestjs/core` | `@Controller(`, `@Module(` |
| Fastify / Koa / Hapi | `fastify` / `koa` / `@hapi/hapi` | `fastify()`, `new Koa()`, `Hapi.server` |
| Spring Boot | `spring-boot-starter-web` | `@RestController`, `@SpringBootApplication` |
| Gin / Echo / chi | `gin-gonic/gin` / `labstack/echo` / `go-chi/chi` | `gin.Default()`, `echo.New()`, `chi.NewRouter()` |
| Rails / Laravel | `rails` / `laravel/framework` | `config/routes.rb` / `routes/web.php` |

Liste também dependências relevantes para a auditoria: CORS, ORM, validação (`marshmallow`, `pydantic`, `joi`, `zod`), HTTP client, dotenv, auth (`jwt`, `passport`).
Dependência declarada e **não usada** (ou usada e **não declarada**) é sinal de finding (LOW / MEDIUM).

## 3. Banco de dados

| Sinal | Engine / acesso |
|---|---|
| `import sqlite3`, `sqlite3.connect(`, `require('sqlite3')`, `':memory:'`, `*.db` | SQLite, driver cru |
| `flask_sqlalchemy`, `SQLAlchemy(`, `db.Model`, `SQLALCHEMY_DATABASE_URI` | SQLAlchemy ORM (veja a URI) |
| `psycopg2`, `pg`, `mysql2`, `pymysql`, `mongoose`, `pymongo` | Postgres / MySQL / MongoDB |
| `prisma`, `typeorm`, `sequelize`, `knex` | ORM / query builder JS |

Mapeie as **tabelas/entidades**: `CREATE TABLE <nome>`, `__tablename__ = '<nome>'`, `class X(db.Model)`, schemas do ORM. Anote onde o schema é criado (arquivo:linha) e se há seed automático no boot.

## 4. Domínio da aplicação

Infira pelos substantivos das tabelas, rotas e README. Descreva em uma linha: tipo de sistema + entidades principais.
Exemplos: "E-commerce API (produtos, usuários, pedidos, itens de pedido)", "LMS com checkout (cursos, matrículas, pagamentos)", "Task Manager (tasks, usuários, categorias, relatórios)".

## 5. Entry point e comando de start

- Python: arquivo com `if __name__ == "__main__":` + `app.run(`; ou `FLASK_APP`; ou `uvicorn x:app`. Comando citado no README tem prioridade.
- Node: `scripts.start` / `main` do `package.json`; arquivo que chama `app.listen(`.
- Registre porta e host (`app.run(port=...)`, `app.listen(PORT)`), flags como `debug=True` e pré-requisitos (ex.: rodar `seed.py` antes).

## 6. Inventário de endpoints

Extraia todas as rotas com método e handler:

- Flask: `@app.route('/x', methods=[...])`, `@bp.route(...)`, `app.add_url_rule('/x', ..., view_func, methods=[...])` (+ `url_prefix` do blueprint).
- Express: `app.<verbo>('/x', ...)`, `router.<verbo>(...)` + prefixo de `app.use('/prefix', router)`.
- Outros: anotações/decorators equivalentes.

Também leia arquivos `*.http`, coleções Postman ou exemplos do README: são casos de teste prontos para a baseline.

## 7. Mapeamento da arquitetura atual

Classifique em um dos níveis e justifique com a distribuição de responsabilidades:

| Nível | Sinais |
|---|---|
| **Monolito / Big Ball of Mud** | 1–4 arquivos concentram rotas + SQL + regra de negócio + config; um único arquivo/classe "faz tudo" (ex.: `AppManager`, `models.py` com SQL e regras de 4 domínios) |
| **Camadas parciais** | já existem pastas `models/`, `routes/`, `services/`, `utils/`, mas as rotas contêm regra de negócio, queries e formatação; services/utils subutilizados ou com código morto |
| **Camadas adequadas** | rotas finas, controllers/services com regras, models só com dados; config externa; error handling central |

Para cada arquivo-fonte, anote quais responsabilidades ele carrega: **R** (roteamento/HTTP), **B** (regra de negócio), **D** (acesso a dados/SQL), **C** (configuração), **V** (validação), **F** (formatação/serialização), **I** (integração externa: e-mail, pagamento). Um arquivo com 3+ letras é candidato a God Class (ver catálogo AP-03).

## 8. Saída

Preencha o bloco "PHASE 1: PROJECT ANALYSIS" do `SKILL.md`. Conte arquivos e linhas com um comando (ex.: `wc -l`) e não com estimativa. Registre a baseline (ver `validation.md`) antes de seguir para a Fase 2.
