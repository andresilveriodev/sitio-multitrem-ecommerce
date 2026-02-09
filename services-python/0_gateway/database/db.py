"""
Database connection configuration
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager
from typing import Generator

from ..config import settings

# Engine configurada
engine = create_engine(
    settings.DATABASE_URI,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Session factory
SessionLocal = scoped_session(sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False
))

# Base para os modelos
Base = declarative_base()


def get_db() -> Generator:
    """
    Dependency para obter sessão do banco de dados
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session():
    """
    Context manager para sessão do banco de dados
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()




