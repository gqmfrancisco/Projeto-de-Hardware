
from flask import Flask, jsonify

from config import Config
from database import db

# Importar os modelos do banco
from models import Colaborador, Evento, Usuario


def create_app():

    app = Flask(__name__)

    # Carregar configuracoes
    app.config.from_object(Config)

    # Conectar o banco ao Flask
    db.init_app(app)

    # Criar as tabelas
    with app.app_context():
        db.create_all()
        print("BANCO DE DADOS INICIALIZADO!")

    @app.route("/")
    def home():
        return jsonify({
            "mensagem": "Backend funcionando!",
            "projeto": "Sala de Seguranca"
        })

    @app.route("/api/status")
    def status():
        return jsonify({
            "status": "online",
            "banco": "SQLite"
        })

    return app


app = create_app()


if __name__ == "__main__":
    print("INICIANDO SERVIDOR FLASK...")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )
