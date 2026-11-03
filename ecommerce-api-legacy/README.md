# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
npm install
npm start
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória e já carrega seeds automaticamente no boot.

Exemplos de requisições estão em `api.http`.

## Configuração (após a refatoração `refactor-arch`)

Variáveis de ambiente (veja `.env.example`): `PORT`, `DB_PATH`, `PAYMENT_GATEWAY_KEY`, `LOG_LEVEL` e `ADMIN_TOKEN`.
`GET /api/admin/financial-report` exige o cabeçalho `X-Admin-Token` igual a `ADMIN_TOKEN`; sem `ADMIN_TOKEN` definido o endpoint responde 403.

```bash
ADMIN_TOKEN=meu-token npm start
```
