from flask import Blueprint, jsonify, request

from src.middlewares.admin_auth import require_admin_token


def create_sistema_blueprint(sistema_controller, relatorio_controller, admin_controller):
    bp = Blueprint("sistema", __name__)

    @bp.get("/")
    def index():
        return jsonify(sistema_controller.indice())

    @bp.get("/health")
    def health_check():
        return jsonify(sistema_controller.health()), 200

    @bp.get("/relatorios/vendas")
    def relatorio_vendas():
        return jsonify({"dados": relatorio_controller.vendas(), "sucesso": True}), 200

    @bp.post("/admin/reset-db")
    @require_admin_token
    def reset_database():
        admin_controller.resetar_banco()
        return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200

    @bp.post("/admin/query")
    @require_admin_token
    def executar_query():
        resultado = admin_controller.consultar(request.get_json(silent=True))
        return jsonify({"dados": resultado, "sucesso": True}), 200

    return bp
