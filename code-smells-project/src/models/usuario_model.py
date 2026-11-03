"""Model de usuários. A senha nunca sai deste módulo: as leituras públicas não incluem a coluna `senha`."""

COLUNAS_PUBLICAS = "id, nome, email, tipo, criado_em"


def _to_dict(row):
    return dict(row) if row else None


class UsuarioModel:
    def __init__(self, get_connection):
        self._db = get_connection

    def listar(self):
        rows = self._db().execute(f"SELECT {COLUNAS_PUBLICAS} FROM usuarios ORDER BY id").fetchall()
        return [_to_dict(row) for row in rows]

    def buscar_por_id(self, usuario_id):
        row = self._db().execute(
            f"SELECT {COLUNAS_PUBLICAS} FROM usuarios WHERE id = ?", (usuario_id,)
        ).fetchone()
        return _to_dict(row)

    def buscar_credenciais(self, email):
        """Retorna o registro com o hash da senha — uso exclusivo do fluxo de login."""
        row = self._db().execute(
            "SELECT id, nome, email, tipo, senha FROM usuarios WHERE email = ? ORDER BY id LIMIT 1", (email,)
        ).fetchone()
        return _to_dict(row)

    def criar(self, nome, email, senha_hash, tipo):
        db = self._db()
        with db:
            cursor = db.execute(
                "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
                (nome, email, senha_hash, tipo),
            )
        return cursor.lastrowid

    def atualizar_senha(self, usuario_id, senha_hash):
        db = self._db()
        with db:
            db.execute("UPDATE usuarios SET senha = ? WHERE id = ?", (senha_hash, usuario_id))

    def contar(self):
        return self._db().execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
