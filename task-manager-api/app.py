"""Entry point e composition root (application factory)."""
import logging

from flask import Flask
from flask_cors import CORS

from config import Settings
from controllers.category_controller import CategoryController
from controllers.report_controller import ReportController
from controllers.task_controller import TaskController
from controllers.user_controller import UserController
from database import db
from middlewares.error_handler import register_error_handlers
from routes.category_routes import create_category_blueprint
from routes.report_routes import create_report_blueprint
from routes.system_routes import create_system_blueprint
from routes.task_routes import create_task_blueprint
from routes.user_routes import create_user_blueprint
from services.notification_service import NotificationService
from services.token_service import TokenService


def create_app(settings=None):
    settings = settings or Settings()
    logging.basicConfig(level=logging.DEBUG if settings.DEBUG else logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI=settings.DATABASE_URL,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SECRET_KEY=settings.SECRET_KEY,
        DEBUG=settings.DEBUG,
        SETTINGS=settings,
    )
    CORS(app, origins=settings.CORS_ORIGINS)
    db.init_app(app)

    notification_service = NotificationService(
        host=settings.SMTP_HOST, port=settings.SMTP_PORT,
        user=settings.SMTP_USER, password=settings.SMTP_PASSWORD,
    )
    token_service = TokenService(settings.SECRET_KEY, settings.TOKEN_MAX_AGE_SECONDS)

    app.register_blueprint(create_system_blueprint())
    app.register_blueprint(create_task_blueprint(TaskController(notification_service)))
    app.register_blueprint(create_user_blueprint(UserController(token_service)))
    app.register_blueprint(create_report_blueprint(ReportController()))
    app.register_blueprint(create_category_blueprint(CategoryController()))
    register_error_handlers(app)

    with app.app_context():
        db.create_all()

    return app


if __name__ == '__main__':
    application = create_app()
    cfg = application.config['SETTINGS']
    application.run(host=cfg.HOST, port=cfg.PORT, debug=cfg.DEBUG)
