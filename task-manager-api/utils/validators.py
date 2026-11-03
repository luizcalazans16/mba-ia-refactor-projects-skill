"""Validação de payloads: uma função por recurso, usada por create e update."""
import re
from datetime import datetime

from config.settings import (
    DATE_FORMAT,
    DEFAULT_PRIORITY,
    DEFAULT_ROLE,
    DEFAULT_STATUS,
    MAX_PRIORITY,
    MAX_TITLE_LENGTH,
    MIN_PASSWORD_LENGTH,
    MIN_PRIORITY,
    MIN_TITLE_LENGTH,
    TASK_STATUSES,
    USER_ROLES,
)
from errors import ValidationError

EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$")
COLOR_PATTERN = re.compile(r"^#[0-9a-fA-F]{6}$")


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def require_json_object(data):
    if not data or not isinstance(data, dict):
        raise ValidationError("Dados inválidos")
    return data


def parse_int_param(value, message):
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValidationError(message)


# --- Tasks --------------------------------------------------------------------
def _validate_title(title):
    if not title:
        raise ValidationError("Título é obrigatório")
    if not isinstance(title, str):
        raise ValidationError("Título inválido")
    if len(title) < MIN_TITLE_LENGTH:
        raise ValidationError("Título muito curto")
    if len(title) > MAX_TITLE_LENGTH:
        raise ValidationError("Título muito longo")
    return title


def _validate_due_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, DATE_FORMAT)
    except (TypeError, ValueError):
        raise ValidationError("Formato de data inválido. Use YYYY-MM-DD")


def _normalize_tags(tags):
    return ",".join(tags) if isinstance(tags, list) else tags


def validate_task_payload(data, partial=False):
    """Retorna somente os campos presentes e válidos. Em create (`partial=False`) aplica defaults."""
    data = require_json_object(data)
    result = {}

    if not partial or "title" in data:
        result["title"] = _validate_title(data.get("title"))
    if "description" in data or not partial:
        result["description"] = data.get("description", "")
    if "status" in data or not partial:
        status = data.get("status", DEFAULT_STATUS)
        if status not in TASK_STATUSES:
            raise ValidationError("Status inválido")
        result["status"] = status
    if "priority" in data or not partial:
        priority = data.get("priority", DEFAULT_PRIORITY)
        if not _is_int(priority) or not MIN_PRIORITY <= priority <= MAX_PRIORITY:
            raise ValidationError(f"Prioridade deve ser entre {MIN_PRIORITY} e {MAX_PRIORITY}")
        result["priority"] = priority
    for field in ("user_id", "category_id"):
        if field in data or not partial:
            value = data.get(field)
            if value is not None and not _is_int(value):
                raise ValidationError(f"{field} inválido")
            result[field] = value
    if "due_date" in data:
        result["due_date"] = _validate_due_date(data["due_date"])
    if "tags" in data and (partial or data["tags"]):
        result["tags"] = _normalize_tags(data["tags"])
    return result


# --- Users --------------------------------------------------------------------
def _validate_email(email):
    if not isinstance(email, str) or not EMAIL_PATTERN.match(email):
        raise ValidationError("Email inválido")
    return email


def _validate_password(password):
    if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(f"Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres")
    return password


def _validate_role(role):
    if role not in USER_ROLES:
        raise ValidationError("Role inválido")
    return role


def validate_new_user(data):
    data = require_json_object(data)
    for field, message in (("name", "Nome é obrigatório"), ("email", "Email é obrigatório"),
                           ("password", "Senha é obrigatória")):
        if not data.get(field):
            raise ValidationError(message)
    if not isinstance(data["name"], str):
        raise ValidationError("Nome inválido")
    return {
        "name": data["name"],
        "email": _validate_email(data["email"]),
        "password": _validate_password(data["password"]),
        "role": data.get("role", DEFAULT_ROLE),  # validado pelo controller depois da checagem de duplicidade
    }


def validate_user_update(data):
    data = require_json_object(data)
    result = {}
    if "name" in data:
        if not isinstance(data["name"], str) or not data["name"]:
            raise ValidationError("Nome inválido")
        result["name"] = data["name"]
    if "email" in data:
        result["email"] = _validate_email(data["email"])
    if "password" in data:
        result["password"] = _validate_password(data["password"])
    if "role" in data:
        result["role"] = _validate_role(data["role"])
    if "active" in data:
        if not isinstance(data["active"], bool):
            raise ValidationError("Campo active deve ser booleano")
        result["active"] = data["active"]
    return result


def validate_role(role):
    return _validate_role(role)


def validate_login(data):
    data = require_json_object(data)
    email, password = data.get("email"), data.get("password")
    if not email or not password:
        raise ValidationError("Email e senha são obrigatórios")
    return str(email), str(password)


# --- Categories ---------------------------------------------------------------
def validate_category_payload(data, partial=False):
    data = require_json_object(data)
    result = {}
    if not partial or "name" in data:
        if not data.get("name") or not isinstance(data["name"], str):
            raise ValidationError("Nome é obrigatório")
        result["name"] = data["name"]
    if "description" in data or not partial:
        result["description"] = data.get("description", "")
    if "color" in data:
        if not isinstance(data["color"], str) or not COLOR_PATTERN.match(data["color"]):
            raise ValidationError("Cor inválida. Use o formato #RRGGBB")
        result["color"] = data["color"]
    return result
