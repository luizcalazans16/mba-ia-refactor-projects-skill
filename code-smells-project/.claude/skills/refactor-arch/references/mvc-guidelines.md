# Guidelines da Arquitetura-Alvo — MVC para APIs (Fase 3)

Em uma API não há templates HTML: a **View** é a camada que expõe e serializa (rotas + formato da resposta). A arquitetura-alvo é MVC com duas camadas de apoio (config e middlewares) e, quando há integrações, services.

```
            HTTP request
                 │
        ┌────────▼────────┐
        │  View / Routes  │  parse request → chama controller → serializa resposta
        └────────┬────────┘
        ┌────────▼────────┐
        │   Controller    │  fluxo do caso de uso, regras de negócio, validação
        └───┬─────────┬───┘
   ┌────────▼───┐ ┌───▼────────┐
   │   Model    │ │  Service   │  dados/entidades   |  integrações (e-mail, pagamento, hash, cache)
   └────────┬───┘ └────────────┘
        ┌───▼───┐
        │  DB   │
        └───────┘
   Config ─ lida só pelo composition root e injetada.   Middlewares ─ erros, CORS, logging.
```

## Responsabilidades e proibições

| Camada | Faz | **Não** faz |
|---|---|---|
| **Model** (`models/`) | Define entidades/tabelas; encapsula acesso a dados (queries parametrizadas, ORM, transações); regras intrínsecas da entidade (`is_overdue`, `to_dict` sem campos sensíveis) | Ler `request`, montar resposta HTTP, enviar e-mail, ler variáveis de ambiente |
| **Controller** (`controllers/`) | Orquestra o caso de uso: valida a entrada, aplica regras de negócio, chama models e services, decide erros de domínio (lançando exceções tipadas); retorna dados puros (dict/obj) | Conhecer `request`/`res`, status HTTP em sucesso, SQL |
| **View / Routes** (`views/` ou `routes/`) | Mapeia rota+método → controller; extrai params/query/body; devolve `jsonify`/`res.json` com o status; registra blueprints/routers | Regras de negócio, SQL, `try/except` repetido (isso é do error handler) |
| **Service** (`services/`) | Integrações e utilidades com efeito colateral ou técnicas: notificação, gateway de pagamento, hash de senha, token, cache | Conhecer HTTP; acessar tabelas de outros domínios diretamente |
| **Config** (`config/`) | Lê variáveis de ambiente, define defaults **não sensíveis** para dev, centraliza constantes de negócio | Conter segredos de produção como literal |
| **Middlewares** (`middlewares/`) | Error handler central (exceção → status + envelope de erro), logging de request, CORS | Regra de negócio |
| **Composition root** (`app.py`/`app.js` dentro de `src/`) | Cria a app, carrega config, cria conexões/serviços, injeta dependências, registra rotas e middlewares | Lógica de request |

### Direção das dependências
`views → controllers → (models, services)`. Models e services **nunca** importam controllers ou views. Config é lida no composition root e passada adiante (ou via objeto de config da app, ex.: `current_app.config`).

### Erros
- Defina uma hierarquia mínima: `AppError(status, message)` com subclasses `ValidationError` (400), `NotFoundError` (404), `ConflictError` (409), `UnauthorizedError` (401), `ForbiddenError` (403).
- Controllers lançam; o middleware central converte. Erros inesperados → 500 com mensagem genérica + log do stack (nunca `str(e)` para o cliente).
- **Preserve o envelope de erro original do projeto** (ex.: `{"erro": "...", "sucesso": false}` vs `{"error": "..."}` vs texto puro). O handler central deve produzir exatamente o mesmo formato que os clientes já consomem.

## Estrutura-alvo por stack

