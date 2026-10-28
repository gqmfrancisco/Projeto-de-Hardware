
from flask import Blueprint, jsonify
import pandas as pd

from models import Colaborador, Evento


analise_bp = Blueprint("analise", __name__)


@analise_bp.route("/api/analise/presenca", methods=["GET"])
def analisar_presenca():
    colaboradores = Colaborador.query.filter_by(
        ativo=True,
        autorizado=True
    ).all()

    eventos = Evento.query.filter(
        Evento.tipo.in_(["ENTRADA", "SAIDA"])
    ).all()

    dados_colaboradores = [
        {
            "colaborador_id": colaborador.id,
            "nome": colaborador.nome,
            "cargo": colaborador.cargo,
        }
        for colaborador in colaboradores
    ]

    if not dados_colaboradores:
        return jsonify({
            "total_colaboradores": 0,
            "total_presentes": 0,
            "total_ausentes": 0,
            "por_cargo": [],
        }), 200

    df_colaboradores = pd.DataFrame(dados_colaboradores)

    dados_eventos = [
        {
            "colaborador_id": evento.colaborador_id,
            "tipo": evento.tipo,
            "data_hora": evento.data_hora,
            "evento_id": evento.id,
        }
        for evento in eventos
        if evento.colaborador_id is not None
    ]

    if dados_eventos:
        df_eventos = pd.DataFrame(dados_eventos)

        df_eventos = df_eventos.sort_values(
            ["data_hora", "evento_id"]
        )

        ultimos_eventos = (
            df_eventos.groupby("colaborador_id")
            .tail(1)
        )

        presentes_ids = set(
            ultimos_eventos.loc[
                ultimos_eventos["tipo"] == "ENTRADA",
                "colaborador_id"
            ].tolist()
        )
    else:
        presentes_ids = set()

    df_colaboradores["presente"] = (
        df_colaboradores["colaborador_id"].isin(presentes_ids)
    )

    resumo_cargos = (
        df_colaboradores.groupby("cargo")
        .agg(
            total_colaboradores=("colaborador_id", "count"),
            total_presentes=("presente", "sum"),
        )
        .reset_index()
    )

    resumo_cargos["total_ausentes"] = (
        resumo_cargos["total_colaboradores"]
        - resumo_cargos["total_presentes"]
    )

    total_colaboradores = len(df_colaboradores)
    total_presentes = int(df_colaboradores["presente"].sum())

    return jsonify({
        "total_colaboradores": total_colaboradores,
        "total_presentes": total_presentes,
        "total_ausentes": total_colaboradores - total_presentes,
        "por_cargo": resumo_cargos.to_dict(orient="records"),
    }), 200
