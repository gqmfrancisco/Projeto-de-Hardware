
from datetime import datetime, timezone, date, time, timedelta
import csv
import io

from flask import Blueprint, request, jsonify, Response, current_app

from database import db
from models import Colaborador, Evento


acessos_bp = Blueprint("acessos", __name__)


# ============================================================
# VALIDAÇÃO SIMPLES DO RFID
# ============================================================

@acessos_bp.route("/api/acessos/validar", methods=["POST"])
def validar_acesso():
    dados = request.get_json(silent=True)

    if not isinstance(dados, dict):
        return jsonify({
            "erro": "Envie um JSON valido"
        }), 400

    rfid = dados.get("rfid")

    if not isinstance(rfid, str) or not rfid.strip():
        return jsonify({
            "erro": "O campo rfid e obrigatorio"
        }), 400

    rfid = rfid.strip()
    colaborador = Colaborador.query.filter_by(rfid=rfid).first()

    if colaborador is None:
        return jsonify({
            "autorizado": False,
            "situacao": "DESCONHECIDO",
            "mensagem": "RFID nao cadastrado",
            "colaborador_id": None
        }), 200

    if not colaborador.ativo:
        return jsonify({
            "autorizado": False,
            "situacao": "NEGADO",
            "motivo": "COLABORADOR_INATIVO",
            "mensagem": "Colaborador inativo",
            "colaborador_id": colaborador.id
        }), 200

    if not colaborador.autorizado:
        return jsonify({
            "autorizado": False,
            "situacao": "NEGADO",
            "motivo": "SEM_PERMISSAO",
            "mensagem": "Acesso nao autorizado",
            "colaborador_id": colaborador.id
        }), 200

    return jsonify({
        "autorizado": True,
        "situacao": "AUTORIZADO",
        "mensagem": f"Bem-vindo, {colaborador.nome}!",
        "colaborador_id": colaborador.id,
        "nome": colaborador.nome
    }), 200


# ============================================================
# REGISTRO COMPLETO DE ACESSO
# ============================================================

@acessos_bp.route("/api/acessos/registrar", methods=["POST"])
def registrar_acesso():
    dados = request.get_json(silent=True)

    if not isinstance(dados, dict):
        return jsonify({
            "erro": "Envie um JSON valido"
        }), 400

    rfid = dados.get("rfid")

    if not isinstance(rfid, str) or not rfid.strip():
        return jsonify({
            "erro": "O campo rfid e obrigatorio"
        }), 400

    rfid = rfid.strip()

    colaborador = Colaborador.query.filter_by(
        rfid=rfid
    ).first()

    # RFID desconhecido: possível invasão.
    if colaborador is None:
        evento = Evento(
            colaborador_id=None,
            rfid=rfid,
            tipo="INVASAO"
        )

        db.session.add(evento)
        db.session.commit()

        return jsonify({
            "autorizado": False,
            "situacao": "INVASAO",
            "mensagem": "RFID nao cadastrado.",
            "colaborador_id": None,
            "rfid": rfid
        }), 200

    # Colaborador inativo.
    if not colaborador.ativo:
        evento = Evento(
            colaborador_id=colaborador.id,
            rfid=rfid,
            tipo="ACESSO_NEGADO"
        )

        db.session.add(evento)
        db.session.commit()

        return jsonify({
            "autorizado": False,
            "situacao": "NEGADO",
            "motivo": "COLABORADOR_INATIVO",
            "mensagem": "Colaborador inativo.",
            "colaborador_id": colaborador.id,
            "nome": colaborador.nome,
            "rfid": rfid
        }), 200

    # Colaborador sem permissão.
    if not colaborador.autorizado:
        evento = Evento(
            colaborador_id=colaborador.id,
            rfid=rfid,
            tipo="ACESSO_NEGADO"
        )

        db.session.add(evento)
        db.session.commit()

        return jsonify({
            "autorizado": False,
            "situacao": "NEGADO",
            "motivo": "SEM_PERMISSAO",
            "mensagem": "Acesso nao autorizado.",
            "colaborador_id": colaborador.id,
            "nome": colaborador.nome,
            "rfid": rfid
        }), 200

    # Descobre se o colaborador está dentro ou fora.
    ultimo_evento = Evento.query.filter(
        Evento.colaborador_id == colaborador.id,
        Evento.tipo.in_(["ENTRADA", "SAIDA"])
    ).order_by(
        Evento.data_hora.desc(),
        Evento.id.desc()
    ).first()

    esta_dentro = (
        ultimo_evento is not None
        and ultimo_evento.tipo == "ENTRADA"
    )

    # Registrar saída.
    if esta_dentro:
        evento = Evento(
            colaborador_id=colaborador.id,
            rfid=rfid,
            tipo="SAIDA"
        )

        db.session.add(evento)
        db.session.commit()

        return jsonify({
            "autorizado": True,
            "situacao": "SAIDA",
            "mensagem": f"Saida registrada para {colaborador.nome}.",
            "colaborador_id": colaborador.id,
            "nome": colaborador.nome,
            "rfid": rfid
        }), 200

    # Verifica se já houve entrada hoje.
    agora = datetime.now(timezone.utc)

    inicio_dia = agora.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    )

    entrada_hoje = Evento.query.filter(
        Evento.colaborador_id == colaborador.id,
        Evento.tipo == "ENTRADA",
        Evento.data_hora >= inicio_dia
    ).first()

    # Registrar entrada.
    evento = Evento(
        colaborador_id=colaborador.id,
        rfid=rfid,
        tipo="ENTRADA"
    )

    db.session.add(evento)
    db.session.commit()

    if entrada_hoje is None:
        mensagem = f"Bem-vindo, {colaborador.nome}!"
    else:
        mensagem = f"Bem-vindo de volta, {colaborador.nome}!"

    return jsonify({
        "autorizado": True,
        "situacao": "ENTRADA",
        "mensagem": mensagem,
        "colaborador_id": colaborador.id,
        "nome": colaborador.nome,
        "rfid": rfid
    }), 200


