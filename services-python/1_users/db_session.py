"""
Configuração de sessão de banco de dados para Auth Service
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from typing import Generator
from config import settings

# Criar engine do banco de dados
engine = create_engine(
    settings.DATABASE_URI,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    pool_recycle=settings.DATABASE_POOL_RECYCLE,
    echo=settings.DEBUG
)

# Criar sessão local
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para modelos
Base = declarative_base()

# Não importar modelos aqui para evitar conflitos

def get_db_session() -> Generator[Session, None, None]:
    """Dependency para obter sessão do banco de dados"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Criar todas as tabelas"""
    Base.metadata.create_all(bind=engine)

def drop_tables():
    """Remover todas as tabelas"""
    Base.metadata.drop_all(bind=engine)

