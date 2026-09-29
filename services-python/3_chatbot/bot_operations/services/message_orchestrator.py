"""
Message Orchestrator - Orquestra o fluxo Router -> Tools/AI -> Resposta
Implementa a arquitetura Router + AI + Tools
"""

import json
import re
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

import structlog

from services.router_service import router_service, RouteType, IntentType
from services.tools_registry import tools_registry
from services.ai_integration import ai_integration
from services.policy_layer import policy_layer
from services.telegram_order_parser import telegram_order_parser

# Import opcional - se não existir, não quebra
try:
    from services.context_service import context_service
    from models.conversation_context import Message, MessageType
except ImportError:
    context_service = None
    Message = None
    MessageType = None

logger = structlog.get_logger(__name__)


def _order_extraction_state_default() -> Dict[str, Any]:
    """Estado inicial do fluxo de extração de pedido (IA conduz a conversa)."""
    return {
        "current_order": {
            "customer_name": None,
            "contact_name": None,
            "items": [],
            "delivery_date": None,
        },
        "updated_at": None,
    }


# Convenção: mesma conversa /ai/chat; a IA pode terminar a resposta com uma linha
# "ORDER_DATA: {json}" para o chatbot extrair dados e persistir quando can_save_now.
ORDER_DATA_MARKER = "ORDER_DATA:"

# Padrões para extrair nome do cliente da resposta da IA ou do histórico (aceita "cliente: X" ou "cliente, X")
CLIENT_NAME_PATTERNS = [
    re.compile(r"nome\s+do\s+cliente[:\s,]+([A-Za-zÀ-ÿ\s]+?)(?:\.|,|\n|$)", re.IGNORECASE),
    re.compile(r"já\s+temos\s+(?:o\s+)?nome\s+(?:do\s+cliente)?[:\s,]+([A-Za-zÀ-ÿ\s]+?)(?:\.|,|\n|$)", re.IGNORECASE),
    re.compile(r"cliente[:\s,]+([A-Za-zÀ-ÿ\s]+?)(?:\.|,|\n|$)", re.IGNORECASE),
    re.compile(r"temos\s+o\s+nome\s+do\s+cliente[,\s]+([A-Za-zÀ-ÿ\s]+?)(?:\.|,|\n|$)", re.IGNORECASE),
]


def _extract_client_name_from_text(text: str) -> Optional[str]:
    """Tenta extrair nome do cliente do texto da resposta da IA (fallback quando ORDER_DATA não vem)."""
    if not text or not text.strip():
        return None
    for pat in CLIENT_NAME_PATTERNS:
        m = pat.search(text)
        if m:
            name = m.group(1).strip()
            if name and len(name) <= 120:
                return name
    return None


def _parse_client_name_from_user_message(text: str) -> Optional[str]:
    """Extrai nome do cliente quando o usuário diz 'pedido do X' ou 'registrar o pedido do X'."""
    if not text or not text.strip():
        return None
    m = re.search(r"(?:pedido|registrar\s+o\s+pedido)\s+do\s+([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s]{0,80}?)(?:\s*\.|,|\n|$)", text.strip(), re.IGNORECASE)
    if m:
        name = m.group(1).strip()
        return name if name and len(name) <= 80 else None
    return None


def _parse_items_from_user_message(text: str) -> List[Dict[str, Any]]:
    """
    Extrai itens da mensagem do usuário no formato '02 Alface crespa 01 Rucula'.
    Retorna lista de {product_name, quantity} para não depender da IA trocar produtos (ex.: rucula -> couve).
    """
    if not text or not text.strip():
        return []
    tokens = text.strip().split()
    items = []
    i = 0
    while i < len(tokens):
        # token que é só número = quantidade
        if tokens[i].isdigit():
            qty = int(tokens[i])
            i += 1
            name_parts = []
            while i < len(tokens) and not tokens[i].isdigit():
                name_parts.append(tokens[i])
                i += 1
            name = " ".join(name_parts).strip()
            if name and qty > 0:
                items.append({"product_name": name, "quantity": qty})
        else:
            i += 1
    return items


