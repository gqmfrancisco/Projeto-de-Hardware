
from flask import Blueprint, request, jsonify

from database import db
from models import Colaborador, Evento


eventos_bp = Blueprint("eventos", __name__)

TIPOS_VALIDOS = {
    "ENTRADA",
    "SAIDA",
    "ACESSO_NEGADO",
    "INVASAO"
}


def evento_json(evento):
    return {
        "id": evento.id,
        "colaborador_id": evento.colaborador_id,
        "rfid": evento.rfid,
        "tipo": evento.tipo,
        "data_hora": evento.data_hora.isoformat()
    }


@eventos_bp.route("/api/eventos", methods=["POST"])
def registrar_evento():

    dados = request.get_json(silent=True)

    if not isinstance(dados, dict):
        return jsonify({
            "erro": "Envie um JSON valido"
        }), 400

    rfid = dados.get("rfid")
    tipo = dados.get("tipo")

    if not isinstance(rfid, str) or not rfid.strip():
        return jsonify({
            "erro": "RFID obrigatorio"
        }), 400

    if tipo not in TIPOS_VALIDOS:
        return jsonify({
            "erro": "Tipo de evento invalido"
        }), 400

    rfid = rfid.strip()

    colaborador = Colaborador.query.filter_by(
        rfid=rfid
    ).first()

    # Impedir entrada/saida de colaboradores desconhecidos
    # ou sem permissao.
    if tipo in {"ENTRADA", "SAIDA"}:
        if (
            colaborador is None
            or not colaborador.ativo
            or not colaborador.autorizado
        ):
            return jsonify({
                "erro": "Colaborador sem permissao"
            }), 403

    # Acesso negado exige um colaborador conhecido sem permissao.
    if tipo == "ACESSO_NEGADO":
        if colaborador is None:
            return jsonify({
                "erro": "RFID desconhecido: utilize INVASAO"
            }), 400

        if colaborador.ativo and colaborador.autorizado:
            return jsonify({
                "erro": "Colaborador possui permissao"
            }), 400

    # Invasao representa RFID desconhecido.
    if tipo == "INVASAO" and colaborador is not None:
        return jsonify({
            "erro": "RFID conhecido: tipo INVASAO invalido"
        }), 400

    evento = Evento(
        colaborador_id=colaborador.id if colaborador else None,
        rfid=rfid,
        tipo=tipo
    )

    db.session.add(evento)
    db.session.commit()

    return jsonify({
        "mensagem": "Evento registrado!",
        "evento": evento_json(evento)
    }), 201


@eventos_bp.route("/api/eventos", methods=["GET"])
def listar_eventos():

    eventos = Evento.query.order_by(
        Evento.data_hora.desc(),
        Evento.id.desc()
    ).all()

    return jsonify([
        evento_json(evento)
        for evento in eventos
    ]), 200
