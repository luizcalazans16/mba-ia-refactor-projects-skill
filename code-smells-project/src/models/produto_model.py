"""Model de produtos: acesso a dados da tabela `produtos` (queries sempre parametrizadas)."""

COLUNAS = "id, nome, descricao, preco, estoque, categoria, ativo, criado_em"


def _to_dict(row):
    return dict(row) if row else None


class ProdutoModel:
    def __init__(self, get_connection):
        self._db = get_connection

    def listar(self):
        rows = self._db().execute(f"SELECT {COLUNAS} FROM produtos ORDER BY id").fetchall()
        return [_to_dict(row) for row in rows]

    def buscar_por_id(self, produto_id):
        row = self._db().execute(f"SELECT {COLUNAS} FROM produtos WHERE id = ?", (produto_id,)).fetchone()
        return _to_dict(row)

    def buscar_por_ids(self, produto_ids):
        if not produto_ids:
            return {}
        placeholders = ", ".join("?" for _ in produto_ids)
        rows = self._db().execute(
            f"SELECT {COLUNAS} FROM produtos WHERE id IN ({placeholders})", tuple(produto_ids)
        ).fetchall()
        return {row["id"]: _to_dict(row) for row in rows}

    def pesquisar(self, termo=None, categoria=None, preco_min=None, preco_max=None):
        clausulas, params = [], []
        if termo:
            clausulas.append("(nome LIKE ? OR descricao LIKE ?)")
            params += [f"%{termo}%", f"%{termo}%"]
        if categoria:
            clausulas.append("categoria = ?")
            params.append(categoria)
        if preco_min is not None:
            clausulas.append("preco >= ?")
            params.append(preco_min)
        if preco_max is not None:
            clausulas.append("preco <= ?")
            params.append(preco_max)
        where = " AND ".join(clausulas) or "1=1"
        rows = self._db().execute(f"SELECT {COLUNAS} FROM produtos WHERE {where} ORDER BY id", params).fetchall()
        return [_to_dict(row) for row in rows]

    def criar(self, nome, descricao, preco, estoque, categoria):
        db = self._db()
        with db:
            cursor = db.execute(
                "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
                (nome, descricao, preco, estoque, categoria),
            )
        return cursor.lastrowid

    def atualizar(self, produto_id, nome, descricao, preco, estoque, categoria):
        db = self._db()
        with db:
            db.execute(
                "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
                (nome, descricao, preco, estoque, categoria, produto_id),
            )

    def deletar(self, produto_id):
        db = self._db()
        with db:
            db.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))

    def contar(self):
        return self._db().execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
