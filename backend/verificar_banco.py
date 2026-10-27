
from sqlalchemy import inspect

from app import app
from database import db

with app.app_context():

    inspector = inspect(db.engine)

    tabelas = inspector.get_table_names()

    print("TABELAS ENCONTRADAS:")

    for tabela in tabelas:
        print("-", tabela)
