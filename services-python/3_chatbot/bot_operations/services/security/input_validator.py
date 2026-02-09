"""
Serviço de validação de entrada para segurança e conformidade
"""

import re
import hashlib
import json
import mimetypes
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import structlog
from pydantic import BaseModel, validator, ValidationError
import phonenumbers
from email_validator import validate_email, EmailNotValidError

logger = structlog.get_logger(__name__)


class ContentType(str, Enum):
    """Tipos de conteúdo suportados"""
    TEXT = "text"
    JSON = "json"
    CSV = "csv"
    PDF = "pdf"
    IMAGE = "image"
    AUDIO = "audio"
    UNSUPPORTED = "unsupported"


class ValidationLevel(str, Enum):
    """Níveis de validação"""
    PASS = "pass"
    WARN = "warn"
    REJECT = "reject"


@dataclass
class ValidationResult:
    """Resultado da validação"""
    is_valid: bool
    level: ValidationLevel
    message: str
    details: Dict[str, Any] = None
    sanitized_content: str = None


class InputValidator:
    """Validador de entrada com segurança e conformidade"""
    
    def __init__(self):
        # Configurações de tamanho
        self.min_chars = 2
        self.max_chars = 8000
        self.max_tokens_estimate = 4000  # Estimativa conservadora
        
        # Tipos MIME permitidos
        self.allowed_mime_types = {
            'text/plain': ContentType.TEXT,
            'text/markdown': ContentType.TEXT,
            'application/json': ContentType.JSON,
            'text/csv': ContentType.CSV,
            'application/pdf': ContentType.PDF,
            'image/png': ContentType.IMAGE,
            'image/jpeg': ContentType.IMAGE,
            'image/webp': ContentType.IMAGE,
            'audio/mpeg': ContentType.AUDIO,
            'audio/wav': ContentType.AUDIO,
        }
        
        # Extensões bloqueadas
        self.blocked_extensions = {
            '.exe', '.bat', '.cmd', '.com', '.scr', '.pif', '.vbs', '.js',
            '.jar', '.apk', '.dmg', '.deb', '.rpm', '.msi', '.app'
        }
        
        # Termos financeiros legítimos (exceções para validação de spam)
        self.financial_terms = [
            # Tickers comuns
            'petr', 'vale', 'itub', 'b3', 'bbas', 'abev', 'wiz', 'mglu',
            'bbdc', 'bidi', 'brkm', 'brfs', 'csan', 'cyre', 'egie', 'elet',
            'embr', 'eqtl', 'flry', 'goll', 'goau', 'hapo', 'hype', 'irbr',
            'jbss', 'klbn', 'lren', 'mult', 'pcar', 'pssa', 'qual', 'radl',
            'rapt', 'rent', 'sapr', 'smle', 'suzb', 'taee', 'tims', 'tots',
            'ugpa', 'usim', 'vivt', 'vvar', 'wege', 'yduq',
            # Termos financeiros
            'preço', 'cotação', 'fechamento', 'abertura', 'máxima', 'mínima',
            'volume', 'ações', 'papéis', 'ticker', 'ativo', 'ativos',
            'ibovespa', 'dólar', 'euro', 'bitcoin', 'criptomoeda',
            'investimento', 'investir', 'carteira', 'portfólio', 'dividendos',
            'lucro', 'prejuízo', 'ganho', 'perda', 'rendimento', 'rentabilidade'
        ]
        
        # Padrão para detectar tickers de ações (4 letras + número opcional)
        self.ticker_pattern = r'\b[A-Z]{4}\d?\b'
        
        # Padrões de spam (mais específicos para evitar falsos positivos)
        self.spam_patterns = [
            r'\b(compre agora|oferta limitada|ganhe dinheiro fácil|riqueza rápida|enriqueça)\b',
            r'\b(bitcoin|criptomoeda|mineração)\b.*\b(ganhe|lucro rápido|dinheiro fácil)\b',
            r'\b(www\.|http://|https://)\b',
            r'\b\d{15,}\b',  # Muitos números (aumentado de 10 para 15 para evitar falsos positivos)
            r'\b[A-Z]{15,}\b',  # Muitas letras maiúsculas (aumentado de 10 para 15)
            r'(.)\1{10,}',  # Caracteres repetidos
        ]
        
        # Padrões de prompt injection
        self.prompt_injection_patterns = [
            r'\b(ignore|forget|disregard)\b.*\b(previous|above|instructions)\b',
            r'\b(system|internal|secret|confidential)\b.*\b(prompt|instruction)\b',
            r'\b(roleplay|pretend|act as)\b',
            r'\b(bypass|override|hack)\b',
            r'\{\{.*\}\}',  # Template markers
            r'<tool>.*</tool>',  # Tool markers
            r'<function>.*</function>',  # Function markers
        ]
        
        # Palavras proibidas (moderação)
        self.forbidden_words = [
            'hack', 'crack', 'exploit', 'bypass', 'override', 'ignore',
            'system', 'internal', 'secret', 'confidential', 'admin'
        ]
        
        # Rate limiting por usuário
        self.rate_limits = {}  # user_id -> [timestamps]
        self.max_requests_per_minute = 30
        
    def validate_message(self, user_id: str, message: str, 
                        content_type: str = "text/plain",
                        metadata: Dict = None) -> ValidationResult:
        """
        Validação completa da mensagem
        """
        try:
            # Gate 0: Validações básicas
            basic_validation = self._validate_basic(message, content_type)
            if not basic_validation.is_valid:
                return basic_validation
            
            # Normalização
            normalized_content = self._normalize_content(message)
            
            # Rate limiting
            rate_validation = self._validate_rate_limit(user_id)
            if not rate_validation.is_valid:
                return rate_validation
            
            # Anti-spam
            spam_validation = self._validate_spam(normalized_content)
            if not spam_validation.is_valid:
                return spam_validation
            
            # Segurança de prompt
            security_validation = self._validate_prompt_security(normalized_content)
            if not security_validation.is_valid:
                return security_validation
            
            # Moderação de conteúdo
            moderation_validation = self._validate_content_moderation(normalized_content)
            if not moderation_validation.is_valid:
                return moderation_validation
            
            # Sanitização de PII
            sanitized_content = self._sanitize_pii(normalized_content)
            
            # Validação de tamanho/tokens
            size_validation = self._validate_size(sanitized_content)
            if not size_validation.is_valid:
                return size_validation
            
            # Validação de formato específico
            format_validation = self._validate_format(sanitized_content, content_type)
            if not format_validation.is_valid:
                return format_validation
            
            return ValidationResult(
                is_valid=True,
                level=ValidationLevel.PASS,
                message="Mensagem validada com sucesso",
                details={
                    "original_length": len(message),
                    "sanitized_length": len(sanitized_content),
                    "content_type": content_type,
                    "validation_steps": "all_passed"
                },
                sanitized_content=sanitized_content
            )
            
        except Exception as e:
            logger.error(f"Erro na validação: {e}")
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.REJECT,
                message="Erro interno na validação",
                details={"error": str(e)}
            )
    
    def _validate_basic(self, message: str, content_type: str) -> ValidationResult:
        """Validações básicas (Gate 0)"""
        # Mensagem vazia
        if not message or not message.strip():
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.REJECT,
                message="Mensagem vazia ou apenas espaços",
                details={"error_code": "EMPTY_MESSAGE"}
            )
        
        # Comprimento mínimo
        if len(message.strip()) < self.min_chars:
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.REJECT,
                message=f"Mensagem muito curta (mínimo {self.min_chars} caracteres)",
                details={"error_code": "TOO_SHORT", "min_chars": self.min_chars}
            )
        
        # Comprimento máximo
        if len(message) > self.max_chars:
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.REJECT,
                message=f"Mensagem muito longa (máximo {self.max_chars} caracteres)",
                details={"error_code": "TOO_LONG", "max_chars": self.max_chars}
            )
        
        # Tipo MIME suportado
        if content_type not in self.allowed_mime_types:
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.REJECT,
                message=f"Tipo de conteúdo não suportado: {content_type}",
                details={"error_code": "UNSUPPORTED_MIME", "content_type": content_type}
            )
        
        return ValidationResult(
            is_valid=True,
            level=ValidationLevel.PASS,
            message="Validações básicas aprovadas"
        )
    
    def _normalize_content(self, content: str) -> str:
        """Normalização de conteúdo"""
        # Trim e normalização de quebras de linha
        normalized = content.strip()
        
        # Remover bytes não imprimíveis
        normalized = ''.join(char for char in normalized if char.isprintable() or char in '\n\r\t')
        
        # Remover ZWJ/ZWSP (Zero Width Joiner/Space)
        normalized = re.sub(r'[\u200D\u200B\u200C\uFEFF]', '', normalized)
        
        # Canonizar whitespace (reduzir múltiplos espaços)
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Normalizar quebras de linha
        normalized = re.sub(r'\r\n|\r', '\n', normalized)
        
        return normalized
    
    def _validate_rate_limit(self, user_id: str) -> ValidationResult:
        """Validação de rate limiting"""
        now = datetime.utcnow()
        
        if user_id not in self.rate_limits:
            self.rate_limits[user_id] = []
        
        # Limpar timestamps antigos (último minuto)
        cutoff = now - timedelta(minutes=1)
        self.rate_limits[user_id] = [
            ts for ts in self.rate_limits[user_id] 
            if ts > cutoff
        ]
        
        # Verificar limite
        if len(self.rate_limits[user_id]) >= self.max_requests_per_minute:
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.REJECT,
                message="Muitas requisições. Tente novamente em alguns segundos.",
                details={
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "requests_per_minute": self.max_requests_per_minute
                }
            )
        
        # Adicionar timestamp atual
        self.rate_limits[user_id].append(now)
        
        return ValidationResult(
            is_valid=True,
            level=ValidationLevel.PASS,
            message="Rate limit OK"
        )
    
    def _validate_spam(self, content: str) -> ValidationResult:
        """Validação anti-spam"""
        content_lower = content.lower()
        
        # Verificar se contém termos financeiros legítimos
        has_financial_term = any(term in content_lower for term in self.financial_terms)
        
        # Verificar se contém ticker de ação (padrão: 4 letras maiúsculas + número opcional)
        has_ticker = bool(re.search(self.ticker_pattern, content))
        
        # Considerar como termo financeiro se tiver ticker ou termos financeiros
        has_financial_term = has_financial_term or has_ticker
        
        # Padrões sempre suspeitos (mesmo com termos financeiros)
        always_suspicious_patterns = [
            r'\b(compre agora|oferta limitada|ganhe dinheiro fácil|riqueza rápida|enriqueça)\b',
            r'\b(www\.|http://|https://)\b',
            r'(.)\1{10,}',  # Caracteres repetidos
        ]
        
        # Verificar padrões de spam (com exceção para termos financeiros)
        for pattern in self.spam_patterns:
            match = re.search(pattern, content_lower, re.IGNORECASE)
            if match:
                # Se contém termos financeiros legítimos, ser mais permissivo
                if has_financial_term:
                    # Para termos financeiros, apenas rejeitar padrões muito suspeitos
                    is_always_suspicious = any(
                        re.search(susp_pattern, content_lower, re.IGNORECASE) 
                        for susp_pattern in always_suspicious_patterns
                    )
                    
                    if is_always_suspicious:
                        return ValidationResult(
                            is_valid=False,
                            level=ValidationLevel.REJECT,
                            message="Conteúdo detectado como spam",
                            details={
                                "error_code": "SPAM_DETECTED",
                                "pattern": pattern
                            }
                        )
                    # Para outros padrões com termos financeiros, apenas logar warning mas permitir
                    logger.warning(
                        "Padrão de spam detectado mas permitido devido a termos financeiros",
                        pattern=pattern,
                        content_preview=content[:50]
                    )
                    # Continua para o próximo padrão ao invés de rejeitar
                    continue
                else:
                    # Sem termos financeiros, aplicar validação normal
                    return ValidationResult(
                        is_valid=False,
                        level=ValidationLevel.REJECT,
                        message="Conteúdo detectado como spam",
                        details={
                            "error_code": "SPAM_DETECTED",
                            "pattern": pattern
                        }
                    )
        
        # Verificar repetição excessiva
        if self._has_excessive_repetition(content):
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.REJECT,
                message="Conteúdo com repetição excessiva",
                details={"error_code": "EXCESSIVE_REPETITION"}
            )
        
        return ValidationResult(
            is_valid=True,
            level=ValidationLevel.PASS,
            message="Anti-spam OK"
        )
    
    def _validate_prompt_security(self, content: str) -> ValidationResult:
        """Validação de segurança de prompt"""
        content_lower = content.lower()
        
        # Verificar padrões de prompt injection
        for pattern in self.prompt_injection_patterns:
            if re.search(pattern, content_lower, re.IGNORECASE):
                return ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.REJECT,
                    message="Tentativa de injeção de prompt detectada",
                    details={
                        "error_code": "PROMPT_INJECTION",
                        "pattern": pattern
                    }
                )
        
        # Verificar palavras proibidas
        for word in self.forbidden_words:
            if word in content_lower:
                return ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.REJECT,
                    message="Conteúdo contém palavras proibidas",
                    details={
                        "error_code": "FORBIDDEN_WORDS",
                        "word": word
                    }
                )
        
        return ValidationResult(
            is_valid=True,
            level=ValidationLevel.PASS,
            message="Segurança de prompt OK"
        )
    
    def _validate_content_moderation(self, content: str) -> ValidationResult:
        """Moderação de conteúdo"""
        # Implementar aqui lógica de moderação mais sofisticada
        # Por enquanto, verificação básica
        
        # Palavras de ódio (exemplo básico)
        hate_words = ['odio', 'morte', 'matar', 'destruir']
        content_lower = content.lower()
        
        for word in hate_words:
            if word in content_lower:
                return ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.REJECT,
                    message="Conteúdo não atende às políticas de uso",
                    details={
                        "error_code": "CONTENT_MODERATION",
                        "reason": "hate_speech"
                    }
                )
        
        return ValidationResult(
            is_valid=True,
            level=ValidationLevel.PASS,
            message="Moderação OK"
        )
    
    def _sanitize_pii(self, content: str) -> str:
        """Sanitização de PII"""
        # Mascarar CPF
        content = re.sub(r'\b\d{3}\.\d{3}\.\d{3}-\d{2}\b', '***.***.***-**', content)
        content = re.sub(r'\b\d{11}\b', '***.***.***-**', content)
        
        # Mascarar CNPJ
        content = re.sub(r'\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b', '**.***.***/****-**', content)
        content = re.sub(r'\b\d{14}\b', '**.***.***/****-**', content)
        
        # Mascarar telefone
        content = re.sub(r'\b\+?55\s?\d{2}\s?\d{4,5}\s?\d{4}\b', '***-****-****', content)
        
        # Mascarar email (parcialmente)
        content = re.sub(r'\b([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b', 
                        r'***@\2', content)
        
        return content
    
    def _validate_size(self, content: str) -> ValidationResult:
        """Validação de tamanho e tokens"""
        # Estimativa de tokens (aproximada: 1 token ≈ 4 caracteres)
        estimated_tokens = len(content) // 4
        
        if estimated_tokens > self.max_tokens_estimate:
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.REJECT,
                message=f"Conteúdo muito longo (estimativa: {estimated_tokens} tokens)",
                details={
                    "error_code": "TOKEN_LIMIT_EXCEEDED",
                    "estimated_tokens": estimated_tokens,
                    "max_tokens": self.max_tokens_estimate
                }
            )
        
        return ValidationResult(
            is_valid=True,
            level=ValidationLevel.PASS,
            message="Tamanho OK"
        )
    
    def _validate_format(self, content: str, content_type: str) -> ValidationResult:
        """Validação de formato específico"""
        if content_type == "application/json":
            try:
                json.loads(content)
            except json.JSONDecodeError as e:
                return ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.REJECT,
                    message="JSON inválido",
                    details={
                        "error_code": "INVALID_JSON",
                        "json_error": str(e)
                    }
                )
        
        elif content_type == "text/csv":
            # Validação básica de CSV
            lines = content.strip().split('\n')
            if len(lines) < 2:  # Pelo menos cabeçalho + uma linha
                return ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.REJECT,
                    message="CSV deve ter pelo menos cabeçalho e uma linha de dados",
                    details={"error_code": "INVALID_CSV"}
                )
        
        return ValidationResult(
            is_valid=True,
            level=ValidationLevel.PASS,
            message="Formato OK"
        )
    
    def _has_excessive_repetition(self, content: str) -> bool:
        """Verifica repetição excessiva"""
        # Ignorar mensagens muito curtas (menos de 5 caracteres)
        # Mensagens curtas como "oi", "ok", "sim" são válidas
        if len(content.strip()) < 5:
            return False
        
        # Verificar caracteres repetidos consecutivos (mais de 5 repetições)
        max_consecutive = 1
        current_consecutive = 1
        for i in range(1, len(content)):
            if content[i] == content[i-1] and content[i].isalnum():
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 1
        
        if max_consecutive > 5:
            return True
        
        # Verificar se algum caractere representa mais de 50% do conteúdo
        # Apenas para mensagens com mais de 10 caracteres
        if len(content) > 10:
            for char in set(content):
                if content.count(char) > len(content) * 0.5:  # Mais de 50% do conteúdo
                    return True
        
        # Verificar palavras repetidas (apenas para mensagens longas)
        words = content.split()
        if len(words) > 10:
            word_counts = {}
            for word in words:
                word_counts[word] = word_counts.get(word, 0) + 1
                if word_counts[word] > len(words) * 0.3:  # Mais de 30% das palavras
                    return True
        
        return False
    
    def validate_file_attachment(self, filename: str, mime_type: str, 
                               file_size: int) -> ValidationResult:
        """Validação de anexos"""
        # Tamanho máximo (10MB)
        max_size = 10 * 1024 * 1024
        if file_size > max_size:
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.REJECT,
                message="Arquivo muito grande (máximo 10MB)",
                details={
                    "error_code": "FILE_TOO_LARGE",
                    "file_size": file_size,
                    "max_size": max_size
                }
            )
        
        # Extensão bloqueada
        file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
        if f'.{file_ext}' in self.blocked_extensions:
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.REJECT,
                message="Tipo de arquivo não permitido",
                details={
                    "error_code": "BLOCKED_EXTENSION",
                    "extension": file_ext
                }
            )
        
        # MIME type não suportado
        if mime_type not in self.allowed_mime_types:
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.REJECT,
                message=f"Tipo de arquivo não suportado: {mime_type}",
                details={
                    "error_code": "UNSUPPORTED_MIME",
                    "mime_type": mime_type
                }
            )
        
        return ValidationResult(
            is_valid=True,
            level=ValidationLevel.PASS,
            message="Anexo validado com sucesso"
        )
    
    def generate_content_hash(self, content: str, user_id: str) -> str:
        """Gera hash do conteúdo para deduplicação"""
        content_with_user = f"{user_id}:{content}"
        return hashlib.md5(content_with_user.encode('utf-8')).hexdigest()


# Instância global do validador
input_validator = InputValidator()


