# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot, já com produtos e usuários de exemplo.

## Configuração (após a refatoração `refactor-arch`)

Variáveis de ambiente (veja `.env.example`): `SECRET_KEY`, `FLASK_DEBUG`, `HOST`, `PORT`, `DATABASE_PATH`, `CORS_ORIGINS`, `APP_ENV` e `ADMIN_TOKEN`.
`POST /admin/reset-db` e `POST /admin/query` exigem o cabeçalho `X-Admin-Token` igual a `ADMIN_TOKEN` (sem `ADMIN_TOKEN` definido, respondem 403); `/admin/query` aceita apenas um `SELECT`, executado em conexão somente leitura.