def _parse_order_data_from_reply(reply: str) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Extrai bloco ORDER_DATA da resposta da IA (mesmo fluxo de chat).
    Retorna (mensagem para o usuário, dados do pedido ou None).
    """
    if not reply or not reply.strip():
        return reply or "", None
    # Procurar última linha que começa com ORDER_DATA:
    lines = reply.strip().split("\n")
    user_lines = []
    order_data = None
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(ORDER_DATA_MARKER):
            try:
                json_str = stripped[len(ORDER_DATA_MARKER):].strip()
                order_data = json.loads(json_str)
            except (json.JSONDecodeError, TypeError):
                pass
            # não adiciona essa linha à mensagem do usuário
        else:
            user_lines.append(line)
    user_message = "\n".join(user_lines).strip()
    return user_message or reply.strip(), order_data


class MessageOrchestrator:
    """Orquestra o processamento de mensagens usando Router + Tools + AI"""
    
    def __init__(self):
        self.router = router_service
        self.tools = tools_registry
        self.ai = ai_integration
        self.policy = policy_layer
        # Estado por user_id para fluxo criar_pedido (IA extrai dados)
        self._order_extraction_state: Dict[str, Dict[str, Any]] = {}
    
    async def process_message(
        self,
        message: str,
        user_id: str,
        token: Optional[str] = None,
        user_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Processa mensagem usando a arquitetura Router + Tools + AI
        
        Args:
            message: Mensagem do usuário
            user_id: ID do usuário
            token: Token de autenticação
            user_state: Estado atual do usuário (fluxos ativos, etc)
            
        Returns:
            {
                "response": str,
                "route_used": str,
                "intent": str,
                "confidence": float,
                "tools_called": List[str],
                "metadata": Dict
            }
        """
        logger.info(
            "Orquestrando processamento de mensagem",
            user_id=user_id,
            message_preview=message[:50]
        )
        
        # 1. Router: só como hint para a IA aprender (intent/confidence/reason). Não usamos para decidir tools.
        route_result = self.router.route(message, user_id, user_state)
        logger.info(
            "Router (hint para IA)",
            user_id=user_id,
            intent=route_result.get("intent"),
            confidence=route_result.get("confidence"),
            reason=route_result.get("reason"),
        )
        
        # 2. Sempre enviar para a IA: ela identifica intents e parâmetros. Depois de aprender, pode-se restringir.
        return await self._handle_ai_route(
            route_result=route_result,
            message=message,
            user_id=user_id,
            token=token,
            user_state=user_state,
        )
    
    async def _handle_tools_route(
        self,
        route_result: Dict[str, Any],
        message: str,
        user_id: str,
        token: Optional[str] = None,
        user_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Processa rota para Tools (determinístico)"""
        intent = route_result["intent"]
        tools_called = []
        
        # Mapear intent para tool
        intent_to_tool = {
            IntentType.PEDIDOS: "listar_pedidos",
            IntentType.ESTOQUE: "consultar_estoque",
            IntentType.FINANCEIRO: "resumo_financeiro",
            IntentType.CLIENTE: "buscar_cliente",
            IntentType.PRODUTO: "listar_produtos",
            IntentType.HOJE: "resumo_hoje",
        }
        
        tool_name = intent_to_tool.get(intent)
        
        if not tool_name:
            # Se não tem tool mapeada, vai para AI
            logger.info(
                "Intent sem tool mapeada, redirecionando para AI",
                intent=intent,
                user_id=user_id
            )
            return await self._handle_ai_route(
                route_result=route_result,
                message=message,
                user_id=user_id,
                token=token,
                user_state=user_state
            )
        
        # Extrair parâmetros básicos da mensagem (heurística simples)
        params = self._extract_params_from_message(message, intent)
        
        # Executar tool
        tool_result = await self.tools.execute(
            tool_name=tool_name,
            params=params,
            user_id=user_id,
            token=token
        )
        
        tools_called.append(tool_name)
        
        if tool_result.ok:
            # Formatar resposta
            response = tool_result.message or "Operação realizada com sucesso."
            
            # Adicionar sugestão se disponível
            if tool_result.user_message_suggestion:
                response += f"\n\n{tool_result.user_message_suggestion}"
            
            return {
                "response": response,
                "route_used": "TOOLS",
                "intent": intent.value if hasattr(intent, 'value') else str(intent),
                "confidence": route_result["confidence"],
                "tools_called": tools_called,
                "metadata": {
                    "tool_result": tool_result.data,
                    "user_id": user_id
                }
            }
        else:
            # Erro na tool - retornar erro ou ir para AI
            error_msg = tool_result.error or "Erro ao executar operação."
            return {
                "response": f"❌ {error_msg}",
                "route_used": "TOOLS",
                "intent": intent.value if hasattr(intent, 'value') else str(intent),
                "confidence": route_result["confidence"],
                "tools_called": tools_called,
                "metadata": {
                    "error": error_msg,
                    "user_id": user_id
                }
            }
    
    async def _handle_ai_route(
        self,
        route_result: Dict[str, Any],
        message: str,
        user_id: str,
        token: Optional[str] = None,
        user_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Tudo vai para a IA: ela identifica intents e parâmetros.
        Router só envia hint (intent/confidence/reason) para aprendizado.
        Se a IA devolver ORDER_DATA, fazemos merge de estado e persistência.
        """
        intent = route_result.get("intent")
        intent_str = intent.value if hasattr(intent, "value") else str(intent) if intent else "unknown"
        
        # Salvar mensagem do usuário logo no início para não perder nenhuma (mesmo se a IA falhar ou der erro depois)
        await self._save_user_message_only(user_id, message)
        
        # Estado de pedido (opcional): a IA pode devolver ORDER_DATA em qualquer resposta (persistido no Redis entre requisições)
        state = await self._get_order_extraction_state(user_id)
        current_order = state.get("current_order") or {
            "customer_name": None,
            "contact_name": None,
            "items": [],
            "delivery_date": None,
        }
        items = current_order.get("items") or []
        current_order = {
            "customer_name": current_order.get("customer_name") or current_order.get("contact_name"),
            "contact_name": current_order.get("contact_name") or current_order.get("customer_name"),
            "items": items,
            "delivery_date": current_order.get("delivery_date"),
        }
        msg_stripped = (message or "").strip()
        # Se o usuário disse "pedido do X", guardar o nome já (para na próxima mensagem já ter cliente)
        client_from_msg = _parse_client_name_from_user_message(msg_stripped)
        if client_from_msg:
            current_order["customer_name"] = client_from_msg
            current_order["contact_name"] = client_from_msg
            state["current_order"] = current_order
            await self._persist_order_state(user_id, state)
        # Se a mensagem parece ser uma data (ex.: 20/03, amanhã), guardar como data de entrega
        if msg_stripped and (
            re.search(r"\d{1,2}/\d{1,2}", msg_stripped)
            or "amanhã" in msg_stripped.lower()
            or ("dia" in msg_stripped.lower() and re.search(r"\d+", msg_stripped))
        ):
            current_order["delivery_date"] = msg_stripped[:50]
            state["current_order"] = current_order
            await self._persist_order_state(user_id, state)
        # Itens parseados da mensagem atual: usamos o que o usuário digitou (ex.: Rucula) para a IA não trocar por outro (ex.: couve)
        parsed_items = _parse_items_from_user_message(message)
        if parsed_items:
            current_order["items"] = [{"product_name": p.get("product_name", "").strip(), "quantity": int(p.get("quantity", 0))} for p in parsed_items if p.get("product_name") and p.get("quantity", 0) > 0]
            state["current_order"] = current_order
            await self._persist_order_state(user_id, state)
            logger.info("Itens extraídos da mensagem do usuário (prioridade sobre IA)", user_id=user_id, items=current_order["items"])
        
        # Histórico: mensagens salvas (DB/Redis) — SEMPRE enviadas à IA; se faltam itens, puxar da conversa recente
        history_text = ""
        if context_service and Message is not None and MessageType is not None:
            try:
                ctx = await context_service.get_conversation_context(user_id)
                last_n = (ctx.message_history or [])[-20:]
                # Evitar duplicar a mensagem atual no bloco de histórico (ela já foi salva no início e vai em "Mensagem atual")
                if last_n and last_n[-1].message_type == MessageType.USER and (last_n[-1].content or "").strip() == (message or "").strip():
                    last_n = last_n[:-1]
                parts = []
                for m in last_n:
                    role = "Usuário" if m.message_type == MessageType.USER else "Bot"
                    content = (m.content or "")[:600]  # trecho maior para não cortar contexto
                    parts.append(f"- {role}: {content}")
                history_text = "\n".join(parts) if parts else ""
                # Se a mensagem atual não trouxe itens mas temos cliente e histórico, puxar itens da conversa recente
                if not parsed_items and not (current_order.get("items")):
                    for m in reversed(last_n):
                        if m.message_type != MessageType.USER:
                            continue
                        content = (m.content or "").strip()
                        if not content or content == message.strip():
                            continue
                        items_from_history = _parse_items_from_user_message(content)
                        if items_from_history:
                            current_order["items"] = [{"product_name": p.get("product_name", "").strip(), "quantity": int(p.get("quantity", 0))} for p in items_from_history if p.get("product_name") and p.get("quantity", 0) > 0]
                            state["current_order"] = current_order
                            await self._persist_order_state(user_id, state)
                            logger.info("Itens puxados da conversa recente (usuário já tinha citado)", user_id=user_id, items=current_order["items"])
                            break
                # Se temos itens mas não temos cliente, puxar nome do histórico (ex.: bot disse "já temos Adriano" ou usuário disse "pedido do Adriano")
                if (parsed_items or current_order.get("items")) and not (current_order.get("customer_name") or current_order.get("contact_name")):
                    for m in reversed(last_n):
                        content = (m.content or "").strip()
                        if not content:
                            continue
                        name = _extract_client_name_from_text(content) if m.message_type == MessageType.BOT else _parse_client_name_from_user_message(content)
                        if name:
                            current_order["customer_name"] = name
                            current_order["contact_name"] = name
                            state["current_order"] = current_order
                            await self._persist_order_state(user_id, state)
                            logger.info("Cliente puxado do histórico (para resposta direta)", user_id=user_id, customer_name=name)
                            break
                if history_text:
                    logger.info(
                        "Enviando histórico para a IA",
                        user_id=user_id,
                        num_mensagens=len(parts),
                        preview=history_text[:200].replace("\n", " "),
                    )
                else:
                    logger.info("Histórico vazio para este usuário", user_id=user_id)
            except Exception as e:
                logger.warning("Falha ao obter histórico de conversa", user_id=user_id, error=str(e))
        
        # Resposta direta quando já temos cliente e itens mas falta data: perguntar SÓ o que falta (sem IA = sem "para quem é?" nem exemplo com produto errado)
        contact_name = (current_order.get("contact_name") or current_order.get("customer_name") or "").strip()
        order_items = current_order.get("items") or []
        has_items = bool(order_items)
        delivery_date = (current_order.get("delivery_date") or "").strip()
        if contact_name and has_items and not delivery_date:
            # Uma pergunta só: data. Resposta curta e natural.
            direct_reply = "Falta só a data de entrega. Qual data?"
            logger.info("Resposta direta (já tem cliente e itens, pergunta só data)", user_id=user_id)
            await self._save_conversation_turn(user_id, message, direct_reply)
            return self._ai_route_result(direct_reply, intent_str, route_result, user_id)
        if contact_name and has_items and delivery_date:
            # Se respondeu "sim" / "confirmo", salvar o pedido direto (sem IA)
            if msg_stripped.lower() in ("sim", "confirmo", "pode salvar", "está certo", "confirmar", "pode confirmar"):
                normalized = [{"product_name": (it.get("product_name") or "").strip(), "qty": int(it.get("quantity") or it.get("qty", 0))} for it in order_items if (it.get("product_name") or "").strip()]
                if normalized:
                    try:
                        success, msg, created = await telegram_order_parser.process_orders(
                            [{"contact_name": contact_name, "establishment_name": None, "contact_phone": None, "price_profile_hint": None, "items": normalized}],
                            conversation_id=str(uuid.uuid4()), token=token,
                        )
                        await self._clear_order_extraction_state(user_id)
                        reply = f"✅ Pedido registrado.\n{msg}" if (success and created) else (msg or "Pedido enviado.")
                    except Exception as e:
                        logger.error("Erro ao salvar pedido", user_id=user_id, error=str(e), exc_info=True)
                        reply = f"❌ Erro ao salvar: {str(e)}. Tente novamente."
                    await self._save_conversation_turn(user_id, message, reply)
                    return self._ai_route_result(reply, intent_str, route_result, user_id, metadata={"order_saved": True})
            # Pedir confirmação em uma frase.
            direct_reply = f"Tudo certo. Confirma o pedido? (responda *sim* para salvar)"
            logger.info("Resposta direta (pedindo confirmação)", user_id=user_id)
            await self._save_conversation_turn(user_id, message, direct_reply)
            return self._ai_route_result(direct_reply, intent_str, route_result, user_id)
        
        # Log do que enviamos à IA (para debugar: estado tem cliente? histórico?)
        logger.info(
            "Contexto enviado à IA",
            user_id=user_id,
            customer_name=current_order.get("customer_name") or current_order.get("contact_name"),
            num_items=len(current_order.get("items") or []),
            tem_historico=bool(history_text),
        )
        full_prompt = self._build_unified_prompt(message, current_order, history_text=history_text)
        
        try:
            ai_response = await self.ai.chat_simple(
                full_prompt,
                intent=intent_str,
                confidence=route_result.get("confidence"),
                intent_reason=route_result.get("reason"),
                user_id=user_id,
            )
            
            if not ai_response or not ai_response.strip():
                response_text = self._fallback_response(intent, route_result)
                await self._save_conversation_turn(user_id, message, response_text)
                return self._ai_route_result(response_text, intent_str, route_result, user_id, ai_failed=True)
            
            user_message, order_data = _parse_order_data_from_reply(ai_response)
            
            if order_data:
                if order_data.get("customer_name") is not None:
                    current_order["customer_name"] = order_data["customer_name"]
                    current_order["contact_name"] = order_data["customer_name"]
                # Só aceitar itens da IA se nós não parseamos itens da mensagem (evitar IA trocar rucula por couve)
                if order_data.get("items") and not parsed_items:
                    current_order["items"] = order_data["items"]
                elif parsed_items:
                    # Manter os itens que o usuário digitou (já estão em current_order)
                    pass
                state["current_order"] = current_order
                await self._persist_order_state(user_id, state)
                can_save = order_data.get("can_save_now", False)
                contact_name = (current_order.get("contact_name") or current_order.get("customer_name") or "").strip()
                order_items = current_order.get("items") or []
                normalized_items = []
                for it in order_items:
                    qty = it.get("quantity") if "quantity" in it else it.get("qty", 0)
                    name = (it.get("product_name") or it.get("product") or "").strip()
                    if name and qty > 0:
                        normalized_items.append({"product_name": name, "qty": int(qty)})
                if can_save and contact_name and normalized_items:
                    orders_payload = [{
                        "contact_name": contact_name,
                        "establishment_name": None,
                        "contact_phone": None,
                        "price_profile_hint": None,
                        "items": normalized_items,
                    }]
                    try:
                        success, msg, created = await telegram_order_parser.process_orders(
                            orders_payload, conversation_id=str(uuid.uuid4()), token=token
                        )
                        await self._clear_order_extraction_state(user_id)
                        response_text = f"✅ Pedido registrado.\n{msg}" if (success and created) else (msg or "Pedido enviado.")
                    except Exception as e:
                        logger.error("Erro ao persistir pedido", user_id=user_id, error=str(e), exc_info=True)
                        response_text = f"❌ Erro ao salvar: {str(e)}. Tente novamente ou use o menu de pedidos."
                    await self._save_conversation_turn(user_id, message, response_text)
                    return self._ai_route_result(response_text, intent_str, route_result, user_id, metadata={"order_saved": True})
            else:
                # Fallback: IA disse o nome na resposta mas não enviou ORDER_DATA — extrair para não perder
                extracted_name = _extract_client_name_from_text(ai_response)
                if extracted_name and not (current_order.get("customer_name") or current_order.get("contact_name")):
                    current_order["customer_name"] = extracted_name
                    current_order["contact_name"] = extracted_name
                    state["current_order"] = current_order
                    await self._persist_order_state(user_id, state)
            
            reply_to_show = user_message.strip() if user_message and user_message.strip() else ai_response.strip()
            await self._save_conversation_turn(user_id, message, reply_to_show)
            return self._ai_route_result(reply_to_show, intent_str, route_result, user_id)
                
        except Exception as e:
            logger.error("Erro ao chamar AI Service", user_id=user_id, error=str(e), exc_info=True)
            response_text = self._fallback_response(intent, route_result)
            await self._save_conversation_turn(user_id, message, response_text)
            return self._ai_route_result(response_text, intent_str, route_result, user_id, metadata={"error": str(e)})
    
    async def _save_user_message_only(self, user_id: str, user_message: str) -> None:
        """Grava só a mensagem do usuário no início do processamento para nunca perder (ex.: '02 Alface 01 Rucula')."""
        if not context_service or not Message or not MessageType or not (user_message or "").strip():
            return
        try:
            await context_service.add_message_to_context(
                user_id,
                Message(id=str(uuid.uuid4()), user_id=user_id, content=user_message.strip(), timestamp=datetime.utcnow(), message_type=MessageType.USER),
            )
        except Exception as e:
            logger.warning("Falha ao salvar mensagem do usuário no histórico", user_id=user_id, error=str(e))

    async def _save_conversation_turn(self, user_id: str, user_message: str, bot_message: str) -> None:
        """Grava a resposta do bot no histórico (mensagem do usuário já foi salva no início do processamento)."""
        if not context_service or not Message or not MessageType:
            return
        try:
            now = datetime.utcnow()
            await context_service.add_message_to_context(
                user_id,
                Message(id=str(uuid.uuid4()), user_id=user_id, content=bot_message or "", timestamp=now, message_type=MessageType.BOT),
            )
            logger.info(
                "Resposta do bot salva no histórico",
                user_id=user_id,
                user_msg_preview=(user_message or "")[:80],
                bot_msg_len=len(bot_message or ""),
            )
        except Exception as e:
            logger.warning("Falha ao salvar resposta do bot no histórico", user_id=user_id, error=str(e))

    def _build_unified_prompt(self, message: str, current_order: Dict[str, Any], history_text: Optional[str] = None) -> str:
        """Prompt único: IA conduz o fluxo de pedido; histórico (mensagens salvas) é enviado para a IA usar."""
        try:
            order_json = json.dumps(current_order, ensure_ascii=False)
        except Exception:
            order_json = "{}"
        # Quando já temos cliente e itens, deixar explícito: é continuação, NÃO recomeçar
        has_client = bool((current_order.get("customer_name") or current_order.get("contact_name") or "").strip())
        has_items = bool(current_order.get("items"))
        continuation_block = ""
        if has_client and has_items:
            itens_str = ", ".join(f"{it.get('quantity', 0)} {it.get('product_name', '').strip()}" for it in (current_order.get("items") or [])[:10])
            continuation_block = (
                "\n\n>>> CONTINUAÇÃO DE PEDIDO: O pedido JÁ TEM cliente e itens (veja estado abaixo). "
                "NÃO peça nome do cliente nem itens de novo. Diga o resumo (ex.: 'Pedido do {0}: {1}') e peça APENAS data de entrega e confirmação. <<<\n\n"
            ).format((current_order.get("customer_name") or current_order.get("contact_name") or "").strip(), itens_str)
        # Histórico vai logo antes da mensagem atual para a IA usar — não pedir de novo o que já está no histórico
        history_block = ""
        if history_text and history_text.strip():
            history_block = (
                "\n\n--- HISTÓRICO DA CONVERSA (o que já foi dito — USE e NÃO peça de novo) ---\n"
                + history_text.strip()
                + "\n--- Fim do histórico ---\n\n"
            )
        return (
            "Você é o assistente da horta (pedidos, estoque, financeiro). "
            "Identifique a intenção e responda em português de forma natural.\n\n"
            "REGRA 1 — Se no 'Estado atual do pedido' ou no HISTÓRICO já constarem cliente e itens, NÃO recomece a conversa: NÃO peça nome nem itens de novo. Prossiga para data de entrega e confirmação.\n\n"
            "REGRA 2 — Use EXATAMENTE os produtos que o usuário informou (ex.: rucula é rucula, não troque por couve).\n\n"
            + continuation_block
            + "Estado atual do pedido em construção: " + order_json + ".\n\n"
            "REGISTRO DE PEDIDO: Coletar só o que faltar. Se já tem cliente e itens, peça só data de entrega e confirme. Termine com: ORDER_DATA: {\"customer_name\": \"...\", \"items\": [...], \"delivery_date\": \"... ou null\", \"can_save_now\": false ou true}.\n"
            + history_block
            + "Mensagem atual do usuário: " + message
        )
    
    def _ai_route_result(
        self,
        response: str,
        intent_str: str,
        route_result: Dict[str, Any],
        user_id: str,
        *,
        ai_failed: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        out = {
            "response": response,
            "route_used": "AI",
            "intent": intent_str,
            "confidence": route_result.get("confidence", 0),
            "tools_called": [],
            "metadata": {"user_id": user_id, **(metadata or {})},
        }
        if ai_failed:
            out["metadata"]["ai_failed"] = True
        return out
    
    async def _get_order_extraction_state(self, user_id: str) -> Dict[str, Any]:
        """Obtém estado de extração de pedido (Redis primeiro, para compartilhar entre workers)."""
        if context_service and getattr(context_service, "get_order_state", None):
            try:
                saved = await context_service.get_order_state(user_id)
                if saved and isinstance(saved, dict) and saved.get("current_order") is not None:
                    self._order_extraction_state[user_id] = saved
                    return saved
            except Exception as e:
                logger.warning("Falha ao carregar order_state do Redis", user_id=user_id, error=str(e))
        if user_id not in self._order_extraction_state:
            self._order_extraction_state[user_id] = _order_extraction_state_default()
        return self._order_extraction_state[user_id]

    async def _persist_order_state(self, user_id: str, state: Dict[str, Any]) -> None:
        """Persiste estado do pedido no Redis para a próxima requisição (mesmo em outro worker)."""
        if context_service and getattr(context_service, "save_order_state", None):
            try:
                await context_service.save_order_state(user_id, state)
            except Exception as e:
                logger.warning("Falha ao salvar order_state no Redis", user_id=user_id, error=str(e))
    
    async def _clear_order_extraction_state(self, user_id: str) -> None:
        """Limpa estado de extração de pedido após salvar ou cancelar (memória e Redis)."""
        self._order_extraction_state.pop(user_id, None)
        if context_service and getattr(context_service, "clear_order_state", None):
            try:
                await context_service.clear_order_state(user_id)
            except Exception as e:
                logger.warning("Falha ao limpar order_state no Redis", user_id=user_id, error=str(e))
    
    def _fallback_response(self, intent: Any, route_result: Dict[str, Any]) -> str:
        """
        Resposta de fallback quando o AI Service falha ou não responde.
        """
        intent_str = (intent.value if hasattr(intent, "value") else str(intent)) if intent else "unknown"
        
        if intent_str == "cumprimento":
            return (
                "Olá! Tudo bem?\n\n"
                "Como posso ajudá-lo hoje? Estou à disposição para pedidos, estoque e financeiro da horta.\n\n"
                "Comandos disponíveis:\n"
                "• /menu — Abrir menu principal\n"
                "• /hoje — Resumo operacional do dia\n"
                "• /pedidos — Listar pedidos\n"
                "• /estoque — Ver estoque atual\n"
                "• /financeiro — Resumo financeiro"
            )
        
        if intent_str == "conversa":
            return (
                "Entendi. No momento estou focado em pedidos, estoque e financeiro da horta. "
                "Use /menu para ver as opções ou diga como posso ajudar."
            )
        
        if intent_str == "criar_pedido":
            return (
                "Para registrar um pedido, use o menu de pedidos ou digite no formato: "
                "Nome do cliente: quantidade produto (ex: Adriano: 2 alface 1 couve)."
            )
        
        # Fallback genérico para outras intents
        return (
            "Desculpe, não consegui processar sua mensagem. "
            "Tente novamente ou use um dos comandos: /menu, /pedidos, /estoque, /financeiro"
        )
    
    def _extract_params_from_message(self, message: str, intent: IntentType) -> Dict[str, Any]:
        """Extrai parâmetros básicos da mensagem (heurística simples)"""
        params = {}
        message_lower = message.lower()
        
        # Extrair data se mencionada
        import re
        date_pattern = r"(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{2,4})"
        date_match = re.search(date_pattern, message)
        if date_match:
            params["data"] = message[date_match.start():date_match.end()]
        
        # Extrair nome de produto/cliente (palavras após certas palavras-chave)
        if intent == IntentType.ESTOQUE:
            # Tentar extrair nome do produto
            product_keywords = ["produto", "tem", "disponível", "disponivel"]
            for keyword in product_keywords:
                if keyword in message_lower:
                    # Pegar palavras após a keyword
                    parts = message_lower.split(keyword, 1)
                    if len(parts) > 1:
                        # Pegar primeira palavra após a keyword
                        words = parts[1].strip().split()
                        if words:
                            params["produto"] = words[0]
                            break
        
        return params


# Instância global
message_orchestrator = MessageOrchestrator()
