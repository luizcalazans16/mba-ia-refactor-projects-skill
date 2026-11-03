"""Casos de uso de usuários e autenticação."""
import logging

from src.config.settings import TIPO_USUARIO_PADRAO
from src.errors import NotFoundError, UnauthorizedError
from src.services.password_service import hash_password, is_hashed, verify_password
from src.utils.validators import validar_login, validar_novo_usuario

logger = logging.getLogger(__name__)


class UsuarioController:
    def __init__(self, usuario_model):
        self.usuarios = usuario_model

    def listar(self):
        return self.usuarios.listar()

    def buscar(self, usuario_id):
        usuario = self.usuarios.buscar_por_id(usuario_id)
        if not usuario:
            raise NotFoundError("Usuário não encontrado")
        return usuario

    def criar(self, dados):
        novo = validar_novo_usuario(dados)
        usuario_id = self.usuarios.criar(novo["nome"], novo["email"], hash_password(novo["senha"]), TIPO_USUARIO_PADRAO)
        logger.info("Usuário criado: id=%s", usuario_id)
        return usuario_id

    def login(self, dados):
        email, senha = validar_login(dados)
        registro = self.usuarios.buscar_credenciais(email)
        if not registro or not verify_password(registro["senha"], senha):
            logger.info("Login falhou")
            raise UnauthorizedError("Email ou senha inválidos")

        if not is_hashed(registro["senha"]):  # migra senha legada em texto puro
            self.usuarios.atualizar_senha(registro["id"], hash_password(senha))

        logger.info("Login bem-sucedido: id=%s", registro["id"])
        return {k: registro[k] for k in ("id", "nome", "email", "tipo")}
