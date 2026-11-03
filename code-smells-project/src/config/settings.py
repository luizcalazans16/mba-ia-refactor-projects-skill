"""Configuração central da aplicação: tudo que varia por ambiente vem de variáveis de ambiente."""
import os
import secrets


def _env_bool(name, default=False):
    return os.environ.get(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


class Settings:
    def __init__(self, **overrides):
        self.APP_VERSION = "1.0.0"
        self.ENVIRONMENT = os.environ.get("APP_ENV", "development")
        # Sem SECRET_KEY no ambiente, gera uma chave efêmera (válida só enquanto o processo vive).
        self.SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
        self.DEBUG = _env_bool("FLASK_DEBUG", False)
        self.HOST = os.environ.get("HOST", "127.0.0.1")
        self.PORT = int(os.environ.get("PORT", "5000"))
        self.DATABASE_PATH = os.environ.get("DATABASE_PATH", "loja.db")
        self.CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")
        # Endpoints /admin/* ficam desabilitados enquanto ADMIN_TOKEN não for definido.
        self.ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")
        for key, value in overrides.items():
            setattr(self, key, value)


# --- Regras de negócio (constantes nomeadas) ---------------------------------
CATEGORIAS_VALIDAS = ("informatica", "moveis", "vestuario", "geral", "eletronicos", "livros")
CATEGORIA_PADRAO = "geral"
NOME_PRODUTO_MIN = 2
NOME_PRODUTO_MAX = 200

STATUS_PEDIDO_VALIDOS = ("pendente", "aprovado", "enviado", "entregue", "cancelado")
STATUS_PEDIDO_INICIAL = "pendente"

TIPO_USUARIO_PADRAO = "cliente"

# (faturamento mínimo exclusivo, percentual de desconto), da maior faixa para a menor
FAIXAS_DESCONTO = ((10000, 0.10), (5000, 0.05), (1000, 0.02))
