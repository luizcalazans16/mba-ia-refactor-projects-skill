"""Casos de uso de tasks."""
import logging

from database import db
from errors import NotFoundError
from models.category import Category
from models.task import Task
from models.user import User
from utils.time import utcnow
from utils.validators import parse_int_param, validate_task_payload

logger = logging.getLogger(__name__)


class TaskController:
    def __init__(self, notification_service):
        self.notifier = notification_service

    # --- leitura --------------------------------------------------------------
    def list_tasks(self):
        now = utcnow()
        result = []
        for task in Task.list_with_relations():
            data = task.to_dict()
            data['overdue'] = task.is_overdue(now)
            data['user_name'] = task.user.name if task.user else None
            data['category_name'] = task.category.name if task.category else None
            result.append(data)
        return result

    def get_task(self, task_id):
        task = self._get_or_404(task_id)
        data = task.to_dict()
        data['overdue'] = task.is_overdue()
        return data

    def search(self, args):
        priority = args.get('priority', '')
        user_id = args.get('user_id', '')
        tasks = Task.search(
            text=args.get('q', ''),
            status=args.get('status', ''),
            priority=parse_int_param(priority, 'Prioridade inválida') if priority else None,
            user_id=parse_int_param(user_id, 'user_id inválido') if user_id else None,
        )
        return [t.to_dict() for t in tasks]

    def stats(self):
        total = Task.count()
        by_status = Task.count_by_status()
        done = by_status.get('done', 0)
        return {
            'total': total,
            'pending': by_status.get('pending', 0),
            'in_progress': by_status.get('in_progress', 0),
            'done': done,
            'cancelled': by_status.get('cancelled', 0),
            'overdue': Task.count_overdue(utcnow()),
            'completion_rate': round((done / total) * 100, 2) if total > 0 else 0,
        }

    # --- escrita --------------------------------------------------------------
    def create_task(self, data):
        fields = validate_task_payload(data)
        assignee = self._check_references(fields)
        task = Task(**fields)
        db.session.add(task)
        db.session.commit()
        logger.info("Task criada: %s - %s", task.id, task.title)
        if assignee:
            self.notifier.notify_task_assigned(assignee, task)
        return task.to_dict()

    def update_task(self, task_id, data):
        task = self._get_or_404(task_id)
        fields = validate_task_payload(data, partial=True)
        assignee = self._check_references(fields)
        reassigned = 'user_id' in fields and fields['user_id'] != task.user_id
        for name, value in fields.items():
            setattr(task, name, value)
        task.updated_at = utcnow()
        db.session.commit()
        logger.info("Task atualizada: %s", task.id)
        if assignee and reassigned:
            self.notifier.notify_task_assigned(assignee, task)
        return task.to_dict()

    def delete_task(self, task_id):
        task = self._get_or_404(task_id)
        db.session.delete(task)
        db.session.commit()
        logger.info("Task deletada: %s", task_id)

    # --- auxiliares -----------------------------------------------------------
    @staticmethod
    def _get_or_404(task_id):
        task = Task.get(task_id)
        if not task:
            raise NotFoundError('Task não encontrada')
        return task

    @staticmethod
    def _check_references(fields):
        """Garante que usuário e categoria referenciados existem. Retorna o usuário atribuído (ou None)."""
        user = None
        if fields.get('user_id'):
            user = User.get(fields['user_id'])
            if not user:
                raise NotFoundError('Usuário não encontrado')
        if fields.get('category_id') and not Category.get(fields['category_id']):
            raise NotFoundError('Categoria não encontrada')
        return user

