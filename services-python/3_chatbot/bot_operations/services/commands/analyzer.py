"""
Analisador de comandos - detecta comandos em mensagens de texto
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from .types import CommandAnalysis, CommandDefinition
from .definitions import ALL_COMMANDS
import structlog

logger = structlog.get_logger(__name__)


class CommandAnalyzer:
    """Analisador que detecta comandos em mensagens de texto"""
    
    def __init__(self):
        self.command_patterns = self._build_command_patterns()
        self.symbol_pattern = re.compile(r'\b([A-Z]{4}\d)\b', re.IGNORECASE)
        self.number_pattern = re.compile(r'\b(\d+(?:\.\d+)?)\b')
    
    def _build_command_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Constrói padrões de regex para cada comando"""
        patterns = {}
        
        for command_id, command in ALL_COMMANDS.items():
            command_patterns = []
            
            # Padrão base do comando (com e sem "/")
            command_patterns.append(re.compile(
                rf'\b{re.escape(command_id)}\b', 
                re.IGNORECASE
            ))
            command_patterns.append(re.compile(
                rf'/{re.escape(command_id)}\b', 
                re.IGNORECASE
            ))
            
            # Padrões dos aliases (com e sem "/")
            for alias in command.aliases:
                command_patterns.append(re.compile(
                    rf'\b{re.escape(alias)}\b', 
                    re.IGNORECASE
                ))
                command_patterns.append(re.compile(
                    rf'/{re.escape(alias)}\b', 
                    re.IGNORECASE
                ))
            
            # Padrões baseados no nome
            name_words = command.name.lower().split()
            for word in name_words:
                if len(word) > 3:  # Ignorar palavras muito curtas
                    command_patterns.append(re.compile(
                        rf'\b{re.escape(word)}\b', 
                        re.IGNORECASE
                    ))
            
            patterns[command_id] = command_patterns
        
        return patterns
    
    async def analyze_message(
        self, 
        message: str,
        user_permissions: List[str]
    ) -> CommandAnalysis:
        """
        Analisa uma mensagem para detectar comandos
        
        Args:
            message: Mensagem do usuário
            user_permissions: Lista de permissões do usuário
            
        Returns:
            CommandAnalysis: Resultado da análise
        """
        try:
            # Para comandos que começam com "/", usar mensagem original primeiro
            # Isso garante que o "/" seja preservado para detecção
            if message.strip().startswith('/'):
                # Detectar comandos com mensagem original primeiro
                detected_commands = await self._detect_commands(message, user_permissions)
                # Se não encontrou, tentar com normalizada
                if not detected_commands:
                    processed_message = self._normalize_message(message)
                    detected_commands = await self._detect_commands(processed_message, user_permissions)
                else:
                    processed_message = message
            else:
                # Normalizar mensagem
                processed_message = self._normalize_message(message)
                # Detectar comandos
                detected_commands = await self._detect_commands(processed_message, user_permissions)
            
            if not detected_commands:
                return CommandAnalysis(
                    is_command=False,
                    confidence=0.0,
                    original_message=message,
                    processed_message=processed_message
                )
            
            # Pegar o comando com maior confiança
            best_match = max(detected_commands, key=lambda x: x["confidence"])
            
            # Extrair parâmetros
            parameters = await self._extract_parameters(
                best_match["command"],
                processed_message
            )
            
            # Gerar sugestões
            suggestions = await self._generate_suggestions(processed_message, user_permissions)
            
            return CommandAnalysis(
                is_command=True,
                confidence=best_match["confidence"],
                command_id=best_match["command"].id,
                parameters=parameters,
                original_message=message,
                processed_message=processed_message,
                suggestions=suggestions
            )
            
        except Exception as e:
            logger.error("Erro na análise de comando", error=str(e), message=message)
            return CommandAnalysis(
                is_command=False,
                confidence=0.0,
                original_message=message,
                processed_message=message,
                suggestions=[]
            )
    
    def _normalize_message(self, message: str) -> str:
        """Normaliza a mensagem para análise"""
        # Preservar comandos que começam com "/"
        if message.strip().startswith('/'):
            # Para comandos com "/", preservar o "/" e normalizar o resto
            command_part = message.strip()
            normalized = command_part.lower()
            # Remover caracteres especiais exceto "/" e letras/números
            normalized = re.sub(r'[^\w\s\d\-\./]', ' ', normalized)
        else:
            # Converter para minúsculas
            normalized = message.lower()
            # Remover caracteres especiais desnecessários
            normalized = re.sub(r'[^\w\s\d\-\.]', ' ', normalized)
        
        # Normalizar espaços
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    async def _detect_commands(
        self, 
        message: str, 
        user_permissions: List[str]
    ) -> List[Dict[str, Any]]:
        """Detecta comandos na mensagem"""
        detected = []
        
        for command_id, patterns in self.command_patterns.items():
            command = ALL_COMMANDS[command_id]
            
            # Verificar permissões
            if not await self._check_permissions(command, user_permissions):
                continue
            
            # Calcular confiança para cada padrão
            max_confidence = 0.0
            for pattern in patterns:
                matches = pattern.findall(message)
                if matches:
                    # Calcular confiança baseada no tipo de match
                    pattern_str = pattern.pattern.lower()
                    
                    # Se a mensagem começa com "/", dar mais confiança
                    is_slash_command = message.strip().startswith('/')
                    
                    if pattern_str == command_id.lower() or f'/{command_id.lower()}' in pattern_str:
                        confidence = 0.95 if is_slash_command else 0.9  # Match exato do ID
                    elif any(f'/{alias.lower()}' in pattern_str or alias.lower() in pattern_str for alias in command.aliases):
                        confidence = 0.9 if is_slash_command else 0.8  # Match de alias
                    else:
                        confidence = 0.7 if is_slash_command else 0.6  # Match parcial
                    
                    max_confidence = max(max_confidence, confidence)
            
            # Threshold mínimo: mais baixo para comandos com "/"
            threshold = 0.3 if message.strip().startswith('/') else 0.5
            
            if max_confidence >= threshold:
                detected.append({
                    "command": command,
                    "confidence": max_confidence
                })
        
        return detected
    
    async def _check_permissions(
        self, 
        command: CommandDefinition, 
        user_permissions: List[str]
    ) -> bool:
        """Verifica se o usuário tem permissão para o comando"""
        # Se o comando não requer permissões específicas, permite
        if not command.permissions:
            return True
        
        # Verifica se o usuário tem pelo menos uma das permissões necessárias
        for required_permission in command.permissions:
            if required_permission in user_permissions:
                return True
        return False
    
    async def _extract_parameters(
        self, 
        command: CommandDefinition, 
        message: str
    ) -> Dict[str, Any]:
        """Extrai parâmetros da mensagem baseado na definição do comando"""
        parameters = {}
        
        for param in command.parameters:
            if param.name == "symbol":
                # Extrair símbolo de ativo
                symbol_match = self.symbol_pattern.search(message.upper())
                if symbol_match:
                    parameters["symbol"] = symbol_match.group(1)
            
            elif param.name == "quantity":
                # Extrair quantidade
                number_matches = self.number_pattern.findall(message)
                if number_matches:
                    # Pegar o primeiro número que parece ser uma quantidade
                    for match in number_matches:
                        try:
                            quantity = int(float(match))
                            if 1 <= quantity <= 1000000:  # Range razoável
                                parameters["quantity"] = quantity
                                break
                        except (ValueError, TypeError):
                            continue
            
            elif param.name == "price":
                # Extrair preço
                price_matches = self.number_pattern.findall(message)
                if price_matches:
                    # Pegar o número que parece ser um preço (decimal)
                    for match in price_matches:
                        try:
                            price = float(match)
                            if 0.01 <= price <= 10000:  # Range razoável para preços
                                parameters["price"] = price
                                break
                        except (ValueError, TypeError):
                            continue
            
            elif param.name == "order_id":
                # Extrair ID do pedido (número inteiro)
                number_matches = self.number_pattern.findall(message)
                if number_matches:
                    for match in number_matches:
                        try:
                            order_id = int(float(match))
                            if 1 <= order_id <= 999999:  # Range razoável
                                parameters["order_id"] = order_id
                                break
                        except (ValueError, TypeError):
                            continue
            
            elif param.name == "order_number":
                # Extrair número do pedido (formato ORD-YYYYMMDD-XXXXX)
                order_pattern = re.compile(r'\b(ORD-\d{8}-[A-Z0-9]{5})\b', re.IGNORECASE)
                order_match = order_pattern.search(message.upper())
                if order_match:
                    parameters["order_number"] = order_match.group(1)
            
            elif param.name == "status":
                # Extrair status (pending, confirmed, etc.)
                status_pattern = re.compile(
                    r'\b(pending|confirmed|processing|shipped|delivered|cancelled|rejected)\b',
                    re.IGNORECASE
                )
                status_match = status_pattern.search(message)
                if status_match:
                    parameters["status"] = status_match.group(1).lower()
            
            elif param.name == "customer_id":
                # Extrair ID do cliente (pode ser número ou string)
                customer_pattern = re.compile(r'\bcustomer[_\s]?id[:\s]+(\w+)', re.IGNORECASE)
                customer_match = customer_pattern.search(message)
                if customer_match:
                    parameters["customer_id"] = customer_match.group(1)
                else:
                    # Tentar extrair número que pode ser customer_id
                    number_matches = self.number_pattern.findall(message)
                    if number_matches and "customer" in message.lower():
                        try:
                            customer_id = int(float(number_matches[0]))
                            parameters["customer_id"] = str(customer_id)
                        except (ValueError, TypeError):
                            pass
            
            elif param.name == "limit":
                # Extrair limite (número)
                limit_pattern = re.compile(r'\blimit[:\s]+(\d+)', re.IGNORECASE)
                limit_match = limit_pattern.search(message)
                if limit_match:
                    try:
                        parameters["limit"] = int(limit_match.group(1))
                    except (ValueError, TypeError):
                        pass
            
            elif param.name == "admin_notes":
                # Extrair notas administrativas (texto após "notas:", "motivo:", etc.)
                notes_patterns = [
                    re.compile(r'\b(?:notas?|motivo|observações?)[:\s]+(.+?)(?:\n|$)', re.IGNORECASE),
                    re.compile(r'["\'](.+?)["\']', re.IGNORECASE)
                ]
                for pattern in notes_patterns:
                    notes_match = pattern.search(message)
                    if notes_match:
                        parameters["admin_notes"] = notes_match.group(1).strip()
                        break
        
        return parameters
    
    async def _generate_suggestions(
        self, 
        message: str, 
        user_permissions: List[str]
    ) -> List[str]:
        """Gera sugestões de comandos baseadas na mensagem"""
        suggestions = []
        
        # Se a mensagem é muito curta, sugerir comandos básicos
        if len(message.split()) <= 2:
            for command_id, command in ALL_COMMANDS.items():
                if await self._check_permissions(command, user_permissions):
                    if command.category.value == "view":
                        suggestions.append(f"Tente: {command.examples[0] if command.examples else command.name}")
                        if len(suggestions) >= 3:
                            break
        
        # Se contém palavras relacionadas a trading
        trading_words = ["comprar", "vender", "ordem", "trade", "buy", "sell"]
        if any(word in message for word in trading_words):
            for command_id, command in ALL_COMMANDS.items():
                if (command.category.value == "trade" and 
                    await self._check_permissions(command, user_permissions)):
                    suggestions.append(f"Para trading: {command.examples[0] if command.examples else command.name}")
        
        # Se contém símbolos de ativos
        if self.symbol_pattern.search(message):
            suggestions.append("Você pode usar comandos como 'mostrar posição PETR4' ou 'book PETR4'")
        
        return suggestions[:3]  # Máximo 3 sugestões
    
    async def get_command_examples(
        self, 
        category: Optional[str] = None,
        user_permissions: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Retorna exemplos de comandos"""
        examples = []
        
        for command_id, command in ALL_COMMANDS.items():
            # Filtrar por categoria se especificada
            if category and command.category.value != category:
                continue
            
            # Filtrar por permissões se especificadas
            if user_permissions and not await self._check_permissions(command, user_permissions):
                continue
            
            examples.append({
                "id": command.id,
                "name": command.name,
                "category": command.category.value,
                "examples": command.examples,
                "description": command.description
            })
        
        return examples
    
    async def get_available_commands(
        self, 
        user_permissions: List[str]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Retorna comandos disponíveis organizados por categoria"""
        available = {
            "view": [],
            "create": [],
            "modify": [],
            "delete": [],
            "trade": []
        }
        
        for command_id, command in ALL_COMMANDS.items():
            if await self._check_permissions(command, user_permissions):
                category = command.category.value
                available[category].append({
                    "id": command.id,
                    "name": command.name,
                    "description": command.description,
                    "requires_confirmation": command.requires_confirmation,
                    "risk_level": command.risk_level,
                    "examples": command.examples[:2]
                })
        
        # Remover categorias vazias
        return {k: v for k, v in available.items() if v}
    
    async def validate_command_syntax(
        self, 
        command_id: str, 
        parameters: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """Valida a sintaxe de um comando específico"""
        errors = []
        
        command = ALL_COMMANDS.get(command_id)
        if not command:
            return False, ["Comando não encontrado"]
        
        # Verificar parâmetros obrigatórios
        for param in command.parameters:
            if param.required and param.name not in parameters:
                errors.append(f"Parâmetro obrigatório '{param.name}' não fornecido")
        
        # Verificar tipos dos parâmetros
        for param_name, param_value in parameters.items():
            param_def = next((p for p in command.parameters if p.name == param_name), None)
            if param_def:
                type_valid = await self._validate_parameter_type(param_def, param_value)
                if not type_valid[0]:
                    errors.append(type_valid[1])
        
        return len(errors) == 0, errors
    
    async def _validate_parameter_type(
        self, 
        param_def: 'ParameterDefinition', 
        value: Any
    ) -> Tuple[bool, str]:
        """Valida o tipo de um parâmetro"""
        try:
            if param_def.type == "string":
                if not isinstance(value, str):
                    return False, f"'{param_def.name}' deve ser uma string"
                
                # Validações específicas
                if param_def.name == "symbol":
                    if not re.match(r'^[A-Z]{4}\d$', value.upper()):
                        return False, f"Símbolo deve estar no formato AAAA4 (ex: PETR4)"
            
            elif param_def.type == "integer":
                try:
                    int_value = int(value)
                    if int_value <= 0:
                        return False, f"'{param_def.name}' deve ser um número positivo"
                except (ValueError, TypeError):
                    return False, f"'{param_def.name}' deve ser um número inteiro"
            
            elif param_def.type == "float":
                try:
                    float_value = float(value)
                    if float_value <= 0:
                        return False, f"'{param_def.name}' deve ser um número positivo"
                except (ValueError, TypeError):
                    return False, f"'{param_def.name}' deve ser um número decimal"
            
            return True, ""
            
        except Exception as e:
            return False, f"Erro na validação: {str(e)}"

