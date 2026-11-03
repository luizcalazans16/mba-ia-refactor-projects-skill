"""Relatórios agregados (queries agrupadas, sem N+1)."""
from datetime import timedelta

from config.settings import HIGH_PRIORITY_THRESHOLD, PRIORITY_LABELS, RECENT_ACTIVITY_DAYS, TASK_STATUSES
from errors import NotFoundError
from models.category import Category
from models.task import Task
from models.user import User
from utils.time import utcnow


def _rate(part, total):
    return round((part / total) * 100, 2) if total > 0 else 0


class ReportController:
    def summary(self):
        now = utcnow()
        since = now - timedelta(days=RECENT_ACTIVITY_DAYS)
        by_status = Task.count_by_status()
        by_priority = Task.count_by_priority()
        overdue = [
            {
                'id': t.id,
                'title': t.title,
                'due_date': str(t.due_date),
                'days_overdue': (now - t.due_date).days,
            }
            for t in Task.list_overdue(now)
        ]
        user_productivity = [
            {
                'user_id': user.id,
                'user_name': user.name,
                'total_tasks': total,
                'completed_tasks': completed,
                'completion_rate': _rate(completed, total),
            }
            for user, total, completed in User.list_with_task_stats()
        ]
        return {
            'generated_at': str(now),
            'overview': {
                'total_tasks': Task.count(),
                'total_users': User.count(),
                'total_categories': Category.count(),
            },
            'tasks_by_status': {status: by_status.get(status, 0) for status in TASK_STATUSES},
            'tasks_by_priority': {label: by_priority.get(p, 0) for p, label in PRIORITY_LABELS.items()},
            'overdue': {'count': len(overdue), 'tasks': overdue},
            'recent_activity': {
                'tasks_created_last_7_days': Task.count_created_since(since),
                'tasks_completed_last_7_days': Task.count_done_since(since),
            },
            'user_productivity': user_productivity,
        }

    def user_report(self, user_id):
        user = User.get(user_id)
        if not user:
            raise NotFoundError('Usuário não encontrado')
        by_status = Task.count_by_status(user_id=user_id)
        total = sum(by_status.values())
        done = by_status.get('done', 0)
        return {
            'user': {'id': user.id, 'name': user.name, 'email': user.email},
            'statistics': {
                'total_tasks': total,
                'done': done,
                'pending': by_status.get('pending', 0),
                'in_progress': by_status.get('in_progress', 0),
                'cancelled': by_status.get('cancelled', 0),
                'overdue': Task.count_overdue(utcnow(), user_id=user_id),
                'high_priority': Task.count_high_priority(HIGH_PRIORITY_THRESHOLD, user_id),
                'completion_rate': _rate(done, total),
            },
        }
