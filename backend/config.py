
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "chave-temporaria-desenvolvimento"
    )

    SQLALCHEMY_DATABASE_URI = (
        "sqlite:///" + str(BASE_DIR / "seguranca.db")
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
