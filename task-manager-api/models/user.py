import hashlib
import hmac
import re

from sqlalchemy import case, func
from werkzeug.security import check_password_hash, generate_password_hash

from database import db
from utils.time import utcnow

_LEGACY_MD5 = re.compile(r"^[0-9a-f]{32}$")


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='user')
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        # O hash da senha nunca é serializado.
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at),
        }

    def set_password(self, pwd):
        self.password = generate_password_hash(pwd)

    def has_legacy_password_hash(self):
        return bool(_LEGACY_MD5.match(self.password or ''))

    def check_password(self, pwd):
        if self.has_legacy_password_hash():  # hashes MD5 antigos: verifica e deixa o controller migrar
            return hmac.compare_digest(self.password, hashlib.md5(pwd.encode()).hexdigest())
        return check_password_hash(self.password, pwd)

    def is_admin(self):
        return self.role == 'admin'

    # --- acesso a dados -------------------------------------------------------
    @classmethod
    def get(cls, user_id):
        return db.session.get(cls, user_id)

    @classmethod
    def find_by_email(cls, email):
        return db.session.scalars(db.select(cls).filter_by(email=email)).first()

    @classmethod
    def count(cls):
        return db.session.scalar(db.select(func.count(cls.id)))

    @classmethod
    def list_with_task_stats(cls):
        """[(user, total_tasks, completed_tasks)] em uma única query."""
        from models.task import Task

        stmt = (
            db.select(
                cls,
                func.count(Task.id),
                func.coalesce(func.sum(case((Task.status == 'done', 1), else_=0)), 0),
            )
            .outerjoin(Task, Task.user_id == cls.id)
            .group_by(cls.id)
            .order_by(cls.id)
        )
        return db.session.execute(stmt).all()
