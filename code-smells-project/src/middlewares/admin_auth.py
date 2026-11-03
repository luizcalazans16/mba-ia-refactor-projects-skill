"""Proteção dos endpoints administrativos por token (cabeçalho X-Admin-Token)."""
import hmac
from functools import wraps

from flask import current_app, request

from src.errors import ForbiddenError


def require_admin_token(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        expected = current_app.config["SETTINGS"].ADMIN_TOKEN
        given = request.headers.get("X-Admin-Token", "")
        if not expected or not hmac.compare_digest(given.encode(), expected.encode()):
            raise ForbiddenError("Acesso negado")
        return view(*args, **kwargs)

    return wrapper
