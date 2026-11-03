"""Operações administrativas. A autorização é feita pelo middleware `require_admin_token`."""
import logging
import sqlite3

from src.errors import ValidationError

logger = logging.getLogger(__name__)


class AdminController:
    def __init__(self, admin_model):
        self.admin = admin_model

    def resetar_banco(self):
        self.admin.limpar_banco()
        logger.warning("Banco de dados resetado via /admin/reset-db")

    def consultar(self, dados):
        sql = dados.get("sql", "") if isinstance(dados, dict) else ""
        if not isinstance(sql, str) or not sql.strip():
            raise ValidationError("Query não informada")
        if not sql.lstrip().upper().startswith("SELECT"):
            raise ValidationError("Apenas consultas SELECT são permitidas")
        try:
            return self.admin.consulta_somente_leitura(sql)
        except sqlite3.Error as exc:
            raise ValidationError(f"Query inválida: {exc}")
