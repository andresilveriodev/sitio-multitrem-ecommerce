"""
Database connection configuration
"""

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager
from typing import Generator
import structlog

from config import settings

logger = structlog.get_logger()

# Engine configurada
engine = create_engine(
    settings.DATABASE_URI,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    pool_recycle=settings.DATABASE_POOL_RECYCLE,
    echo=False,
    pool_pre_ping=True
)

# Session factory
SessionLocal = scoped_session(sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False
))

# Base para os modelos
Base = declarative_base()


def get_db_session() -> Generator:
    """
    Dependency para obter sessão do banco de dados
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db():
    """
    Context manager para sessão do banco de dados
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Cria todas as tabelas"""
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """Remove todas as tabelas"""
    Base.metadata.drop_all(bind=engine)


def create_schemas():
    """Cria os schemas necessários no banco de dados"""
    schemas = ['commerce', 'chatbot', 'ai_management']
    
    try:
        with engine.connect() as conn:
            for schema in schemas:
                conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
                logger.info(f"Schema '{schema}' criado/verificado com sucesso")
            conn.commit()
    except Exception as e:
        logger.error(f"Erro ao criar schemas: {e}")
        raise
