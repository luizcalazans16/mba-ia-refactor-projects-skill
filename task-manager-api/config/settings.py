"""Configuração central: valores por ambiente vêm de variáveis de ambiente; regras de negócio são constantes nomeadas."""
import os
import secrets


def _env_bool(name, default=False):
    return os.environ.get(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


class Settings:
    def __init__(self, **overrides):
        # Sem SECRET_KEY no ambiente, gera uma chave efêmera (tokens deixam de valer ao reiniciar).
        self.SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
        self.DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///tasks.db")
        self.DEBUG = _env_bool("FLASK_DEBUG", False)
        self.HOST = os.environ.get("HOST", "127.0.0.1")
        self.PORT = int(os.environ.get("PORT", "5000"))
        self.CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")
        self.TOKEN_MAX_AGE_SECONDS = int(os.environ.get("TOKEN_MAX_AGE_SECONDS", "3600"))
        # SMTP: sem SMTP_HOST as notificações são apenas registradas em log.
        self.SMTP_HOST = os.environ.get("SMTP_HOST", "")
        self.SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
        self.SMTP_USER = os.environ.get("SMTP_USER", "")
        self.SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
        for key, value in overrides.items():
            setattr(self, key, value)


# --- Regras de negócio --------------------------------------------------------
TASK_STATUSES = ("pending", "in_progress", "done", "cancelled")
CLOSED_STATUSES = ("done", "cancelled")
DEFAULT_STATUS = "pending"

MIN_PRIORITY = 1
MAX_PRIORITY = 5
DEFAULT_PRIORITY = 3
HIGH_PRIORITY_THRESHOLD = 2  # prioridades 1 e 2 contam como "alta"
PRIORITY_LABELS = {1: "critical", 2: "high", 3: "medium", 4: "low", 5: "minimal"}

MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200

USER_ROLES = ("user", "admin", "manager")
DEFAULT_ROLE = "user"
MIN_PASSWORD_LENGTH = 4

DEFAULT_CATEGORY_COLOR = "#000000"
RECENT_ACTIVITY_DAYS = 7
DATE_FORMAT = "%Y-%m-%d"
