"""
Tools Registry - Funções determinísticas do sistema
Tools são funções que executam operações do sistema sem usar IA
"""

from typing import Dict, Any, Optional, List
import structlog
from datetime import datetime

from services.commerce_client import commerce_client
from services.telegram_order_parser import telegram_order_parser

logger = structlog.get_logger(__name__)


class ToolResult:
    """Resultado de execução de uma tool"""
    
    def __init__(
        self,
        ok: bool,
        data: Optional[Dict[str, Any]] = None,
        message: Optional[str] = None,
        user_message_suggestion: Optional[str] = None,
        error: Optional[str] = None
    ):
        self.ok = ok
        self.data = data or {}
        self.message = message
        self.user_message_suggestion = user_message_suggestion
        self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "data": self.data,
            "message": self.message,
            "user_message_suggestion": self.user_message_suggestion,
            "error": self.error
        }


class ToolsRegistry:
    """Registry de tools disponíveis"""
    
    def __init__(self):
        self.tools = {
            "listar_pedidos": self._listar_pedidos,
            "consultar_estoque": self._consultar_estoque,
            "resumo_financeiro": self._resumo_financeiro,
            "buscar_cliente": self._buscar_cliente,
            "listar_produtos": self._listar_produtos,
            "resumo_hoje": self._resumo_hoje,
        }
    
    async def execute(
        self,
        tool_name: str,
        params: Dict[str, Any],
        user_id: str,
        token: Optional[str] = None
    ) -> ToolResult:
        """
        Executa uma tool
        
        Args:
            tool_name: Nome da tool
            params: Parâmetros da tool
            user_id: ID do usuário
            token: Token de autenticação (opcional)
            
        Returns:
            ToolResult com resultado da execução
        """
        if tool_name not in self.tools:
            logger.warning(
                "Tool não encontrada",
                tool_name=tool_name,
                available_tools=list(self.tools.keys())
            )
            return ToolResult(
                ok=False,
                error=f"Tool '{tool_name}' não encontrada"
            )
        
        try:
            logger.info(
                "Executando tool",
                tool_name=tool_name,
                user_id=user_id,
                params=params
            )
            
            result = await self.tools[tool_name](params, user_id, token)
            
            logger.info(
                "Tool executada com sucesso",
                tool_name=tool_name,
                user_id=user_id,
                ok=result.ok
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "Erro ao executar tool",
                tool_name=tool_name,
                user_id=user_id,
                error=str(e),
                exc_info=True
            )
            return ToolResult(
                ok=False,
                error=f"Erro ao executar {tool_name}: {str(e)}"
            )
    
    async def _listar_pedidos(
        self,
        params: Dict[str, Any],
        user_id: str,
        token: Optional[str] = None
    ) -> ToolResult:
        """Lista pedidos"""
        # TODO: Implementar busca de pedidos no commerce service
        data = params.get("data")
        status = params.get("status")
        
        # Por enquanto, retorna estrutura básica
        return ToolResult(
            ok=True,
            data={
                "pedidos": [],
                "total": 0,
                "filtros": {
                    "data": data,
                    "status": status
                }
            },
            message="Listando pedidos...",
            user_message_suggestion="Quer filtrar por data ou status?"
        )
    
    async def _consultar_estoque(
        self,
        params: Dict[str, Any],
        user_id: str,
        token: Optional[str] = None
    ) -> ToolResult:
        """Consulta estoque de produtos"""
        produto_nome = params.get("produto") or params.get("nome")
        
        if not produto_nome:
            return ToolResult(
                ok=False,
                error="Nome do produto é obrigatório"
            )
        
        try:
            # Buscar produto no commerce service
            produtos = await commerce_client.search_products(
                search=produto_nome,
                token=token
            )
            
            if not produtos:
                return ToolResult(
                    ok=True,
                    data={"produto": produto_nome, "encontrado": False},
                    message=f"Produto '{produto_nome}' não encontrado",
                    user_message_suggestion="Quer buscar outro produto?"
                )
            
            # Retornar primeiro resultado
            produto = produtos[0]
            return ToolResult(
                ok=True,
                data={
                    "produto": produto,
                    "encontrado": True
                },
                message=f"Produto encontrado: {produto.get('name', produto_nome)}",
                user_message_suggestion="Quer ver mais detalhes ou buscar outro produto?"
            )
            
        except Exception as e:
            logger.error(f"Erro ao consultar estoque: {e}", exc_info=True)
            return ToolResult(
                ok=False,
                error=f"Erro ao consultar estoque: {str(e)}"
            )
    
    async def _resumo_financeiro(
        self,
        params: Dict[str, Any],
        user_id: str,
        token: Optional[str] = None
    ) -> ToolResult:
        """Resumo financeiro"""
        periodo = params.get("periodo", "hoje")
        
        # TODO: Implementar busca de dados financeiros
        return ToolResult(
            ok=True,
            data={
                "periodo": periodo,
                "receita": 0.0,
                "despesas": 0.0,
                "lucro": 0.0
            },
            message=f"Resumo financeiro - {periodo}",
            user_message_suggestion="Quer ver detalhes de receitas ou despesas?"
        )
    
    async def _buscar_cliente(
        self,
        params: Dict[str, Any],
        user_id: str,
        token: Optional[str] = None
    ) -> ToolResult:
        """Busca cliente por nome ou telefone"""
        nome = params.get("nome")
        telefone = params.get("telefone")
        
        if not nome and not telefone:
            return ToolResult(
                ok=False,
                error="Nome ou telefone é obrigatório"
            )
        
        try:
            search_term = nome or telefone
            clientes = await commerce_client.search_customers(
                search=search_term,
                token=token
            )
            
            if not clientes:
                return ToolResult(
                    ok=True,
                    data={"clientes": [], "encontrado": False},
                    message=f"Cliente não encontrado: {search_term}",
                    user_message_suggestion="Quer cadastrar um novo cliente?"
                )
            
            return ToolResult(
                ok=True,
                data={
                    "clientes": clientes,
                    "encontrado": True,
                    "total": len(clientes)
                },
                message=f"Encontrado(s) {len(clientes)} cliente(s)",
                user_message_suggestion="Quer ver detalhes de algum cliente?"
            )
            
        except Exception as e:
            logger.error(f"Erro ao buscar cliente: {e}", exc_info=True)
            return ToolResult(
                ok=False,
                error=f"Erro ao buscar cliente: {str(e)}"
            )
    
    async def _listar_produtos(
        self,
        params: Dict[str, Any],
        user_id: str,
        token: Optional[str] = None
    ) -> ToolResult:
        """Lista produtos"""
        categoria = params.get("categoria")
        search = params.get("search")
        
        try:
            if search:
                produtos = await commerce_client.search_products(
                    search=search,
                    token=token
                )
            else:
                # TODO: Implementar listagem completa
                produtos = []
            
            return ToolResult(
                ok=True,
                data={
                    "produtos": produtos,
                    "total": len(produtos)
                },
                message=f"Encontrado(s) {len(produtos)} produto(s)",
                user_message_suggestion="Quer buscar um produto específico?"
            )
            
        except Exception as e:
            logger.error(f"Erro ao listar produtos: {e}", exc_info=True)
            return ToolResult(
                ok=False,
                error=f"Erro ao listar produtos: {str(e)}"
            )
    
    async def _resumo_hoje(
        self,
        params: Dict[str, Any],
        user_id: str,
        token: Optional[str] = None
    ) -> ToolResult:
        """Resumo operacional do dia"""
        hoje = datetime.now().strftime("%Y-%m-%d")
        
        # TODO: Implementar busca de dados do dia
        return ToolResult(
            ok=True,
            data={
                "data": hoje,
                "pedidos": 0,
                "vendas": 0.0,
                "clientes_atendidos": 0
            },
            message=f"Resumo operacional - {hoje}",
            user_message_suggestion="Quer ver detalhes de pedidos ou vendas?"
        )


# Instância global
tools_registry = ToolsRegistry()
