"""
Serviço para processar pedidos recebidos via Telegram
Parseia texto do formato: "Dona Dilma: 08 Couve 04 Coentros 04 Cebolinhas"
"""

import re
import uuid
import json
from typing import List, Dict, Any, Optional, Tuple
import structlog
import httpx

from services.commerce_client import commerce_client

logger = structlog.get_logger(__name__)


class TelegramOrderParser:
    """Parser de pedidos do Telegram"""
    
    # Pronomes a serem removidos dos nomes
    PRONOUNS = [
        r"^dona\s+",
        r"^don\s+",
        r"^senhor\s+",
        r"^senhora\s+",
        r"^sr\.?\s+",
        r"^sra\.?\s+",
    ]
    
    def remove_pronouns(self, name: str) -> str:
        """Remove pronomes do nome do contato"""
        name = name.strip()
        for pronoun_pattern in self.PRONOUNS:
            name = re.sub(pronoun_pattern, "", name, flags=re.IGNORECASE)
        return name.strip()
    
    def parse_order_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Parseia texto de pedido do Telegram
        
        Formato esperado:
        "Dona Dilma: 08 Couve 04 Coentros 04 Cebolinhas 01 palito alface roxa"
        
        Pode ter múltiplos pedidos separados por quebras de linha ou repetições
        
        Returns:
            Lista de pedidos parseados
        """
        orders = []
        text = text.strip()
        
        # Dividir por linhas ou por padrão de nome seguido de dois pontos
        # Padrão: "Nome: produtos" ou "Nome produtos"
        lines = text.split('\n')
        
        current_order = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Verificar se a linha contém um nome seguido de dois pontos ou espaço
            # Padrão: "Nome: produtos" ou "Nome produtos"
            name_match = re.match(r'^([^:]+?):\s*(.+)$', line, re.IGNORECASE)
            if name_match:
                # Novo pedido encontrado
                if current_order:
                    orders.append(current_order)
                
                contact_name = self.remove_pronouns(name_match.group(1).strip())
                products_text = name_match.group(2).strip()
                
                # Se products_text começa com número (ex: "08 Couve"), está ok
                # Se começa com letra (ex: "Couve04"), também está ok
                # O parser de produtos vai lidar com ambos
                
                current_order = {
                    "contact_name": contact_name,
                    "establishment_name": None,
                    "contact_phone": None,
                    "price_profile_hint": None,
                    "items": self._parse_products(products_text)
                }
            elif current_order:
                # Continuar parseando produtos na mesma linha ou próxima
                # Pode ser continuação do pedido anterior ou novo pedido sem nome
                products = self._parse_products(line)
                if products:
                    current_order["items"].extend(products)
                else:
                    # Se não conseguiu parsear produtos, pode ser um novo pedido sem nome explícito
                    # Tentar detectar se é um nome seguido de produtos
                    name_match_inline = re.match(r'^([A-Za-zÀ-ÿ\s]+?)\s+(\d+)', line, re.IGNORECASE)
                    if name_match_inline:
                        # Novo pedido sem dois pontos
                        if current_order:
                            orders.append(current_order)
                        
                        contact_name = self.remove_pronouns(name_match_inline.group(1).strip())
                        remaining_text = line[len(name_match_inline.group(1)):].strip()
                        
                        current_order = {
                            "contact_name": contact_name,
                            "establishment_name": None,
                            "contact_phone": None,
                            "price_profile_hint": None,
                            "items": self._parse_products(remaining_text)
                        }
            else:
                # Primeira linha sem nome explícito - tentar detectar nome e produtos
                name_match_inline = re.match(r'^([A-Za-zÀ-ÿ\s]+?)\s+(\d+)', line, re.IGNORECASE)
                if name_match_inline:
                    contact_name = self.remove_pronouns(name_match_inline.group(1).strip())
                    remaining_text = line[len(name_match_inline.group(1)):].strip()
                    
                    current_order = {
                        "contact_name": contact_name,
                        "establishment_name": None,
                        "contact_phone": None,
                        "price_profile_hint": None,
                        "items": self._parse_products(remaining_text)
                    }
                else:
                    # Tentar parsear como apenas produtos (sem nome)
                    products = self._parse_products(line)
                    if products:
                        # Criar pedido sem nome
                        current_order = {
                            "contact_name": None,
                            "establishment_name": None,
                            "contact_phone": None,
                            "price_profile_hint": None,
                            "items": products
                        }
        
        # Adicionar último pedido
        if current_order:
            orders.append(current_order)
        
        return orders
    
    def _parse_products(self, text: str) -> List[Dict[str, Any]]:
        """
        Parseia produtos e quantidades do texto
        
        Formato: "08 Couve 04 Coentros 01 palito alface roxa"
        Também aceita: "Couve04 Coentros04" (sem espaços)
        Aceita padrões mistos: "08 Couve04 Coentros04 01 palito alface roxa"
        
        Returns:
            Lista de itens com qty e product_name
        """
        items = []
        
        # Normalizar texto: garantir que haja espaço entre número e letra quando necessário
        # Isso ajuda a processar padrões mistos como "08Couve" ou "Couve04"
        # Mas preserva espaços existentes
        
        # Padrão 1: número seguido de espaço seguido de nome do produto
        # Exemplos: "08 Couve", "01 palito alface roxa", "04 Coentros"
        pattern_with_space = r'(\d+)\s+([A-Za-zÀ-ÿ\s]+?)(?=\s+\d+|$)'
        
        # Padrão 2: nome do produto seguido de número (sem espaço entre eles)
        # Exemplos: "Couve04", "Coentros04", "alface roxa01"
        # Mas precisa ter espaço antes do produto ou ser início da string
        # Usar alternativas ao invés de lookbehind variável
        pattern_product_number = r'(?:^|\s)([A-Za-zÀ-ÿ\s]+?)(\d+)(?=[A-Za-zÀ-ÿ]|\s+\d+|$)'
        
        # Padrão 3: número seguido diretamente de letra (sem espaço)
        # Exemplos: "08Couve", "04Coentros" (quando número está no início ou após espaço)
        # Usar alternativas ao invés de lookbehind variável
        pattern_number_letter = r'(?:^|:|\s)(\d+)([A-Za-zÀ-ÿ]+)(?=\s+\d+|\d+[A-Za-zÀ-ÿ]|$)'
        
        # Primeiro, tentar padrão com espaço (mais comum e confiável)
        matches = re.finditer(pattern_with_space, text, re.IGNORECASE)
        for match in matches:
            qty_str = match.group(1)
            product_name = match.group(2).strip()
            
            try:
                qty = int(qty_str)
                if qty > 0 and product_name:
                    items.append({
                        "qty": qty,
                        "product_name": product_name
                    })
            except ValueError:
                logger.warning(f"Quantidade inválida: {qty_str}")
                continue
        
        # Se encontrou itens com espaços, marcar posições já processadas
        processed_positions = set()
        if items:
            # Re-processar para marcar posições
            matches = re.finditer(pattern_with_space, text, re.IGNORECASE)
            for match in matches:
                processed_positions.add((match.start(), match.end()))
        
        # Tentar padrão produto-número (sem espaço) em posições não processadas
        matches = re.finditer(pattern_product_number, text, re.IGNORECASE)
        for match in matches:
            # Verificar se esta posição já foi processada
            is_processed = any(
                match.start() >= start and match.end() <= end
                for start, end in processed_positions
            )
            if is_processed:
                continue
                
            product_name = match.group(1).strip()
            qty_str = match.group(2)
            
            try:
                qty = int(qty_str)
                if qty > 0 and product_name:
                    items.append({
                        "qty": qty,
                        "product_name": product_name
                    })
                    processed_positions.add((match.start(), match.end()))
            except ValueError:
                logger.warning(f"Quantidade inválida: {qty_str}")
                continue
        
        # Tentar padrão número-letra (sem espaço) em posições não processadas
        matches = re.finditer(pattern_number_letter, text, re.IGNORECASE)
        for match in matches:
            # Verificar se esta posição já foi processada
            is_processed = any(
                match.start() >= start and match.end() <= end
                for start, end in processed_positions
            )
            if is_processed:
                continue
            
            qty_str = match.group(1)
            product_name = match.group(2).strip()
            
            try:
                qty = int(qty_str)
                if qty > 0 and product_name:
                    items.append({
                        "qty": qty,
                        "product_name": product_name
                    })
                    processed_positions.add((match.start(), match.end()))
            except ValueError:
                logger.warning(f"Quantidade inválida: {qty_str}")
                continue
        
        return items
    
    async def search_product(
        self,
        product_name: str,
        token: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Busca produto no e-commerce service
        
        Returns:
            Produto encontrado ou None
        """
        try:
            products = await commerce_client.search_products(product_name, token=token)
            
            if not products:
                return None
            
            # Se houver apenas um resultado, usar ele
            if len(products) == 1:
                return products[0]
            
            # Se houver múltiplos, tentar matching mais preciso
            product_name_lower = product_name.lower().strip()
            
            # Buscar match exato (case insensitive)
            for product in products:
                if product.get("name", "").lower() == product_name_lower:
                    return product
            
            # Buscar match parcial
            for product in products:
                product_name_db = product.get("name", "").lower()
                if product_name_lower in product_name_db or product_name_db in product_name_lower:
                    return product
            
            # Se não encontrou match preciso, retornar o primeiro
            logger.warning(
                f"Múltiplos produtos encontrados para '{product_name}', usando o primeiro",
                products=[p.get("name") for p in products[:3]]
            )
            return products[0]
            
        except Exception as e:
            logger.error(f"Erro ao buscar produto '{product_name}': {e}", exc_info=True)
            return None
    
    async def process_orders(
        self,
        orders: List[Dict[str, Any]],
        conversation_id: Optional[str] = None,
        token: Optional[str] = None
    ) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """
        Processa pedidos: busca produtos e envia para o e-commerce service
        
        Args:
            orders: Lista de pedidos parseados
            conversation_id: ID da conversa (opcional)
            token: Token de autenticação Keycloak
            
        Returns:
            Tuple (success, message, created_orders)
        """
        if not orders:
            return False, "Nenhum pedido encontrado no texto", []
        
        # Buscar produtos para cada pedido
        for order in orders:
            for item in order.get("items", []):
                product_name = item.get("product_name")
                if not product_name:
                    continue
                
                # Buscar produto no e-commerce service
                product = await self.search_product(product_name, token=token)
                
                if product:
                    item["product_id"] = product.get("id")
                    logger.info(
                        f"Produto identificado: {product_name} -> ID {product.get('id')}"
                    )
                else:
                    item["product_id"] = None
                    logger.warning(f"Produto não encontrado: {product_name}")
        
        # Preparar dados para envio
        bulk_data = {
            "orders": orders
        }
        
        if conversation_id:
            bulk_data["conversation_id"] = conversation_id
        else:
            # Gerar UUID para conversa se não fornecido
            bulk_data["conversation_id"] = str(uuid.uuid4())
        
        # Enviar pedidos para o e-commerce service
        base_url = commerce_client.base_url
        
        # LOG DETALHADO ANTES DE ENVIAR
        logger.info("=" * 70)
        logger.info("PREPARANDO PARA ENVIAR PEDIDOS AO E-COMMERCE")
        logger.info("=" * 70)
        logger.info(
            "Dados do pedido que sera enviado",
            endpoint=f"{base_url}/v1/chatbot/orders/bulk",
            orders_count=len(orders),
            conversation_id=conversation_id,
            conversation_id_type=type(conversation_id).__name__,
            has_token=bool(token),
            token_preview=token[:20] + "..." if token else None,
            bulk_data_keys=list(bulk_data.keys())
        )
        
        # Log detalhado de cada pedido
        for i, order in enumerate(orders, 1):
            logger.info(
                f"Pedido {i} detalhado",
                contact_name=order.get("contact_name"),
                establishment_name=order.get("establishment_name"),
                contact_phone=order.get("contact_phone"),
                price_profile_hint=order.get("price_profile_hint"),
                items_count=len(order.get("items", [])),
                items=[{
                    "qty": item.get("qty"),
                    "product_name": item.get("product_name"),
                    "product_id": item.get("product_id")
                } for item in order.get("items", [])]
            )
        
        # Log do JSON completo que será enviado
        try:
            bulk_data_json = json.dumps(bulk_data, indent=2, ensure_ascii=False)
            logger.info("=" * 70)
            logger.info("JSON COMPLETO QUE SERA ENVIADO:")
            logger.info(bulk_data_json)
            logger.info("=" * 70)
        except Exception as e:
            logger.warning(f"Nao foi possivel serializar JSON para log: {e}")
        
        try:
            logger.info("=" * 70)
            logger.info("CHAMANDO commerce_client.create_orders_bulk")
            logger.info("=" * 70)
            logger.info(
                "Parametros da chamada",
                endpoint=f"{base_url}/v1/chatbot/orders/bulk",
                conversation_id=conversation_id,
                has_token=bool(token)
            )
            
            created_orders = await commerce_client.create_orders_bulk(bulk_data, token=token)
            
            logger.info("=" * 70)
            logger.info("RESPOSTA RECEBIDA DO E-COMMERCE SERVICE")
            logger.info("=" * 70)
            logger.info(
                "Resposta basica",
                has_response=bool(created_orders),
                response_type=type(created_orders).__name__,
                response_length=len(created_orders) if isinstance(created_orders, list) else "N/A"
            )
            
            # Log detalhado da resposta
            if created_orders:
                try:
                    response_json = json.dumps(created_orders, indent=2, ensure_ascii=False, default=str)
                    logger.info("RESPOSTA JSON COMPLETA:")
                    logger.info(response_json)
                except Exception as e:
                    logger.warning(f"Nao foi possivel serializar resposta JSON: {e}")
                    logger.info("Resposta como string:", response_preview=str(created_orders)[:1000])
                
                # Log de cada pedido criado
                for i, order in enumerate(created_orders, 1):
                    logger.info(
                        f"Pedido criado {i}",
                        order_id=order.get("id"),
                        order_number=order.get("order_number"),
                        status=order.get("status"),
                        customer_id=order.get("customer_id"),
                        subtotal=order.get("subtotal"),
                        total=order.get("total"),
                        items_count=len(order.get("items", [])),
                        order_full=order
                    )
            else:
                logger.warning("RESPOSTA VAZIA - nenhum pedido foi retornado")
            logger.info("=" * 70)
            
            # VALIDAÇÃO CRÍTICA: Verificar se realmente foram criados pedidos
            if not created_orders:
                logger.error(
                    "Nenhum pedido foi retornado pelo e-commerce service",
                    orders_sent=len(orders),
                    bulk_data=bulk_data
                )
                return False, "❌ Erro: Nenhum pedido foi criado. O e-commerce service pode estar offline ou os produtos não foram identificados corretamente.", []
            
            # Validar que os pedidos têm IDs (indicando que foram realmente salvos)
            valid_orders = []
            for order in created_orders:
                order_id = order.get('id')
                if order_id:
                    valid_orders.append(order)
                else:
                    logger.warning(
                        "Pedido retornado sem ID - pode não ter sido salvo",
                        order=order
                    )
            
            if not valid_orders:
                logger.error(
                    "Nenhum pedido válido foi retornado (sem IDs)",
                    created_orders=created_orders
                )
                return False, "❌ Erro: Os pedidos foram processados mas não foram salvos. Verifique se o e-commerce service está funcionando corretamente.", []
            
            success_count = len(valid_orders)
            total_items = sum(len(order.get("items", [])) for order in orders)
            
            logger.info(
                "Pedidos criados com sucesso",
                success_count=success_count,
                total_items=total_items,
                order_ids=[o.get('id') for o in valid_orders]
            )
            
            return True, f"✅ {success_count} pedido(s) criado(s) com sucesso! Total de {total_items} item(ns).", valid_orders
            
        except httpx.HTTPStatusError as e:
            # Erros HTTP específicos
            status_code = e.response.status_code
            error_detail = ""
            error_text = ""
            
            try:
                error_text = e.response.text
                error_response = e.response.json()
                error_detail = error_response.get("detail", error_response.get("message", str(e)))
            except:
                error_detail = str(e)
                error_text = str(e.response.text) if hasattr(e.response, 'text') else ""
            
            # LOG DETALHADO DO ERRO
            base_url = commerce_client.base_url
            logger.error(
                "ERRO HTTP ao criar pedidos no e-commerce service",
                status_code=status_code,
                endpoint=f"{base_url}/v1/chatbot/orders/bulk",
                error_detail=error_detail,
                error_text=error_text,
                has_token=bool(token),
                token_preview=token[:20] + "..." if token else None,
                orders_count=len(orders),
                conversation_id=conversation_id,
                exc_info=True
            )
            
            if status_code == 401:
                error_msg = "❌ Erro de autenticação: Token inválido ou expirado. Não foi possível salvar o pedido."
                logger.error(
                    "AUTENTICACAO FALHOU - Token invalido ou expirado",
                    has_token=bool(token),
                    token_provided=bool(token),
                    endpoint=f"{commerce_client.base_url}/v1/chatbot/orders/bulk"
                )
                return False, error_msg, []
            elif status_code == 404:
                error_msg = "❌ Erro: Endpoint não encontrado. O e-commerce service pode estar offline ou com versão incompatível."
                logger.error(
                    "ENDPOINT NAO ENCONTRADO",
                    endpoint=f"{commerce_client.base_url}/v1/chatbot/orders/bulk",
                    status_code=404
                )
                return False, error_msg, []
            elif status_code == 500:
                error_msg = "❌ Erro interno do e-commerce service. Tente novamente mais tarde."
                logger.error(
                    "ERRO INTERNO DO E-COMMERCE SERVICE",
                    status_code=500,
                    error_detail=error_detail
                )
                return False, error_msg, []
            else:
                error_msg = f"❌ Erro ao criar pedidos (HTTP {status_code}): {error_detail}"
                logger.error(
                    "ERRO HTTP DESCONHECIDO ao criar pedidos",
                    status_code=status_code,
                    error_detail=error_detail
                )
                return False, error_msg, []
                
        except httpx.RequestError as e:
            # Erros de conexão (serviço offline, timeout, etc.)
            logger.error(
                "ERRO DE CONEXAO com e-commerce service",
                error=str(e),
                error_type=type(e).__name__,
                endpoint=f"{commerce_client.base_url}/v1/chatbot/orders/bulk",
                timeout=commerce_client.timeout,
                has_token=bool(token),
                orders_count=len(orders),
                conversation_id=conversation_id,
                exc_info=True
            )
            return False, "❌ Erro: Não foi possível conectar ao e-commerce service. O serviço pode estar offline. O pedido NÃO foi salvo.", []
            
        except Exception as e:
            # Outros erros inesperados
            logger.error(
                "ERRO INESPERADO ao criar pedidos",
                error=str(e),
                error_type=type(e).__name__,
                endpoint=f"{commerce_client.base_url}/v1/chatbot/orders/bulk",
                has_token=bool(token),
                orders_count=len(orders),
                conversation_id=conversation_id,
                exc_info=True
            )
            return False, f"❌ Erro inesperado ao criar pedidos: {str(e)}. O pedido NÃO foi salvo.", []


# Instância global
telegram_order_parser = TelegramOrderParser()
