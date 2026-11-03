"""Casos de uso de usuários e login."""
import logging

from database import db
from errors import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError
from models.task import Task
from models.user import User
from utils.time import utcnow
from utils.validators import validate_login, validate_new_user, validate_role, validate_user_update

logger = logging.getLogger(__name__)


class UserController:
    def __init__(self, token_service):
        self.tokens = token_service

    def list_users(self):
        result = []
        for user, task_count, _completed in User.list_with_task_stats():
            data = user.to_dict()
            data['task_count'] = task_count
            result.append(data)
        return result

    def get_user(self, user_id):
        user = self._get_or_404(user_id)
        data = user.to_dict()
        data['tasks'] = [t.to_dict() for t in Task.list_by_user(user_id)]
        return data

    def get_user_tasks(self, user_id):
        self._get_or_404(user_id)
        now = utcnow()
        return [
            {
                'id': t.id,
                'title': t.title,
                'description': t.description,
                'status': t.status,
                'priority': t.priority,
                'created_at': str(t.created_at),
                'due_date': str(t.due_date) if t.due_date else None,
                'overdue': t.is_overdue(now),
            }
            for t in Task.list_by_user(user_id)
        ]

    def create_user(self, data):
        fields = validate_new_user(data)
        if User.find_by_email(fields['email']):
            raise ConflictError('Email já cadastrado')
        validate_role(fields['role'])

        user = User(name=fields['name'], email=fields['email'], role=fields['role'])
        user.set_password(fields['password'])
        db.session.add(user)
        db.session.commit()
        logger.info("Usuário criado: %s", user.id)
        return user.to_dict()

    def update_user(self, user_id, data):
        user = self._get_or_404(user_id)
        fields = validate_user_update(data)
        if 'email' in fields:
            existing = User.find_by_email(fields['email'])
            if existing and existing.id != user_id:
                raise ConflictError('Email já cadastrado')
        password = fields.pop('password', None)
        if password:
            user.set_password(password)
        for name, value in fields.items():
            setattr(user, name, value)
        db.session.commit()
        return user.to_dict()

    def delete_user(self, user_id):
        user = self._get_or_404(user_id)
        Task.delete_by_user(user_id)
        db.session.delete(user)
        db.session.commit()
        logger.info("Usuário deletado: %s", user_id)

    def login(self, data):
        email, password = validate_login(data)
        user = User.find_by_email(email)
        if not user or not user.check_password(password):
            raise UnauthorizedError('Credenciais inválidas')
        if not user.active:
            raise ForbiddenError('Usuário inativo')
        if user.has_legacy_password_hash():  # migra MD5 legado para o hash atual
            user.set_password(password)
            db.session.commit()
        return {
            'message': 'Login realizado com sucesso',
            'user': user.to_dict(),
            'token': self.tokens.issue(user.id),
        }

    @staticmethod
    def _get_or_404(user_id):
        user = User.get(user_id)
        if not user:
            raise NotFoundError('Usuário não encontrado')
        return user
