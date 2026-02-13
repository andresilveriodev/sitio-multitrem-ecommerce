from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
import os

# Agora lendo de variável de ambiente, mas mantendo compatível
DATABASE_URI = os.getenv("DATABASE_URI", 'postgresql://postgres:123456@localhost:5434/b3_trader')

# Engine configurada
engine = create_engine(DATABASE_URI, echo=False)

# Session original mantida
Session = scoped_session(sessionmaker(bind=engine))

# Base para os modelos com schema chatbot
Base = declarative_base()
Base.metadata.schema = 'chatbot'

# Função para criar schema se não existir
def create_schema_if_not_exists():
    """Cria o schema chatbot se não existir"""
    with engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS chatbot"))
        conn.commit()

# Função para inicializar o banco
def init_db():
    """Inicializa o banco de dados criando schema e tabelas"""
    create_schema_if_not_exists()
    Base.metadata.create_all(bind=engine)

# Função para obter sessão do banco (dependency do FastAPI)
def get_db():
    """Dependency para obter sessão do banco de dados"""
    db = Session()
    try:
        yield db
    finally:
        db.close()