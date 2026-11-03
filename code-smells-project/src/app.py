"""Composition root: cria a aplicação, instancia models/services/controllers e registra as views."""
import logging

from flask import Flask
from flask_cors import CORS

from src import database
from src.config import Settings
from src.controllers.admin_controller import AdminController
from src.controllers.pedido_controller import PedidoController
from src.controllers.produto_controller import ProdutoController
from src.controllers.relatorio_controller import RelatorioController
from src.controllers.sistema_controller import SistemaController
from src.controllers.usuario_controller import UsuarioController
from src.middlewares.error_handler import register_error_handlers
from src.models.admin_model import AdminModel
from src.models.pedido_model import PedidoModel
from src.models.produto_model import ProdutoModel
from src.models.usuario_model import UsuarioModel
from src.services.notification_service import NotificationService
from src.views.pedido_routes import create_pedido_blueprint
from src.views.produto_routes import create_produto_blueprint
from src.views.sistema_routes import create_sistema_blueprint
from src.views.usuario_routes import create_usuario_blueprint


def create_app(settings=None):
    settings = settings or Settings()
    logging.basicConfig(level=logging.DEBUG if settings.DEBUG else logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    app = Flask(__name__)
    app.config.update(SECRET_KEY=settings.SECRET_KEY, DEBUG=settings.DEBUG, SETTINGS=settings)
    CORS(app, origins=settings.CORS_ORIGINS)

    database.init_app(app)

    # Models
    produto_model = ProdutoModel(database.get_db)
    usuario_model = UsuarioModel(database.get_db)
    pedido_model = PedidoModel(database.get_db)
    admin_model = AdminModel(database.get_db, settings.DATABASE_PATH)

    # Controllers (dependências injetadas)
    produto_controller = ProdutoController(produto_model)
    usuario_controller = UsuarioController(usuario_model)
    pedido_controller = PedidoController(pedido_model, produto_model, NotificationService())
    relatorio_controller = RelatorioController(pedido_model)
    sistema_controller = SistemaController(settings, produto_model, usuario_model, pedido_model)
    admin_controller = AdminController(admin_model)

    # Views
    app.register_blueprint(create_produto_blueprint(produto_controller))
    app.register_blueprint(create_usuario_blueprint(usuario_controller))
    app.register_blueprint(create_pedido_blueprint(pedido_controller))
    app.register_blueprint(create_sistema_blueprint(sistema_controller, relatorio_controller, admin_controller))

    register_error_handlers(app)
    return app
