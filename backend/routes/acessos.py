
from flask import Blueprint, request, jsonify

from models import Colaborador


acessos_bp = Blueprint("acessos", __name__)


@acessos_bp.route("/api/acessos/validar", methods=["POST"])
def validar_acesso():

    dados = request.get_json(silent=True)

    # Verificar se recebemos um JSON valido
    if not isinstance(dados, dict):
        return jsonify({
            "erro": "Envie um JSON valido"
        }), 400

    rfid = dados.get("rfid")

    # Verificar se o RFID foi informado
    if not isinstance(rfid, str) or not rfid.strip():
        return jsonify({
            "erro": "O campo rfid e obrigatorio"
        }), 400

    rfid = rfid.strip()

    # Procurar o RFID no banco de dados
    colaborador = Colaborador.query.filter_by(
        rfid=rfid
    ).first()

    # RFID desconhecido
    if colaborador is None:
        return jsonify({
            "autorizado": False,
            "situacao": "DESCONHECIDO",
            "mensagem": "RFID nao cadastrado",
            "colaborador_id": None
        }), 200

    # Colaborador inativo
    if not colaborador.ativo:
        return jsonify({
            "autorizado": False,
            "situacao": "NEGADO",
            "motivo": "COLABORADOR_INATIVO",
            "mensagem": "Colaborador inativo",
            "colaborador_id": colaborador.id
        }), 200

    # Colaborador sem autorizacao
    if not colaborador.autorizado:
        return jsonify({
            "autorizado": False,
            "situacao": "NEGADO",
            "motivo": "SEM_PERMISSAO",
            "mensagem": "Acesso nao autorizado",
            "colaborador_id": colaborador.id
        }), 200

    # Acesso permitido
    return jsonify({
        "autorizado": True,
        "situacao": "AUTORIZADO",
        "mensagem": f"Bem-vindo, {colaborador.nome}!",
        "colaborador_id": colaborador.id,
        "nome": colaborador.nome
    }), 200
