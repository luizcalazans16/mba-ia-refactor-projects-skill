from sqlalchemy import func
from sqlalchemy.orm import joinedload

from config.settings import CLOSED_STATUSES, DEFAULT_PRIORITY, DEFAULT_STATUS
from database import db
from utils.time import utcnow


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=DEFAULT_STATUS)
    priority = db.Column(db.Integer, default=DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship('User', backref='tasks')
    category = db.relationship('Category', backref='tasks')

    # --- regras da entidade ---------------------------------------------------
    def is_overdue(self, now=None):
        now = now or utcnow()
        return bool(self.due_date and self.due_date < now and self.status not in CLOSED_STATUSES)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'user_id': self.user_id,
            'category_id': self.category_id,
            'created_at': str(self.created_at),
            'updated_at': str(self.updated_at),
            'due_date': str(self.due_date) if self.due_date else None,
            'tags': self.tags.split(',') if self.tags else [],
        }

    # --- acesso a dados -------------------------------------------------------
    @classmethod
    def get(cls, task_id):
        return db.session.get(cls, task_id)

    @classmethod
    def list_with_relations(cls):
        stmt = db.select(cls).options(joinedload(cls.user), joinedload(cls.category)).order_by(cls.id)
        return db.session.scalars(stmt).all()

    @classmethod
    def list_by_user(cls, user_id):
        return db.session.scalars(db.select(cls).filter_by(user_id=user_id).order_by(cls.id)).all()

    @classmethod
    def search(cls, text=None, status=None, priority=None, user_id=None):
        stmt = db.select(cls)
        if text:
            stmt = stmt.where(db.or_(cls.title.like(f'%{text}%'), cls.description.like(f'%{text}%')))
        if status:
            stmt = stmt.where(cls.status == status)
        if priority is not None:
            stmt = stmt.where(cls.priority == priority)
        if user_id is not None:
            stmt = stmt.where(cls.user_id == user_id)
        return db.session.scalars(stmt.order_by(cls.id)).all()

    @classmethod
    def count(cls):
        return db.session.scalar(db.select(func.count(cls.id)))

    @classmethod
    def count_by_status(cls, user_id=None):
        stmt = db.select(cls.status, func.count(cls.id)).group_by(cls.status)
        if user_id is not None:
            stmt = stmt.where(cls.user_id == user_id)
        return dict(db.session.execute(stmt).all())

    @classmethod
    def count_by_priority(cls):
        return dict(db.session.execute(db.select(cls.priority, func.count(cls.id)).group_by(cls.priority)).all())

    @classmethod
    def _overdue_filter(cls, now):
        return db.and_(cls.due_date.is_not(None), cls.due_date < now, cls.status.not_in(CLOSED_STATUSES))

    @classmethod
    def list_overdue(cls, now):
        return db.session.scalars(db.select(cls).where(cls._overdue_filter(now)).order_by(cls.id)).all()

    @classmethod
    def count_overdue(cls, now, user_id=None):
        stmt = db.select(func.count(cls.id)).where(cls._overdue_filter(now))
        if user_id is not None:
            stmt = stmt.where(cls.user_id == user_id)
        return db.session.scalar(stmt)

    @classmethod
    def count_high_priority(cls, threshold, user_id):
        stmt = db.select(func.count(cls.id)).where(cls.priority <= threshold, cls.user_id == user_id)
        return db.session.scalar(stmt)

    @classmethod
    def count_created_since(cls, since):
        return db.session.scalar(db.select(func.count(cls.id)).where(cls.created_at >= since))

    @classmethod
    def count_done_since(cls, since):
        return db.session.scalar(
            db.select(func.count(cls.id)).where(cls.status == 'done', cls.updated_at >= since))

    @classmethod
    def delete_by_user(cls, user_id):
        db.session.execute(db.delete(cls).where(cls.user_id == user_id))
