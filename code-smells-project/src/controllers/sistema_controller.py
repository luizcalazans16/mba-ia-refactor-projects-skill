"""Informações do sistema: índice da API e health check (sem expor configuração interna)."""


class SistemaController:
    def __init__(self, settings, produto_model, usuario_model, pedido_model):
        self.settings = settings
        self.produtos = produto_model
        self.usuarios = usuario_model
        self.pedidos = pedido_model

    def indice(self):
        return {
            "mensagem": "Bem-vindo à API da Loja",
            "versao": self.settings.APP_VERSION,
            "endpoints": {
                "produtos": "/produtos",
                "usuarios": "/usuarios",
                "pedidos": "/pedidos",
                "login": "/login",
                "relatorios": "/relatorios/vendas",
                "health": "/health",
            },
        }

    def health(self):
        return {
            "status": "ok",
            "database": "connected",
            "counts": {
                "produtos": self.produtos.contar(),
                "usuarios": self.usuarios.contar(),
                "pedidos": self.pedidos.contar(),
            },
            "versao": self.settings.APP_VERSION,
            "ambiente": self.settings.ENVIRONMENT,
        }
