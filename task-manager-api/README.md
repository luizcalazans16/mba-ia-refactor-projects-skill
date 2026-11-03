# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`. Diferente dos outros projetos, este já possui alguma separação de camadas (`models/`, `routes/`, `services/`, `utils/`), mas ainda contém problemas arquiteturais e de qualidade.

## Como rodar

```bash
pip install -r requirements.txt
python seed.py
python app.py
```

A aplicação sobe em `http://localhost:5000`. O `seed.py` popula o banco SQLite (`tasks.db`) com usuários, categorias e tasks de exemplo — **rode-o antes do primeiro boot**, caso contrário os endpoints vão retornar listas vazias.

## Configuração (após a refatoração `refactor-arch`)

Variáveis de ambiente (veja `.env.example`): `SECRET_KEY`, `DATABASE_URL`, `FLASK_DEBUG`, `HOST`, `PORT`, `CORS_ORIGINS`, `TOKEN_MAX_AGE_SECONDS` e `SMTP_*`.
Sem `SECRET_KEY` a aplicação gera uma chave efêmera (tokens de login deixam de valer ao reiniciar). Sem `SMTP_HOST` as notificações de atribuição de task são apenas registradas em log.
