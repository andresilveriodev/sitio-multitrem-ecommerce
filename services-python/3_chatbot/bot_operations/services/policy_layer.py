"""
Policy Layer - Regras de negócio e segurança
Define políticas curtas e rígidas para o chatbot
"""

from typing import Dict, Any, Optional, List
import structlog

logger = structlog.get_logger(__name__)


class PolicyLayer:
    """Camada de políticas do chatbot"""
    
    def __init__(self):
        # Políticas de negócio
        self.business_policies = {
            "domain": "horta",  # Domínio do negócio
            "allowed_intents": [
                "pedidos", "estoque", "financeiro", "cadastro",
                "menu", "hoje", "cliente", "produto"
            ],
            "restrict_to_domain": True,  # Restringir ao domínio da horta
        }
        
        # Políticas de segurança
        self.security_policies = {
            "no_sensitive_data": True,  # Não expor dados sensíveis
            "require_auth_for_tools": True,  # Requer autenticação para tools
            "max_message_length": 5000,  # Tamanho máximo de mensagem
        }
        
        # Políticas de comportamento
        self.behavior_policies = {
            "if_unsure_ask": True,  # Se não souber, perguntar
            "if_human_requested": "create_ticket",  # Se pedir humano, criar ticket
            "greeting_always_ai": True,  # Cumprimentos sempre vão para AI
            "order_text_always_ai": True,  # Texto de pedido sempre vai para AI (parsing)
        }
    
    def get_ai_context(self, intent: str, user_state: Optional[Dict[str, Any]] = None) -> str:
        """
        Retorna contexto para o AI Service baseado na intent
        
        Args:
            intent: Intent detectada
            user_state: Estado atual do usuário
            
        Returns:
            String com contexto para o AI
        """
        context_parts = []
        
        # Contexto do domínio
        context_parts.append(
            "Você é um assistente virtual especializado em gestão de horta orgânica. "
            "Seu domínio é: pedidos, estoque, produtos, clientes e finanças da horta."
        )
        
        # Contexto da intent
        if intent == "pedidos":
            context_parts.append(
                "O usuário está perguntando sobre pedidos. "
                "Você pode ajudar a listar pedidos, criar novos pedidos ou consultar status."
            )
        elif intent == "estoque":
            context_parts.append(
                "O usuário está perguntando sobre estoque. "
                "Você pode ajudar a consultar disponibilidade de produtos."
            )
        elif intent == "financeiro":
            context_parts.append(
                "O usuário está perguntando sobre finanças. "
                "Você pode ajudar com resumos financeiros e relatórios."
            )
        elif intent == "cumprimento":
            context_parts.append(
                "O usuário está cumprimentando. "
                "Responda de forma amigável e profissional, apresentando os comandos principais do sistema. "
                "Comandos disponíveis: /menu (menu principal), /hoje (resumo do dia), /pedidos (listar pedidos), "
                "/estoque (ver estoque), /financeiro (resumo financeiro). "
                "Seja breve e direto."
            )
        elif intent == "conversa":
            context_parts.append(
                "O usuário está tendo uma conversa natural. "
                "Mantenha o foco no domínio da horta. "
                "Se a pergunta não for sobre horta, oriente educadamente."
            )
        elif intent == "duvida":
            context_parts.append(
                "A intent da mensagem não está clara. "
                "Classifique a mensagem do usuário em uma das seguintes categorias: "
                "pedidos, estoque, financeiro, cadastro, menu, hoje, cliente, produto, ou conversa. "
                "Responda de forma útil baseado na classificação."
            )
        
        # Contexto do estado do usuário
        if user_state and user_state.get("active_flow"):
            context_parts.append(
                f"O usuário está em um fluxo ativo: {user_state.get('active_flow')}. "
                "Considere isso ao responder."
            )
        
        # Políticas de comportamento
        context_parts.append(
            "Políticas: "
            "- Se não souber algo, pergunte ao usuário. "
            "- Se o usuário pedir para falar com uma pessoa, ofereça criar um chamado. "
            "- Mantenha respostas breves e objetivas. "
            "- Use os comandos disponíveis quando apropriado."
        )
        
        return " ".join(context_parts)
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """
        Retorna lista de tools disponíveis para o AI Service
        
        Returns:
            Lista de tools no formato para tool-calling
        """
        return [
            {
                "name": "listar_pedidos",
                "description": "Lista pedidos do sistema. Parâmetros: data (opcional), status (opcional)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "data": {"type": "string", "description": "Data no formato YYYY-MM-DD"},
                        "status": {"type": "string", "description": "Status do pedido"}
                    }
                }
            },
            {
                "name": "consultar_estoque",
                "description": "Consulta estoque de um produto. Parâmetros: produto (nome do produto)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "produto": {"type": "string", "description": "Nome do produto"},
                        "nome": {"type": "string", "description": "Nome do produto (alternativo)"}
                    },
                    "required": ["produto"]
                }
            },
            {
                "name": "resumo_financeiro",
                "description": "Retorna resumo financeiro. Parâmetros: periodo (hoje, semana, mes)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "periodo": {"type": "string", "description": "Período: hoje, semana, mes"}
                    }
                }
            },
            {
                "name": "buscar_cliente",
                "description": "Busca cliente por nome ou telefone. Parâmetros: nome (opcional), telefone (opcional)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "nome": {"type": "string", "description": "Nome do cliente"},
                        "telefone": {"type": "string", "description": "Telefone do cliente"}
                    }
                }
            },
            {
                "name": "listar_produtos",
                "description": "Lista produtos. Parâmetros: categoria (opcional), search (opcional)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "categoria": {"type": "string", "description": "Categoria do produto"},
                        "search": {"type": "string", "description": "Termo de busca"}
                    }
                }
            },
            {
                "name": "resumo_hoje",
                "description": "Retorna resumo operacional do dia atual",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
    
    def should_restrict_to_domain(self) -> bool:
        """Verifica se deve restringir ao domínio"""
        return self.business_policies.get("restrict_to_domain", True)
    
    def is_allowed_intent(self, intent: str) -> bool:
        """Verifica se intent é permitida"""
        allowed = self.business_policies.get("allowed_intents", [])
        return intent in allowed or intent in ["conversa", "cumprimento", "duvida"]


# Instância global
policy_layer = PolicyLayer()
