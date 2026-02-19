"""
Serviço de CRUD de produtos
Integrado com o Commerce Service
"""

from typing import List, Optional
import structlog

from models.product_models import ProductCreate, ProductUpdate, ProductResponse
from services.commerce_integration import commerce_integration

logger = structlog.get_logger(__name__)


class ProductService:
    """Serviço para operações CRUD de produtos usando Commerce Service"""
    
    async def create_product(self, product_data: ProductCreate, user_id: str) -> ProductResponse:
        """Cria um novo produto usando Commerce Service"""
        try:
            logger.info(f"Criando produto '{product_data.name}' por usuário {user_id} via Commerce Service")
            product = await commerce_integration.create_product(product_data, user_id)
            logger.info(f"Produto criado: {product.id} por usuário {user_id}")
            return product
        except Exception as e:
            logger.error(f"Erro ao criar produto: {e}", exc_info=True)
            raise
    
    async def get_product(self, product_id: int) -> Optional[ProductResponse]:
        """Busca um produto por ID usando Commerce Service"""
        try:
            return await commerce_integration.get_product(product_id)
        except Exception as e:
            logger.error(f"Erro ao buscar produto {product_id}: {e}", exc_info=True)
            raise
    
    async def list_products(
        self, 
        user_id: Optional[str] = None,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ProductResponse]:
        """Lista produtos com filtros opcionais usando Commerce Service"""
        try:
            # Nota: O Commerce Service pode não filtrar por user_id diretamente
            # Se necessário, podemos filtrar localmente após buscar
            products = await commerce_integration.list_products(
                category=category,
                is_active=is_active,
                limit=limit,
                offset=offset
            )
            
            # Filtrar por user_id se necessário (após buscar do Commerce Service)
            if user_id:
                products = [p for p in products if p.created_by == user_id]
            
            return products
        except Exception as e:
            logger.error(f"Erro ao listar produtos: {e}", exc_info=True)
            raise
    
    async def update_product(
        self, 
        product_id: int, 
        product_data: ProductUpdate,
        user_id: str
    ) -> Optional[ProductResponse]:
        """Atualiza um produto usando Commerce Service"""
        try:
            # Verifica se o produto existe e pertence ao usuário
            product = await commerce_integration.get_product(product_id)
            if not product or product.created_by != user_id:
                logger.warning(f"Produto {product_id} não encontrado ou não pertence ao usuário {user_id}")
                return None
            
            logger.info(f"Atualizando produto {product_id} por usuário {user_id} via Commerce Service")
            updated_product = await commerce_integration.update_product(product_id, product_data, user_id)
            logger.info(f"Produto {product_id} atualizado por usuário {user_id}")
            return updated_product
        except Exception as e:
            logger.error(f"Erro ao atualizar produto {product_id}: {e}", exc_info=True)
            raise
    
    async def delete_product(self, product_id: int, user_id: str) -> bool:
        """Deleta um produto (soft delete - marca como inativo) usando Commerce Service"""
        try:
            # Verifica se o produto existe e pertence ao usuário
            product = await commerce_integration.get_product(product_id)
            if not product or product.created_by != user_id:
                logger.warning(f"Produto {product_id} não encontrado ou não pertence ao usuário {user_id}")
                return False
            
            logger.info(f"Deletando produto {product_id} por usuário {user_id} via Commerce Service")
            success = await commerce_integration.delete_product(product_id, user_id)
            logger.info(f"Produto {product_id} deletado (soft delete) por usuário {user_id}")
            return success
        except Exception as e:
            logger.error(f"Erro ao deletar produto {product_id}: {e}", exc_info=True)
            raise


# Instância global do serviço
product_service = ProductService()
