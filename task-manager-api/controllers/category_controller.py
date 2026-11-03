"""Casos de uso de categorias (antes misturados no blueprint de relatórios)."""
from database import db
from errors import NotFoundError
from models.category import Category
from utils.validators import validate_category_payload


class CategoryController:
    def list_categories(self):
        result = []
        for category, task_count in Category.list_with_task_counts():
            data = category.to_dict()
            data['task_count'] = task_count
            result.append(data)
        return result

    def create_category(self, data):
        category = Category(**validate_category_payload(data))
        db.session.add(category)
        db.session.commit()
        return category.to_dict()

    def update_category(self, category_id, data):
        category = self._get_or_404(category_id)
        for name, value in validate_category_payload(data, partial=True).items():
            setattr(category, name, value)
        db.session.commit()
        return category.to_dict()

    def delete_category(self, category_id):
        category = self._get_or_404(category_id)
        db.session.delete(category)
        db.session.commit()

    @staticmethod
    def _get_or_404(category_id):
        category = Category.get(category_id)
        if not category:
            raise NotFoundError('Categoria não encontrada')
        return category
