from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError

from database import db
from models import Colaborador


colaboradores_bp = Blueprint("colaboradores", __name__)


def colaborador_json(c):
    return {
        "id": c.id,
        "nome": c.nome,
        "matricula": c.matricula,
        "rfid": c.rfid,
        "cargo": c.cargo,
        "autorizado": c.autorizado,
        "ativo": c.ativo
    }


# LISTAR COLABORADORES
@colaboradores_bp.route("/api/colaboradores", methods=["GET"])
def listar():
    colaboradores = Colaborador.query.order_by(Colaborador.id).all()

    return jsonify([
        colaborador_json(c) for c in colaboradores
    ]), 200


# BUSCAR COLABORADOR POR ID
@colaboradores_bp.route("/api/colaboradores/<int:id>", methods=["GET"])
def buscar(id):
    colaborador = db.get_or_404(Colaborador, id)

    return jsonify(colaborador_json(colaborador)), 200


# CADASTRAR COLABORADOR
@colaboradores_bp.route("/api/colaboradores", methods=["POST"])
def cadastrar():
    dados = request.get_json(silent=True)

    if not isinstance(dados, dict):
        return jsonify({"erro": "Envie um JSON valido"}), 400

    obrigatorios = ["nome", "matricula", "rfid", "cargo"]

    for campo in obrigatorios:
        if not isinstance(dados.get(campo), str) or not dados[campo].strip():
            return jsonify({"erro": f"Campo obrigatorio: {campo}"}), 400

    for campo in ["autorizado", "ativo"]:
        if campo in dados and not isinstance(dados[campo], bool):
            return jsonify({"erro": f"{campo} deve ser booleano"}), 400

    colaborador = Colaborador(
        nome=dados["nome"].strip(),
        matricula=dados["matricula"].strip(),
        rfid=dados["rfid"].strip(),
        cargo=dados["cargo"].strip(),
        autorizado=dados.get("autorizado", False),
        ativo=dados.get("ativo", True)
    )

    try:
        db.session.add(colaborador)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"erro": "Matricula ou RFID ja cadastrado"}), 409

    return jsonify({
        "mensagem": "Colaborador cadastrado!",
        "colaborador": colaborador_json(colaborador)
    }), 201


# ATUALIZAR COLABORADOR
@colaboradores_bp.route("/api/colaboradores/<int:id>", methods=["PUT"])
def atualizar(id):
    colaborador = db.get_or_404(Colaborador, id)
    dados = request.get_json(silent=True)

    if not isinstance(dados, dict):
        return jsonify({"erro": "Envie um JSON valido"}), 400

    for campo in ["nome", "matricula", "rfid", "cargo"]:
        if campo in dados:
            valor = dados[campo]

            if not isinstance(valor, str) or not valor.strip():
                return jsonify({"erro": f"Valor invalido: {campo}"}), 400

            setattr(colaborador, campo, valor.strip())

    for campo in ["autorizado", "ativo"]:
        if campo in dados:
            if not isinstance(dados[campo], bool):
                return jsonify({"erro": f"{campo} deve ser booleano"}), 400

            setattr(colaborador, campo, dados[campo])

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"erro": "Matricula ou RFID ja cadastrado"}), 409

    return jsonify({
        "mensagem": "Colaborador atualizado!",
        "colaborador": colaborador_json(colaborador)
    }), 200


# DESATIVAR COLABORADOR
@colaboradores_bp.route("/api/colaboradores/<int:id>", methods=["DELETE"])
def excluir(id):
    colaborador = db.get_or_404(Colaborador, id)

    # Exclusao logica: preserva o historico de acessos
    colaborador.ativo = False
    db.session.commit()

    return jsonify({
        "mensagem": "Colaborador desativado com sucesso"
    }), 200