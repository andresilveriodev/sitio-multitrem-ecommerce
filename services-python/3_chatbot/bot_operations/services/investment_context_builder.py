"""
Serviço para construir contexto de investimentos para enviar ao AI Service
"""

from typing import Dict, Optional, Any, List
import structlog

logger = structlog.get_logger(__name__)


class InvestmentContextBuilder:
    """Constrói contexto de investimentos para enviar ao AI Service"""
    
    def build_investment_context(
        self,
        plan_id: Optional[str] = None,
        periodo_id: Optional[str] = None,
        investment_categories: Optional[List[Dict]] = None,
        available_investment_types: Optional[List[Dict]] = None,
        current_investments: Optional[List[Dict]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Constrói contexto de investimentos no formato esperado pelo AI Service
        
        Args:
            plan_id: ID do plano financeiro atual
            periodo_id: ID do período atual
            investment_categories: Lista de categorias de investimento do usuário
            available_investment_types: Tipos de investimento disponíveis no sistema
            current_investments: Investimentos atuais do usuário
            
        Returns:
            Dict com contexto de investimentos ou None se não houver dados
        """
        try:
            context = {}
            
            # Adiciona IDs do plano e período se disponíveis
            if plan_id:
                context["current_plan_id"] = plan_id
            if periodo_id:
                context["current_periodo_id"] = periodo_id
            
            # Adiciona categorias de investimento se disponíveis
            if investment_categories:
                context["investment_categories"] = investment_categories
            
            # Adiciona tipos de investimento disponíveis se disponíveis
            if available_investment_types:
                context["available_investment_types"] = available_investment_types
            
            # Adiciona investimentos atuais se disponíveis
            if current_investments:
                context["current_investments"] = current_investments
            
            # Só retorna contexto se tiver pelo menos algum dado
            if context:
                logger.debug("Contexto de investimentos construído", 
                           has_plan_id=bool(plan_id),
                           has_categories=bool(investment_categories),
                           has_types=bool(available_investment_types),
                           has_investments=bool(current_investments))
                return context
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao construir contexto de investimentos: {e}", exc_info=True)
            return None
    
    def build_context_from_conversation_metadata(
        self,
        conversation_metadata: Dict[str, Any],
        investment_categories: Optional[List[Dict]] = None,
        available_investment_types: Optional[List[Dict]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Constrói contexto a partir dos metadados da conversa
        
        Args:
            conversation_metadata: Metadados da conversa (pode conter plan_id, periodo_id, etc)
            investment_categories: Categorias de investimento (opcional)
            available_investment_types: Tipos disponíveis (opcional)
            
        Returns:
            Dict com contexto ou None
        """
        try:
            plan_id = conversation_metadata.get("current_plan_id")
            periodo_id = conversation_metadata.get("current_periodo_id")
            
            return self.build_investment_context(
                plan_id=plan_id,
                periodo_id=periodo_id,
                investment_categories=investment_categories,
                available_investment_types=available_investment_types
            )
            
        except Exception as e:
            logger.error(f"Erro ao construir contexto de metadados: {e}", exc_info=True)
            return None
    
    def format_investment_categories_for_context(
        self,
        categories: List[Dict]
    ) -> List[Dict]:
        """
        Formata categorias de investimento para o contexto
        
        Args:
            categories: Lista de categorias
            
        Returns:
            Lista formatada
        """
        try:
            formatted = []
            for cat in categories:
                formatted.append({
                    "id": cat.get("id"),
                    "nome": cat.get("nome") or cat.get("name"),
                    "percentual": cat.get("percentual"),
                    "valor": cat.get("valor") or cat.get("value"),
                    "investimentos": cat.get("investimentos", [])
                })
            return formatted
        except Exception as e:
            logger.error(f"Erro ao formatar categorias: {e}")
            return []
    
    def format_investment_types_for_context(
        self,
        types: List[Dict]
    ) -> List[Dict]:
        """
        Formata tipos de investimento para o contexto
        
        Args:
            types: Lista de tipos
            
        Returns:
            Lista formatada
        """
        try:
            formatted = []
            for inv_type in types:
                formatted.append({
                    "id": inv_type.get("id"),
                    "name": inv_type.get("name") or inv_type.get("nome"),
                    "category": inv_type.get("category") or inv_type.get("categoria"),
                    "description": inv_type.get("description") or inv_type.get("descricao")
                })
            return formatted
        except Exception as e:
            logger.error(f"Erro ao formatar tipos: {e}")
            return []


# Instância global
investment_context_builder = InvestmentContextBuilder()