# ============================================================
# CONSULTAR COLABORADORES PRESENTES
# ============================================================

@acessos_bp.route("/api/presenca", methods=["GET"])
def listar_presenca():
    colaboradores = Colaborador.query.filter_by(
        ativo=True,
        autorizado=True
    ).order_by(
        Colaborador.nome
    ).all()

    presentes = []

    for colaborador in colaboradores:
        ultimo_evento = Evento.query.filter(
            Evento.colaborador_id == colaborador.id,
            Evento.tipo.in_(["ENTRADA", "SAIDA"])
        ).order_by(
            Evento.data_hora.desc(),
            Evento.id.desc()
        ).first()

        if ultimo_evento is None:
            continue

        if ultimo_evento.tipo == "SAIDA":
            continue

        agora = datetime.now(timezone.utc)
        data_entrada = ultimo_evento.data_hora

        if data_entrada.tzinfo is None:
            data_entrada = data_entrada.replace(
                tzinfo=timezone.utc
            )

        permanencia_segundos = (
            agora - data_entrada
        ).total_seconds()

        presentes.append({
            "colaborador_id": colaborador.id,
            "nome": colaborador.nome,
            "matricula": colaborador.matricula,
            "cargo": colaborador.cargo,
            "entrada": ultimo_evento.data_hora.isoformat(),
            "permanencia_segundos": round(
                permanencia_segundos
            )
        })

    return jsonify(presentes), 200


# ============================================================
# RELATÓRIO DIÁRIO DE PRESENÇA
# ============================================================

