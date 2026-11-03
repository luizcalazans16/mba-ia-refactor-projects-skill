"""Operações administrativas sobre o banco (usadas apenas pelos endpoints /admin protegidos)."""
import sqlite3

TABELAS_EM_ORDEM_DE_LIMPEZA = ("itens_pedido", "pedidos", "produtos", "usuarios")


class AdminModel:
    def __init__(self, get_connection, database_path):
        self._db = get_connection
        self._database_path = database_path

    def limpar_banco(self):
        db = self._db()
        with db:
            for tabela in TABELAS_EM_ORDEM_DE_LIMPEZA:
                db.execute(f"DELETE FROM {tabela}")  # nomes de tabela constantes, sem entrada externa

    def consulta_somente_leitura(self, sql):
        """Executa uma consulta numa conexão aberta em modo read-only: o SQLite rejeita qualquer escrita."""
        connection = sqlite3.connect(f"file:{self._database_path}?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        try:
            return [dict(row) for row in connection.execute(sql).fetchall()]
        finally:
            connection.close()
