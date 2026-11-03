"""Validação de payloads. Cada função recebe o JSON bruto e devolve dados limpos ou lança ValidationError."""
from src.config.settings import (
    CATEGORIA_PADRAO,
    CATEGORIAS_VALIDAS,
    NOME_PRODUTO_MAX,
    NOME_PRODUTO_MIN,
    STATUS_PEDIDO_VALIDOS,
)
from src.errors import ValidationError


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def require_object(dados):
    if not dados or not isinstance(dados, dict):
        raise ValidationError("Dados inválidos")
    return dados


def validar_produto(dados):
    dados = require_object(dados)
    for campo, rotulo in (("nome", "Nome"), ("preco", "Preço"), ("estoque", "Estoque")):
        if campo not in dados:
            raise ValidationError(f"{rotulo} é obrigatório")

    nome = dados["nome"]
    descricao = dados.get("descricao", "")
    preco = dados["preco"]
    estoque = dados["estoque"]
    categoria = dados.get("categoria", CATEGORIA_PADRAO)

    if not isinstance(nome, str):
        raise ValidationError("Nome inválido")
    if not _is_number(preco):
        raise ValidationError("Preço inválido")
    if not _is_int(estoque):
        raise ValidationError("Estoque inválido")
    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")
    if len(nome) < NOME_PRODUTO_MIN:
        raise ValidationError("Nome muito curto")
    if len(nome) > NOME_PRODUTO_MAX:
        raise ValidationError("Nome muito longo")
    if categoria not in CATEGORIAS_VALIDAS:
        raise ValidationError("Categoria inválida. Válidas: " + str(list(CATEGORIAS_VALIDAS)))

    return {
        "nome": nome,
        "descricao": descricao if isinstance(descricao, str) else "",
        "preco": preco,
        "estoque": estoque,
        "categoria": categoria,
    }


def validar_filtros_busca(args):
    def _float(nome):
        valor = args.get(nome)
        if not valor:
            return None
        try:
            return float(valor)
        except ValueError:
            raise ValidationError(f"Parâmetro {nome} inválido")

    return {
        "termo": args.get("q", ""),
        "categoria": args.get("categoria") or None,
        "preco_min": _float("preco_min"),
        "preco_max": _float("preco_max"),
    }


def validar_novo_usuario(dados):
    dados = require_object(dados)
    nome, email, senha = dados.get("nome", ""), dados.get("email", ""), dados.get("senha", "")
    if not all(isinstance(v, str) and v for v in (nome, email, senha)):
        raise ValidationError("Nome, email e senha são obrigatórios")
    return {"nome": nome, "email": email, "senha": senha}


def validar_login(dados):
    dados = dados if isinstance(dados, dict) else {}
    email, senha = dados.get("email", ""), dados.get("senha", "")
    if not (isinstance(email, str) and email and isinstance(senha, str) and senha):
        raise ValidationError("Email e senha são obrigatórios")
    return email, senha


def validar_pedido(dados):
    dados = require_object(dados)
    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])
    if not usuario_id:
        raise ValidationError("Usuario ID é obrigatório")
    if not itens:
        raise ValidationError("Pedido deve ter pelo menos 1 item")
    if not _is_int(usuario_id) or not isinstance(itens, list):
        raise ValidationError("Dados inválidos")
    for item in itens:
        if not (
            isinstance(item, dict)
            and _is_int(item.get("produto_id"))
            and _is_int(item.get("quantidade"))
            and item["quantidade"] > 0
        ):
            raise ValidationError("Item de pedido inválido: informe produto_id e quantidade (> 0)")
    return usuario_id, [{"produto_id": i["produto_id"], "quantidade": i["quantidade"]} for i in itens]


def validar_status_pedido(dados):
    status = dados.get("status", "") if isinstance(dados, dict) else ""
    if status not in STATUS_PEDIDO_VALIDOS:
        raise ValidationError("Status inválido")
    return status
