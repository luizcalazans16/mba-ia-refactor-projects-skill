"""Hash e verificação de senha (werkzeug já é dependência do Flask)."""
import hmac

from werkzeug.security import check_password_hash, generate_password_hash

_HASH_PREFIXES = ("scrypt:", "pbkdf2:")


def hash_password(password):
    return generate_password_hash(password)


def is_hashed(stored):
    return bool(stored) and stored.startswith(_HASH_PREFIXES)


def verify_password(stored, password):
    """Verifica a senha. Aceita registros legados em texto puro (para migrá-los no login)."""
    if not stored:
        return False
    if is_hashed(stored):
        return check_password_hash(stored, password)
    return hmac.compare_digest(stored.encode(), password.encode())
