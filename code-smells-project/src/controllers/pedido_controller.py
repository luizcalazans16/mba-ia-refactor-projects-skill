"""Casos de uso de pedidos: criação (com regra de estoque), listagem e mudança de status."""
from src.errors import NotFoundError, ValidationError
from src.utils.validators import validar_pedido, validar_status_pedido


class PedidoController:
    def __init__(self, pedido_model, produto_model, notification_service):
        self.pedidos = pedido_model
        self.produtos = produto_model
        self.notifier = notification_service

    def criar(self, dados):
        usuario_id, itens = validar_pedido(dados)

        produtos = self.produtos.buscar_por_ids({i["produto_id"] for i in itens})
        total = 0
        itens_precificados = []
        for item in itens:
            produto = produtos.get(item["produto_id"])
            if produto is None:
                raise ValidationError(f"Produto {item['produto_id']} não encontrado")
            if produto["estoque"] < item["quantidade"]:
                raise ValidationError(f"Estoque insuficiente para {produto['nome']}")
            total = total + produto["preco"] * item["quantidade"]
            itens_precificados.append({**item, "preco_unitario": produto["preco"]})

        pedido_id = self.pedidos.criar(usuario_id, itens_precificados, total)
        self.notifier.pedido_criado(pedido_id, usuario_id)
        return {"pedido_id": pedido_id, "total": total}

    def listar(self, usuario_id=None):
        return self.pedidos.listar(usuario_id)

    def atualizar_status(self, pedido_id, dados):
        status = validar_status_pedido(dados)
        if not self.pedidos.existe(pedido_id):
            raise NotFoundError("Pedido não encontrado")
        self.pedidos.atualizar_status(pedido_id, status)
        self.notifier.status_alterado(pedido_id, status)
