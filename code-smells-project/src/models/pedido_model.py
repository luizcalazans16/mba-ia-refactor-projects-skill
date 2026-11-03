"""Model de pedidos e itens de pedido."""
from collections import defaultdict

from src.config.settings import STATUS_PEDIDO_INICIAL


class PedidoModel:
    def __init__(self, get_connection):
        self._db = get_connection

    def criar(self, usuario_id, itens, total):
        """Grava pedido, itens e baixa de estoque numa única transação.

        `itens` já deve estar validado: lista de dicts com produto_id, quantidade e preco_unitario.
        """
        db = self._db()
        with db:  # commit no sucesso, rollback em qualquer exceção
            cursor = db.execute(
                "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
                (usuario_id, STATUS_PEDIDO_INICIAL, total),
            )
            pedido_id = cursor.lastrowid
            db.executemany(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                [(pedido_id, i["produto_id"], i["quantidade"], i["preco_unitario"]) for i in itens],
            )
            db.executemany(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
                [(i["quantidade"], i["produto_id"]) for i in itens],
            )
        return pedido_id

    def listar(self, usuario_id=None):
        """Lista pedidos com itens em 2 queries (sem N+1)."""
        db = self._db()
        filtro, params = ("WHERE usuario_id = ?", (usuario_id,)) if usuario_id is not None else ("", ())
        pedidos = db.execute(
            f"SELECT id, usuario_id, status, total, criado_em FROM pedidos {filtro} ORDER BY id", params
        ).fetchall()
        if not pedidos:
            return []

        ids = [p["id"] for p in pedidos]
        placeholders = ", ".join("?" for _ in ids)
        itens = db.execute(
            f"""
            SELECT i.pedido_id, i.produto_id, i.quantidade, i.preco_unitario,
                   COALESCE(p.nome, 'Desconhecido') AS produto_nome
            FROM itens_pedido i
            LEFT JOIN produtos p ON p.id = i.produto_id
            WHERE i.pedido_id IN ({placeholders})
            ORDER BY i.id
            """,
            ids,
        ).fetchall()

        itens_por_pedido = defaultdict(list)
        for item in itens:
            itens_por_pedido[item["pedido_id"]].append({
                "produto_id": item["produto_id"],
                "produto_nome": item["produto_nome"],
                "quantidade": item["quantidade"],
                "preco_unitario": item["preco_unitario"],
            })
        return [{**dict(p), "itens": itens_por_pedido[p["id"]]} for p in pedidos]

    def existe(self, pedido_id):
        return self._db().execute("SELECT 1 FROM pedidos WHERE id = ?", (pedido_id,)).fetchone() is not None

    def atualizar_status(self, pedido_id, status):
        db = self._db()
        with db:
            db.execute("UPDATE pedidos SET status = ? WHERE id = ?", (status, pedido_id))

    def resumo_vendas(self):
        """Totais de pedidos e faturamento em uma única query de agregação."""
        row = self._db().execute(
            """
            SELECT COUNT(*) AS total_pedidos,
                   COALESCE(SUM(total), 0) AS faturamento,
                   COALESCE(SUM(CASE WHEN status = 'pendente' THEN 1 ELSE 0 END), 0) AS pendentes,
                   COALESCE(SUM(CASE WHEN status = 'aprovado' THEN 1 ELSE 0 END), 0) AS aprovados,
                   COALESCE(SUM(CASE WHEN status = 'cancelado' THEN 1 ELSE 0 END), 0) AS cancelados
            FROM pedidos
            """
        ).fetchone()
        return dict(row)

    def contar(self):
        return self._db().execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
