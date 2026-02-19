"""
Serviço de conexão com banco de dados PostgreSQL
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
import structlog
from typing import Optional

from config import settings
from models.product_models import Base
from models.order_models import Base as OrderBase

# Importar modelos para garantir que sejam registrados
from models import order_models  # noqa

logger = structlog.get_logger(__name__)


class DatabaseService:
    """Serviço de gerenciamento de conexão com banco de dados"""
    
    def __init__(self):
        self.engine = None
        self.async_session: Optional[async_sessionmaker] = None
        self._connected = False
    
    async def connect(self):
        """Conecta ao banco de dados"""
        try:
            # Converte postgresql:// para postgresql+asyncpg://
            database_url = settings.DATABASE_URL
            if database_url.startswith("postgresql://"):
                database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
            
            self.engine = create_async_engine(
                database_url,
                poolclass=NullPool,
                echo=False,  # Mude para True para ver SQL queries
                future=True
            )
            
            self.async_session = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Testa a conexão e cria tabelas
            async with self.engine.begin() as conn:
                # Criar todas as tabelas (Product, Order, OrderItem)
                await conn.run_sync(Base.metadata.create_all)
                await conn.run_sync(OrderBase.metadata.create_all)
            
            self._connected = True
            logger.info("Conectado ao banco de dados PostgreSQL com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao conectar ao banco de dados: {e}", exc_info=True)
            self._connected = False
            raise
    
    async def disconnect(self):
        """Desconecta do banco de dados"""
        if self.engine:
            await self.engine.dispose()
            self._connected = False
            logger.info("Desconectado do banco de dados")
    
    def get_session(self) -> AsyncSession:
        """Retorna uma sessão do banco de dados"""
        if not self._connected or not self.async_session:
            raise RuntimeError("Banco de dados não está conectado. Chame connect() primeiro.")
        return self.async_session()
    
    @property
    def is_connected(self) -> bool:
        """Verifica se está conectado"""
        return self._connected


# Instância global do serviço
database_service = DatabaseService()
