"""
Serviço para gerenciamento de pedidos inline no Telegram
UX melhorada: painel único com linhas por produto + rodapé de ajustes
"""

from typing import Dict, Any, Optional
from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)

PRODUTOS = {
    "americana": {"nome": "Alface Americana", "emoji": "🥬"},
    "crespa": {"nome": "Alface Crespa", "emoji": "🥬"},
    "roxa": {"nome": "Alface Roxa", "emoji": "🍃"},
    "rucula": {"nome": "Rúcula", "emoji": "🌿"},
    "couve": {"nome": "Couve", "emoji": "🥬"},
    "salsinha": {"nome": "Salsinha", "emoji": "🌿"},
    "espinafre": {"nome": "Espinafre", "emoji": "🍃"},
    "manjericao": {"nome": "Manjericão", "emoji": "🌱"},
    "cebolinha": {"nome": "Cebolinha", "emoji": "🧅"},
    "agriao": {"nome": "Agrião", "emoji": "🌿"},
    "coentro": {"nome": "Coentro", "emoji": "🌱"},
    "hortela": {"nome": "Hortelã", "emoji": "🍃"},
    "ovos": {"nome": "Ovos", "emoji": "🥚"}
}


class PedidoInlineService:
    """Gerencia estado e renderização de pedidos inline"""
    
    def __init__(self):
        self.user_pedidos: Dict[str, Dict[str, Any]] = {}
        self.user_panel_state: Dict[str, Dict[str, Any]] = {}
        self.panel_message_ids: Dict[str, int] = {}
        self.chat_ids: Dict[str, int] = {}
    
    def init_pedido(self, user_id: str) -> Dict[str, Any]:
        """Inicializa estrutura do pedido"""
        if user_id not in self.user_pedidos:
            self.user_pedidos[user_id] = {
                "nome": "",
                "data": "",
                "endereco": "",
                "status": "EM_EDICAO",
                "produtos": {
                    "americana": 0,
                    "crespa": 0,
                    "roxa": 0,
                    "rucula": 0,
                    "couve": 0,
                    "salsinha": 0,
                    "espinafre": 0,
                    "manjericao": 0,
                    "cebolinha": 0,
                    "agriao": 0,
                    "coentro": 0,
                    "hortela": 0,
                    "ovos": 0
                },
                "outros": ""
            }
        return self.user_pedidos[user_id]
    
    def init_panel_state(self, user_id: str) -> Dict[str, Any]:
        """Inicializa estado do painel"""
        if user_id not in self.user_panel_state:
            self.user_panel_state[user_id] = {
                "panel_msg_id": None,
                "selected_key": None,
                "awaiting": None
            }
        return self.user_panel_state[user_id]
    
    def calcular_total(self, pedido: Dict[str, Any]) -> int:
        """Calcula total de itens do pedido"""
        return sum(pedido["produtos"].values())
    
    def render_text(self, pedido: Dict[str, Any], panel_state: Dict[str, Any], instrucao: str = "") -> str:
        """Renderiza texto do painel"""
        # Texto padrão profissional
        if instrucao:
            return instrucao
        return "Novo Pedido - Cadastre os itens abaixo:"
    
    def render_saved_order(self, pedido: Dict[str, Any], order_id: str = None) -> str:
        """
        Renderiza pedido salvo em formato de texto simples (apenas itens salvos)
        
        Args:
            pedido: Dados do pedido
            order_id: ID do pedido no e-commerce (opcional)
            
        Returns:
            Texto formatado com apenas os itens salvos
        """
        lines = []
        
        # Cabeçalho
        if order_id:
            lines.append(f"✅ Pedido salvo com sucesso! ID: {order_id}\n")
        else:
            lines.append("✅ Pedido salvo com sucesso!\n")
        
        # Informações do pedido (se houver)
        if pedido.get("nome"):
            lines.append(f"👤 Nome: {pedido.get('nome')}")
        if pedido.get("data"):
            lines.append(f"📅 Data: {pedido.get('data')}")
        if pedido.get("endereco"):
            lines.append(f"📍 Endereço: {pedido.get('endereco')}")
        
        # Lista de itens salvos (apenas os que têm quantidade > 0)
        items_saved = []
        for key, quantidade in pedido.get("produtos", {}).items():
            if quantidade > 0 and key in PRODUTOS:
                produto_info = PRODUTOS[key]
                items_saved.append(f"{produto_info['emoji']} {produto_info['nome']}: {quantidade:02d}")
        
        if items_saved:
            lines.append("\n📦 Itens salvos:")
            for item in items_saved:
                lines.append(f"  • {item}")
        else:
            lines.append("\n⚠️ Nenhum item foi salvo")
        
        return "\n".join(lines)
    
    def build_saved_order_keyboard(self, order_id: str = None) -> Dict[str, Any]:
        """
        Constrói teclado para pedido salvo (Editar, Deletar, Sair)
        
        Args:
            order_id: ID do pedido no e-commerce (opcional)
            
        Returns:
            Teclado inline com botões de ação
        """
        keyboard = []
        
        # Botões de ação
        keyboard.append([
            {"text": "✏️ Editar", "callback_data": f"order:edit:{order_id}" if order_id else "order:edit"},
            {"text": "🗑️ Deletar", "callback_data": f"order:delete:{order_id}" if order_id else "order:delete"},
            {"text": "❌ Sair", "callback_data": "order:saved:sair"}
        ])
        
        return {"inline_keyboard": keyboard}
    
    def build_keyboard(self, pedido: Dict[str, Any], panel_state: Dict[str, Any]) -> Dict[str, Any]:
        """Constrói teclado inline"""
        keyboard = []
        
        # 1. Cabeçalho - cada campo em uma linha: botão + valor (ambos editáveis)
        # Nome - ambos botões abrem edição
        nome_valor = pedido.get("nome", "")
        if not nome_valor:
            nome_valor = "Nome"
        keyboard.append([
            {"text": "👤 Nome", "callback_data": "prod:header:nome"},
            {"text": nome_valor, "callback_data": "prod:header:nome"}
        ])
        
        # Data - ambos botões abrem edição
        data_valor = pedido.get("data", "")
        if not data_valor:
            data_valor = datetime.now().strftime("%d/%m/%Y")
        keyboard.append([
            {"text": "📅 Data", "callback_data": "prod:header:data"},
            {"text": data_valor, "callback_data": "prod:header:data"}
        ])
        
        # Endereço - ambos botões abrem edição
        endereco_valor = pedido.get("endereco", "")
        if not endereco_valor:
            endereco_valor = "Endereço"
        keyboard.append([
            {"text": "📍 Endereço", "callback_data": "prod:header:endereco"},
            {"text": endereco_valor, "callback_data": "prod:header:endereco"}
        ])
        
        # 2. Área de produtos - cada produto em uma linha
        # Botões +/- pequenos (10% cada), produto ocupa o resto (80%)
        for key, info in PRODUTOS.items():
            qtde = pedido["produtos"][key]
            qtde_str = f"{qtde:02d}"
            
            # Produto com largura maior, +/- pequenos
            linha = [
                {"text": f"{info['emoji']} {info['nome']}", "callback_data": f"prod:select:{key}"},
                {"text": "−", "callback_data": f"prod:dec:{key}"},  # Sinal menos menor
                {"text": "+", "callback_data": f"prod:inc:{key}"},   # Sinal mais menor
                {"text": qtde_str, "callback_data": "noop"}
            ]
            keyboard.append(linha)
        
        # Outros - no final da lista de produtos (ambos botões editáveis)
        outros_valor = pedido.get("outros", "")
        if not outros_valor:
            outros_valor = "Outros"
        keyboard.append([
            {"text": "📝 Outros", "callback_data": "prod:header:outros"},
            {"text": outros_valor, "callback_data": "prod:header:outros"}
        ])
        
        # 3. Rodapé dinâmico (sempre aparece, mas só funciona quando selected_key != None)
        selected_key = panel_state.get("selected_key")
        if selected_key:
            rodape = [
                {"text": "-10", "callback_data": "sel:add:-10"},
                {"text": "-5", "callback_data": "sel:add:-5"},
                {"text": "-1", "callback_data": "sel:add:-1"},
                {"text": "+1", "callback_data": "sel:add:+1"},
                {"text": "+5", "callback_data": "sel:add:+5"},
                {"text": "+10", "callback_data": "sel:add:+10"}
            ]
            keyboard.append(rodape)
            keyboard.append([{"text": "✏️ Digitar", "callback_data": "sel:set"}])
        else:
            # Rodapé vazio quando não há seleção
            keyboard.append([{"text": "Selecione um produto acima", "callback_data": "noop"}])
        
        # 4. Ações
        keyboard.append([
            {"text": "💾 Salvar", "callback_data": "action:save"},
            {"text": "🔄 Zerar", "callback_data": "action:zero"},
            {"text": "❌ Cancelar", "callback_data": "action:cancel"},
            {"text": "🔙 Voltar", "callback_data": "action:back"}
        ])
        # 5. Botão Sair para excluir mensagem
        keyboard.append([
            {"text": "❌ Sair", "callback_data": "action:close"}
        ])
        
        return {"inline_keyboard": keyboard}
    
    def get_panel_state(self, user_id: str) -> Dict[str, Any]:
        """Retorna estado do painel"""
        return self.init_panel_state(user_id)
    
    def set_selected_key(self, user_id: str, key: Optional[str]):
        """Define produto selecionado"""
        state = self.init_panel_state(user_id)
        state["selected_key"] = key
    
    def get_selected_key(self, user_id: str) -> Optional[str]:
        """Retorna produto selecionado"""
        state = self.init_panel_state(user_id)
        return state.get("selected_key")
    
    def set_awaiting(self, user_id: str, campo: Optional[str]):
        """Define o que está aguardando do usuário"""
        state = self.init_panel_state(user_id)
        state["awaiting"] = campo
    
    def get_awaiting(self, user_id: str) -> Optional[str]:
        """Retorna o que está aguardando do usuário"""
        state = self.init_panel_state(user_id)
        return state.get("awaiting")
    
    def set_panel_message_id(self, user_id: str, message_id: int, chat_id: int):
        """Armazena ID da mensagem do painel"""
        state = self.init_panel_state(user_id)
        state["panel_msg_id"] = message_id
        self.panel_message_ids[user_id] = message_id
        self.chat_ids[user_id] = chat_id
    
    def get_panel_message_id(self, user_id: str) -> Optional[int]:
        """Retorna ID da mensagem do painel"""
        state = self.init_panel_state(user_id)
        return state.get("panel_msg_id") or self.panel_message_ids.get(user_id)
    
    def reset_pedido(self, user_id: str):
        """Reseta pedido do usuário"""
        pedido = self.init_pedido(user_id)
        pedido["status"] = "EM_EDICAO"
        pedido["nome"] = ""
        pedido["data"] = datetime.now().strftime("%d/%m/%Y")  # Data padrão: hoje
        pedido["endereco"] = ""
        pedido["outros"] = ""
        for key in pedido["produtos"]:
            pedido["produtos"][key] = 0
        
        state = self.init_panel_state(user_id)
        state["selected_key"] = None
        state["awaiting"] = None
    
    def cancelar_pedido(self, user_id: str):
        """Cancela e limpa pedido do usuário"""
        self.user_pedidos.pop(user_id, None)
        self.user_panel_state.pop(user_id, None)
        self.panel_message_ids.pop(user_id, None)
        self.chat_ids.pop(user_id, None)
    
    def ajustar_quantidade(self, user_id: str, produto_key: str, delta: int) -> int:
        """Ajusta quantidade do produto e retorna nova quantidade"""
        pedido = self.init_pedido(user_id)
        nova_qtde = pedido["produtos"][produto_key] + delta
        if nova_qtde < 0:
            nova_qtde = 0
        pedido["produtos"][produto_key] = nova_qtde
        return nova_qtde
    
    def set_quantidade(self, user_id: str, produto_key: str, quantidade: int):
        """Define quantidade do produto"""
        pedido = self.init_pedido(user_id)
        if quantidade < 0:
            quantidade = 0
        pedido["produtos"][produto_key] = quantidade


# Instância global
pedido_inline_service = PedidoInlineService()
