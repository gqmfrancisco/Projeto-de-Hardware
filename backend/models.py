
from datetime import datetime, timezone

from database import db
from werkzeug.security import generate_password_hash, check_password_hash


# TABELA DE COLABORADORES

class Colaborador(db.Model):

    __tablename__ = "colaboradores"

    id = db.Column(db.Integer, primary_key=True)

    nome = db.Column(db.String(100), nullable=False)

    matricula = db.Column(
        db.String(30),
        unique=True,
        nullable=False
    )

    rfid = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    cargo = db.Column(db.String(100), nullable=False)

    autorizado = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    ativo = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    eventos = db.relationship(
        "Evento",
        backref="colaborador",
        lazy=True
    )


# TABELA DE EVENTOS

class Evento(db.Model):

    __tablename__ = "eventos"

    id = db.Column(db.Integer, primary_key=True)

    colaborador_id = db.Column(
        db.Integer,
        db.ForeignKey("colaboradores.id"),
        nullable=True
    )

    rfid = db.Column(db.String(100), nullable=False)

    tipo = db.Column(db.String(30), nullable=False)

    data_hora = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )


# TABELA DE USUARIOS ADMINISTRATIVOS

class Usuario(db.Model):

    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    def definir_senha(self, senha):
        self.password_hash = generate_password_hash(senha)

    def verificar_senha(self, senha):
        return check_password_hash(
            self.password_hash,
            senha
        )
