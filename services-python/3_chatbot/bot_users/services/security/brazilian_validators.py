"""
Validadores específicos para o Brasil
"""

import re
from typing import Tuple, Optional
from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)


class BrazilianValidators:
    """Validadores específicos para dados brasileiros"""
    
    @staticmethod
    def validate_cpf(cpf: str) -> Tuple[bool, Optional[str]]:
        """
        Valida CPF brasileiro
        Retorna: (é_válido, cpf_formatado)
        """
        # Remove caracteres não numéricos
        cpf_clean = re.sub(r'[^\d]', '', cpf)
        
        # Verifica se tem 11 dígitos
        if len(cpf_clean) != 11:
            return False, None
        
        # Verifica se todos os dígitos são iguais
        if cpf_clean == cpf_clean[0] * 11:
            return False, None
        
        # Calcula primeiro dígito verificador
        soma = 0
        for i in range(9):
            soma += int(cpf_clean[i]) * (10 - i)
        
        resto = soma % 11
        if resto < 2:
            digito1 = 0
        else:
            digito1 = 11 - resto
        
        # Calcula segundo dígito verificador
        soma = 0
        for i in range(10):
            soma += int(cpf_clean[i]) * (11 - i)
        
        resto = soma % 11
        if resto < 2:
            digito2 = 0
        else:
            digito2 = 11 - resto
        
        # Verifica se os dígitos calculados são iguais aos do CPF
        if int(cpf_clean[9]) == digito1 and int(cpf_clean[10]) == digito2:
            # Formata CPF
            cpf_formatado = f"{cpf_clean[:3]}.{cpf_clean[3:6]}.{cpf_clean[6:9]}-{cpf_clean[9:]}"
            return True, cpf_formatado
        
        return False, None
    
    @staticmethod
    def validate_cnpj(cnpj: str) -> Tuple[bool, Optional[str]]:
        """
        Valida CNPJ brasileiro
        Retorna: (é_válido, cnpj_formatado)
        """
        # Remove caracteres não numéricos
        cnpj_clean = re.sub(r'[^\d]', '', cnpj)
        
        # Verifica se tem 14 dígitos
        if len(cnpj_clean) != 14:
            return False, None
        
        # Verifica se todos os dígitos são iguais
        if cnpj_clean == cnpj_clean[0] * 14:
            return False, None
        
        # Calcula primeiro dígito verificador
        multiplicadores1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = 0
        for i in range(12):
            soma += int(cnpj_clean[i]) * multiplicadores1[i]
        
        resto = soma % 11
        if resto < 2:
            digito1 = 0
        else:
            digito1 = 11 - resto
        
        # Calcula segundo dígito verificador
        multiplicadores2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = 0
        for i in range(13):
            soma += int(cnpj_clean[i]) * multiplicadores2[i]
        
        resto = soma % 11
        if resto < 2:
            digito2 = 0
        else:
            digito2 = 11 - resto
        
        # Verifica se os dígitos calculados são iguais aos do CNPJ
        if int(cnpj_clean[12]) == digito1 and int(cnpj_clean[13]) == digito2:
            # Formata CNPJ
            cnpj_formatado = f"{cnpj_clean[:2]}.{cnpj_clean[2:5]}.{cnpj_clean[5:8]}/{cnpj_clean[8:12]}-{cnpj_clean[12:]}"
            return True, cnpj_formatado
        
        return False, None
    
    @staticmethod
    def validate_brazilian_phone(phone: str) -> Tuple[bool, Optional[str]]:
        """
        Valida telefone brasileiro
        Retorna: (é_válido, telefone_formatado)
        """
        # Remove caracteres não numéricos
        phone_clean = re.sub(r'[^\d]', '', phone)
        
        # Remove código do país se presente
        if phone_clean.startswith('55'):
            phone_clean = phone_clean[2:]
        
        # Verifica se tem 10 ou 11 dígitos (com DDD)
        if len(phone_clean) not in [10, 11]:
            return False, None
        
        # Verifica se DDD é válido (11-99)
        ddd = int(phone_clean[:2])
        if ddd < 11 or ddd > 99:
            return False, None
        
        # Formata telefone
        if len(phone_clean) == 10:  # Telefone fixo
            phone_formatado = f"({phone_clean[:2]}) {phone_clean[2:6]}-{phone_clean[6:]}"
        else:  # Celular
            phone_formatado = f"({phone_clean[:2]}) {phone_clean[2:7]}-{phone_clean[7:]}"
        
        return True, phone_formatado
    
    @staticmethod
    def validate_brazilian_date(date_str: str) -> Tuple[bool, Optional[str]]:
        """
        Valida e normaliza data brasileira
        Retorna: (é_válido, data_iso)
        """
        # Padrões de data brasileira
        patterns = [
            r'(\d{1,2})/(\d{1,2})/(\d{4})',  # DD/MM/YYYY
            r'(\d{1,2})-(\d{1,2})-(\d{4})',  # DD-MM-YYYY
            r'(\d{4})-(\d{1,2})-(\d{1,2})',  # YYYY-MM-DD
        ]
        
        for pattern in patterns:
            match = re.match(pattern, date_str)
            if match:
                groups = match.groups()
                
                if len(groups[0]) == 4:  # YYYY-MM-DD
                    year, month, day = groups
                else:  # DD/MM/YYYY ou DD-MM-YYYY
                    day, month, year = groups
                
                try:
                    # Converte para datetime
                    date_obj = datetime(int(year), int(month), int(day))
                    
                    # Verifica se a data é razoável (não muito no passado ou futuro)
                    now = datetime.now()
                    if date_obj.year < 1900 or date_obj.year > now.year + 10:
                        return False, None
                    
                    # Retorna em formato ISO
                    return True, date_obj.strftime('%Y-%m-%d')
                    
                except ValueError:
                    continue
        
        return False, None
    
    @staticmethod
    def validate_brazilian_cep(cep: str) -> Tuple[bool, Optional[str]]:
        """
        Valida CEP brasileiro
        Retorna: (é_válido, cep_formatado)
        """
        # Remove caracteres não numéricos
        cep_clean = re.sub(r'[^\d]', '', cep)
        
        # Verifica se tem 8 dígitos
        if len(cep_clean) != 8:
            return False, None
        
        # Formata CEP
        cep_formatado = f"{cep_clean[:5]}-{cep_clean[5:]}"
        
        return True, cep_formatado
    
    @staticmethod
    def mask_cpf(cpf: str) -> str:
        """Mascara CPF para exibição"""
        cpf_clean = re.sub(r'[^\d]', '', cpf)
        if len(cpf_clean) == 11:
            return f"***.***.***-{cpf_clean[-2:]}"
        return "***.***.***-**"
    
    @staticmethod
    def mask_cnpj(cnpj: str) -> str:
        """Mascara CNPJ para exibição"""
        cnpj_clean = re.sub(r'[^\d]', '', cnpj)
        if len(cnpj_clean) == 14:
            return f"**.***.***/****-{cnpj_clean[-2:]}"
        return "**.***.***/****-**"
    
    @staticmethod
    def mask_phone(phone: str) -> str:
        """Mascara telefone para exibição"""
        phone_clean = re.sub(r'[^\d]', '', phone)
        if len(phone_clean) >= 10:
            return f"***-****-{phone_clean[-4:]}"
        return "***-****-****"
    
    @staticmethod
    def extract_brazilian_documents(text: str) -> dict:
        """
        Extrai documentos brasileiros do texto
        Retorna: {
            'cpfs': [{'original': '...', 'valid': True, 'formatted': '...'}],
            'cnpjs': [...],
            'phones': [...],
            'dates': [...],
            'ceps': [...]
        }
        """
        result = {
            'cpfs': [],
            'cnpjs': [],
            'phones': [],
            'dates': [],
            'ceps': []
        }
        
        # Extrair CPFs
        cpf_pattern = r'\b\d{3}[.\s]?\d{3}[.\s]?\d{3}[-\s]?\d{2}\b'
        for match in re.finditer(cpf_pattern, text):
            cpf = match.group()
            is_valid, formatted = BrazilianValidators.validate_cpf(cpf)
            result['cpfs'].append({
                'original': cpf,
                'valid': is_valid,
                'formatted': formatted
            })
        
        # Extrair CNPJs
        cnpj_pattern = r'\b\d{2}[.\s]?\d{3}[.\s]?\d{3}[/\s]?\d{4}[-\s]?\d{2}\b'
        for match in re.finditer(cnpj_pattern, text):
            cnpj = match.group()
            is_valid, formatted = BrazilianValidators.validate_cnpj(cnpj)
            result['cnpjs'].append({
                'original': cnpj,
                'valid': is_valid,
                'formatted': formatted
            })
        
        # Extrair telefones
        phone_pattern = r'\b\+?55\s?\d{2}\s?\d{4,5}\s?\d{4}\b'
        for match in re.finditer(phone_pattern, text):
            phone = match.group()
            is_valid, formatted = BrazilianValidators.validate_brazilian_phone(phone)
            result['phones'].append({
                'original': phone,
                'valid': is_valid,
                'formatted': formatted
            })
        
        # Extrair CEPs
        cep_pattern = r'\b\d{5}[-\s]?\d{3}\b'
        for match in re.finditer(cep_pattern, text):
            cep = match.group()
            is_valid, formatted = BrazilianValidators.validate_brazilian_cep(cep)
            result['ceps'].append({
                'original': cep,
                'valid': is_valid,
                'formatted': formatted
            })
        
        # Extrair datas (padrão brasileiro)
        date_pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b'
        for match in re.finditer(date_pattern, text):
            date_str = match.group()
            is_valid, formatted = BrazilianValidators.validate_brazilian_date(date_str)
            result['dates'].append({
                'original': date_str,
                'valid': is_valid,
                'formatted': formatted
            })
        
        return result


# Instância global
brazilian_validators = BrazilianValidators()


