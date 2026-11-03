"""Notificações de pedidos. Hoje apenas registra em log; o ponto de troca por e-mail/SMS/push real é aqui."""
import logging


class NotificationService:
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger("notifications")

    def pedido_criado(self, pedido_id, usuario_id):
        self.logger.info("EMAIL: pedido %s criado para usuario %s", pedido_id, usuario_id)
        self.logger.info("SMS: seu pedido foi recebido")
        self.logger.info("PUSH: novo pedido recebido pelo sistema")

    def status_alterado(self, pedido_id, status):
        if status == "aprovado":
            self.logger.info("Pedido %s aprovado: preparar envio", pedido_id)
        elif status == "cancelado":
            self.logger.info("Pedido %s cancelado: devolver estoque", pedido_id)
