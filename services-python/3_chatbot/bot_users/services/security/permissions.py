"""
Sistema de permissões para comandos
"""

from typing import Dict, List, Set, Optional, Tuple
from enum import Enum
import structlog

logger = structlog.get_logger(__name__)


class PermissionLevel(str, Enum):
    """Níveis de permissão"""
    BASIC = "basic"           # Usuário básico
    PREMIUM = "premium"       # Usuário premium
    TRADER = "trader"         # Trader ativo
    PROFESSIONAL = "professional"  # Profissional
    ADMIN = "admin"           # Administrador


class PermissionCategory(str, Enum):
    """Categorias de permissões"""
    VIEW = "view"             # Visualização
    CREATE = "create"         # Criação
    MODIFY = "modify"         # Modificação
    DELETE = "delete"         # Remoção
    TRADE = "trade"           # Trading
    ADMIN = "admin"           # Administração


class PermissionManager:
    """Gerenciador de permissões para comandos"""
    
    def __init__(self):
        self.permission_definitions = self._build_permission_definitions()
        self.level_permissions = self._build_level_permissions()
    
    def _build_permission_definitions(self) -> Dict[str, Dict[str, any]]:
        """Constrói as definições de permissões"""
        return {
            # Permissões de visualização
            "view_positions": {
                "name": "Visualizar Posições",
                "description": "Permite visualizar posições de ativos",
                "category": PermissionCategory.VIEW,
                "level": PermissionLevel.BASIC,
                "risk": "baixo"
            },
            "view_book": {
                "name": "Visualizar Book de Ofertas",
                "description": "Permite visualizar book de ofertas",
                "category": PermissionCategory.VIEW,
                "level": PermissionLevel.BASIC,
                "risk": "baixo"
            },
            "view_watchlist": {
                "name": "Visualizar Watchlist",
                "description": "Permite visualizar lista de observação",
                "category": PermissionCategory.VIEW,
                "level": PermissionLevel.BASIC,
                "risk": "baixo"
            },
            
            # Permissões de criação
            "create_multibox": {
                "name": "Criar Box de Cotação",
                "description": "Permite criar boxes de cotação",
                "category": PermissionCategory.CREATE,
                "level": PermissionLevel.BASIC,
                "risk": "médio"
            },
            "modify_watchlist": {
                "name": "Modificar Watchlist",
                "description": "Permite adicionar/remover ativos do watchlist",
                "category": PermissionCategory.CREATE,
                "level": PermissionLevel.BASIC,
                "risk": "médio"
            },
            "create_analysis": {
                "name": "Criar Análise",
                "description": "Permite criar abas de análise técnica",
                "category": PermissionCategory.CREATE,
                "level": PermissionLevel.PREMIUM,
                "risk": "médio"
            },
            
            # Permissões de trading
            "prepare_orders": {
                "name": "Preparar Ordens",
                "description": "Permite preparar ordens de compra/venda",
                "category": PermissionCategory.TRADE,
                "level": PermissionLevel.TRADER,
                "risk": "crítico"
            },
            "execute_orders": {
                "name": "Executar Ordens",
                "description": "Permite executar ordens diretamente",
                "category": PermissionCategory.TRADE,
                "level": PermissionLevel.PROFESSIONAL,
                "risk": "crítico"
            },
            
            # Permissões administrativas
            "admin_users": {
                "name": "Administrar Usuários",
                "description": "Permite gerenciar outros usuários",
                "category": PermissionCategory.ADMIN,
                "level": PermissionLevel.ADMIN,
                "risk": "alto"
            },
            "admin_system": {
                "name": "Administrar Sistema",
                "description": "Permite configurações do sistema",
                "category": PermissionCategory.ADMIN,
                "level": PermissionLevel.ADMIN,
                "risk": "alto"
            }
        }
    
    def _build_level_permissions(self) -> Dict[PermissionLevel, Set[str]]:
        """Constrói as permissões por nível"""
        return {
            PermissionLevel.BASIC: {
                "view_positions",
                "view_book", 
                "view_watchlist",
                "create_multibox",
                "modify_watchlist"
            },
            PermissionLevel.PREMIUM: {
                "view_positions",
                "view_book",
                "view_watchlist", 
                "create_multibox",
                "modify_watchlist",
                "create_analysis"
            },
            PermissionLevel.TRADER: {
                "view_positions",
                "view_book",
                "view_watchlist",
                "create_multibox", 
                "modify_watchlist",
                "create_analysis",
                "prepare_orders"
            },
            PermissionLevel.PROFESSIONAL: {
                "view_positions",
                "view_book",
                "view_watchlist",
                "create_multibox",
                "modify_watchlist", 
                "create_analysis",
                "prepare_orders",
                "execute_orders"
            },
            PermissionLevel.ADMIN: {
                "view_positions",
                "view_book",
                "view_watchlist",
                "create_multibox",
                "modify_watchlist",
                "create_analysis", 
                "prepare_orders",
                "execute_orders",
                "admin_users",
                "admin_system"
            }
        }
    
    def get_user_permissions(self, user_level: PermissionLevel) -> List[str]:
        """Retorna as permissões de um usuário baseado no nível"""
        try:
            permissions = self.level_permissions.get(user_level, set())
            return list(permissions)
        except Exception as e:
            logger.error("Erro ao obter permissões do usuário", error=str(e), level=user_level)
            return []
    
    def has_permission(self, user_permissions: List[str], required_permission: str) -> bool:
        """Verifica se o usuário tem uma permissão específica"""
        try:
            return required_permission in user_permissions
        except Exception as e:
            logger.error("Erro ao verificar permissão", error=str(e))
            return False
    
    def has_any_permission(self, user_permissions: List[str], required_permissions: List[str]) -> bool:
        """Verifica se o usuário tem pelo menos uma das permissões requeridas"""
        try:
            return any(perm in user_permissions for perm in required_permissions)
        except Exception as e:
            logger.error("Erro ao verificar permissões", error=str(e))
            return False
    
    def has_all_permissions(self, user_permissions: List[str], required_permissions: List[str]) -> bool:
        """Verifica se o usuário tem todas as permissões requeridas"""
        try:
            return all(perm in user_permissions for perm in required_permissions)
        except Exception as e:
            logger.error("Erro ao verificar permissões", error=str(e))
            return False
    
    def get_permission_info(self, permission_id: str) -> Optional[Dict[str, any]]:
        """Retorna informações sobre uma permissão específica"""
        try:
            return self.permission_definitions.get(permission_id)
        except Exception as e:
            logger.error("Erro ao obter informações da permissão", error=str(e), permission_id=permission_id)
            return None
    
    def get_permissions_by_category(self, category: PermissionCategory) -> List[Dict[str, any]]:
        """Retorna todas as permissões de uma categoria"""
        try:
            permissions = []
            for perm_id, perm_info in self.permission_definitions.items():
                if perm_info["category"] == category:
                    permissions.append({
                        "id": perm_id,
                        **perm_info
                    })
            return permissions
        except Exception as e:
            logger.error("Erro ao obter permissões por categoria", error=str(e), category=category)
            return []
    
    def get_permissions_by_level(self, level: PermissionLevel) -> List[Dict[str, any]]:
        """Retorna todas as permissões de um nível"""
        try:
            permissions = []
            perm_ids = self.level_permissions.get(level, set())
            
            for perm_id in perm_ids:
                perm_info = self.permission_definitions.get(perm_id)
                if perm_info:
                    permissions.append({
                        "id": perm_id,
                        **perm_info
                    })
            
            return permissions
        except Exception as e:
            logger.error("Erro ao obter permissões por nível", error=str(e), level=level)
            return []
    
    def validate_permission_upgrade(
        self, 
        current_level: PermissionLevel, 
        target_level: PermissionLevel
    ) -> Tuple[bool, str]:
        """Valida se um upgrade de permissão é permitido"""
        try:
            # Verificar se o target_level é superior ao current_level
            level_hierarchy = [
                PermissionLevel.BASIC,
                PermissionLevel.PREMIUM, 
                PermissionLevel.TRADER,
                PermissionLevel.PROFESSIONAL,
                PermissionLevel.ADMIN
            ]
            
            current_index = level_hierarchy.index(current_level)
            target_index = level_hierarchy.index(target_level)
            
            if target_index <= current_index:
                return False, "Nível de permissão deve ser superior ao atual"
            
            return True, "Upgrade de permissão válido"
            
        except Exception as e:
            logger.error("Erro na validação de upgrade", error=str(e))
            return False, f"Erro na validação: {str(e)}"
    
    def get_missing_permissions(
        self, 
        user_permissions: List[str], 
        required_permissions: List[str]
    ) -> List[str]:
        """Retorna as permissões que o usuário não tem"""
        try:
            return [perm for perm in required_permissions if perm not in user_permissions]
        except Exception as e:
            logger.error("Erro ao obter permissões faltantes", error=str(e))
            return []
    
    def get_permission_summary(self, user_permissions: List[str]) -> Dict[str, any]:
        """Retorna um resumo das permissões do usuário"""
        try:
            summary = {
                "total_permissions": len(user_permissions),
                "categories": {},
                "risk_levels": {},
                "missing_critical": []
            }
            
            # Contar por categoria
            for perm_id in user_permissions:
                perm_info = self.permission_definitions.get(perm_id)
                if perm_info:
                    category = perm_info["category"].value
                    risk = perm_info["risk"]
                    
                    if category not in summary["categories"]:
                        summary["categories"][category] = 0
                    summary["categories"][category] += 1
                    
                    if risk not in summary["risk_levels"]:
                        summary["risk_levels"][risk] = 0
                    summary["risk_levels"][risk] += 1
            
            # Verificar permissões críticas faltantes
            critical_permissions = [
                "view_positions",  # Básico para qualquer usuário
                "view_watchlist"   # Básico para qualquer usuário
            ]
            
            summary["missing_critical"] = self.get_missing_permissions(
                user_permissions, critical_permissions
            )
            
            return summary
            
        except Exception as e:
            logger.error("Erro ao gerar resumo de permissões", error=str(e))
            return {}
    
    def suggest_permission_upgrade(
        self, 
        user_permissions: List[str], 
        target_command: str
    ) -> Optional[Dict[str, any]]:
        """Sugere upgrade de permissão para executar um comando"""
        try:
            # Mapear comando para permissões necessárias
            command_permissions = {
                "show_position": ["view_positions"],
                "show_book_offers": ["view_book"],
                "show_watchlist": ["view_watchlist"],
                "add_multibox": ["create_multibox"],
                "add_watchlist": ["modify_watchlist"],
                "create_analysis_tab": ["create_analysis"],
                "prepare_buy_order": ["prepare_orders"],
                "prepare_sell_order": ["prepare_orders"]
            }
            
            required_permissions = command_permissions.get(target_command, [])
            if not required_permissions:
                return None
            
            missing_permissions = self.get_missing_permissions(user_permissions, required_permissions)
            if not missing_permissions:
                return None
            
            # Encontrar o nível mínimo necessário
            for level in [PermissionLevel.BASIC, PermissionLevel.PREMIUM, PermissionLevel.TRADER, PermissionLevel.PROFESSIONAL]:
                level_permissions = self.get_user_permissions(level)
                if all(perm in level_permissions for perm in missing_permissions):
                    return {
                        "current_permissions": user_permissions,
                        "missing_permissions": missing_permissions,
                        "suggested_level": level.value,
                        "upgrade_reason": f"Necessário para executar '{target_command}'"
                    }
            
            return None
            
        except Exception as e:
            logger.error("Erro ao sugerir upgrade", error=str(e))
            return None


# Instância global do gerenciador de permissões
permission_manager = PermissionManager()