@acessos_bp.route("/api/presenca/relatorio", methods=["GET"])
def relatorio_presenca():
    data_texto = request.args.get("data")
    fuso = timezone(timedelta(hours=-3))

    try:
        if data_texto:
            dia = date.fromisoformat(data_texto)
        else:
            dia = datetime.now(fuso).date()
    except ValueError:
        return jsonify({
            "erro": "Data invalida. Use o formato AAAA-MM-DD."
        }), 400

    inicio_dia = datetime.combine(
        dia,
        time.min,
        tzinfo=fuso
    ).astimezone(timezone.utc)

    fim_dia = datetime.combine(
        dia,
        time.max,
        tzinfo=fuso
    ).astimezone(timezone.utc)

    agora = datetime.now(timezone.utc)
    limite = min(agora, fim_dia)

    colaboradores = Colaborador.query.filter_by(
        ativo=True,
        autorizado=True
    ).order_by(
        Colaborador.nome
    ).all()

    eventos = Evento.query.filter(
        Evento.tipo.in_(["ENTRADA", "SAIDA"])
    ).order_by(
        Evento.data_hora.asc(),
        Evento.id.asc()
    ).all()

    relatorio = []

    for colaborador in colaboradores:
        eventos_colaborador = [
            evento for evento in eventos
            if evento.colaborador_id == colaborador.id
        ]

        dentro = False
        entrada_atual = None
        total_segundos = 0
        quantidade_entradas = 0
        primeira_entrada = None
        ultima_saida = None

        for evento in eventos_colaborador:
            horario = evento.data_hora

            # O SQLite pode devolver horários sem informação de fuso.
            if horario.tzinfo is None:
                horario = horario.replace(
                    tzinfo=timezone.utc
                )
            else:
                horario = horario.astimezone(timezone.utc)

            if horario > limite:
                break

            if evento.tipo == "ENTRADA":
                if not dentro:
                    dentro = True
                    entrada_atual = horario

                    if inicio_dia <= horario <= limite:
                        quantidade_entradas += 1

                        if primeira_entrada is None:
                            primeira_entrada = horario

            elif evento.tipo == "SAIDA" and dentro:
                if entrada_atual is not None:
                    inicio_periodo = max(
                        entrada_atual,
                        inicio_dia
                    )

                    fim_periodo = min(
                        horario,
                        limite
                    )

                    if fim_periodo > inicio_periodo:
                        total_segundos += (
                            fim_periodo - inicio_periodo
                        ).total_seconds()

                dentro = False
                entrada_atual = None

                if inicio_dia <= horario <= limite:
                    ultima_saida = horario

        # Se continua dentro, contabiliza até o limite do relatório.
        if dentro and entrada_atual is not None:
            inicio_periodo = max(
                entrada_atual,
                inicio_dia
            )

            if limite > inicio_periodo:
                total_segundos += (
                    limite - inicio_periodo
                ).total_seconds()

        relatorio.append({
            "colaborador_id": colaborador.id,
            "nome": colaborador.nome,
            "matricula": colaborador.matricula,
            "cargo": colaborador.cargo,
            "data": dia.isoformat(),
            "quantidade_entradas": quantidade_entradas,
            "total_segundos": round(total_segundos),
            "total_horas": round(total_segundos / 3600, 2),
            "presente": dentro,
            "primeira_entrada": (
                primeira_entrada.isoformat()
                if primeira_entrada else None
            ),
            "ultima_saida": (
                ultima_saida.isoformat()
                if ultima_saida else None
            )
        })

    return jsonify(relatorio), 200


# ============================================================
# EXPORTAR RELATÓRIO DE PRESENÇA EM CSV
# ============================================================

@acessos_bp.route("/api/presenca/relatorio/csv", methods=["GET"])
def exportar_relatorio_presenca_csv():
    # Reutiliza o relatório existente com a data solicitada.
    with current_app.test_request_context(
        "/api/presenca/relatorio",
        query_string=request.args
    ):
        resposta, status = relatorio_presenca()
    if status != 200:
        return resposta, status

    dados = resposta.get_json()

    arquivo = io.StringIO()
    arquivo.write("\ufeff")

    escritor = csv.writer(arquivo, delimiter=";")

    escritor.writerow([
        "ID",
        "Nome",
        "Matricula",
        "Cargo",
        "Data",
        "Quantidade de entradas",
        "Total em segundos",
        "Total em horas",
        "Presente",
        "Primeira entrada",
        "Ultima saida"
    ])

    for item in dados:
        escritor.writerow([
            item["colaborador_id"],
            item["nome"],
            item["matricula"],
            item["cargo"],
            item["data"],
            item["quantidade_entradas"],
            item["total_segundos"],
            item["total_horas"],
            "Sim" if item["presente"] else "Nao",
            item["primeira_entrada"] or "",
            item["ultima_saida"] or ""
        ])

    return Response(
        arquivo.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={
            "Content-Disposition":
                "attachment; filename=relatorio_presenca.csv"
        }
    )