### Python / Flask
```
<projeto>/
├── app.py                      # entry point fino: from src.app import create_app; app = create_app(); app.run(...)
├── requirements.txt
└── src/
    ├── __init__.py
    ├── app.py                  # create_app(): composition root
    ├── config/
    │   ├── __init__.py
    │   └── settings.py         # Settings a partir de os.environ + constantes de negócio
    ├── database.py             # conexão (por request via flask.g) / instância SQLAlchemy, schema, seed
    ├── models/                 # <entidade>_model.py
    ├── controllers/            # <dominio>_controller.py
    ├── views/                  # <dominio>_routes.py (Blueprints)
    ├── services/               # notification_service.py, password_service.py ...
    ├── middlewares/
    │   └── error_handler.py
    └── utils/                  # validators.py, time.py ... (apenas helpers puros)
```
- Use **application factory** (`create_app(config_overrides=None)`), blueprints por domínio e `app.register_error_handler`.
- Conexão sqlite: uma por request (`flask.g` + `teardown_appcontext`), nunca global com `check_same_thread=False`.
- Mantenha o comando `python app.py` funcionando (o `app.py` da raiz vira shim). Scripts auxiliares (ex.: `seed.py`) devem continuar funcionando com o mesmo comando.

### Node.js / Express
```
<projeto>/
├── package.json                # "start" continua apontando para o entry point
└── src/
    ├── app.js                  # entry point: createApp() + listen
    ├── createApp.js            # composition root (instancia db, models, services, controllers, routers)
    ├── config/index.js         # process.env + defaults não sensíveis
    ├── database/               # connection.js (wrapper com Promises), schema.js/seed.js
    ├── models/                 # <entidade>Model.js (classes recebem db no construtor)
    ├── controllers/            # <dominio>Controller.js
    ├── routes/                 # <dominio>Routes.js (express.Router) — a camada View
    ├── services/               # paymentGateway.js, passwordHasher.js, cache.js
    └── middlewares/            # errorHandler.js, asyncHandler.js
```
- Promisifique o driver de callback (`db.get/all/run` → `async`) e use `async/await`; nada de callback hell.
- Injeção por construtor: `new CheckoutController({ userModel, courseModel, paymentGateway, ... })`.
- `asyncHandler(fn)` para encaminhar rejeições ao middleware de erro `(err, req, res, next)`.

### Outras stacks (mapeamento)
| Stack | Model | Controller | View/Routes |
|---|---|---|---|
| FastAPI | `models/` (SQLAlchemy/Pydantic) | `controllers/` ou `services/` | `routers/` (`APIRouter`) |
| Django | `models.py` por app | `services.py` | `views.py` + `urls.py` |
| NestJS | `entities/` + repositories | `*.service.ts` | `*.controller.ts` (no Nest o "controller" é a View) |
| Spring | `entity/` + `repository/` | `service/` | `controller/` (`@RestController`) |
| Go (Gin/Echo) | `internal/model`, `internal/repository` | `internal/service` | `internal/handler` + router |

## Adaptação ao nível de organização atual

| Situação encontrada | Estratégia |
|---|---|
| **Monolito** (tudo em 1–4 arquivos) | Criar a árvore completa; mover funções por domínio; o arquivo antigo é removido quando esvaziado. |
| **God class** (ex.: `AppManager` com DB + rotas) | Quebrar por responsabilidade: schema/seed → `database/`; cada tabela → model; cada fluxo de rota → controller; rotas → routers; helpers → services. |
| **Camadas parciais** (já há `models/`, `routes/`, `services/`) | Manter models que já são bons (só corrigir); introduzir `controllers/` extraindo a lógica das rotas; renomear/mover rotas para `views/` se necessário para clareza; mover rotas que estão no blueprint errado (ex.: categorias dentro de `report_routes`) para o seu próprio módulo; ligar services ociosos via injeção; remover utils mortos ou passar a usá-los. |

## Critérios de "pronto"
- Nenhum handler de rota com SQL/ORM ou regra de negócio.
- Nenhum segredo literal; config única.
- Um único lugar trata erros.
- Entry point claro e comando de start inalterado.
- Cada arquivo tem uma responsabilidade nomeável em uma frase.
