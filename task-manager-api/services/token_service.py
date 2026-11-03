"""Tokens de autenticação assinados e com expiração (itsdangerous já é dependência do Flask)."""
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer


class TokenService:
    def __init__(self, secret_key, max_age_seconds):
        self._serializer = URLSafeTimedSerializer(secret_key, salt="auth-token")
        self._max_age = max_age_seconds

    def issue(self, user_id):
        return self._serializer.dumps({"uid": user_id})

    def verify(self, token):
        """Retorna o id do usuário ou None se o token for inválido/expirado."""
        try:
            return self._serializer.loads(token, max_age=self._max_age)["uid"]
        except (BadSignature, SignatureExpired, KeyError, TypeError):
            return None
