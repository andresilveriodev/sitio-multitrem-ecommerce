#!/usr/bin/env python3
"""
Script de testes de persistência para o Auth Service
Testa todas as funcionalidades: usuários, ACL, perfil, configurações
"""

import asyncio
import json
import structlog
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, date

from config import settings
from db_session import get_db_session
from models.acl import User, Profile, Permission, UserProfile, ProfilePermission
from models.user_profile import UserProfileData, UserPreferences, UserSettings, UserActivity
from services.auth_service import AuthService
from services.acl_service import ACLService
from services.user_profile_service import UserProfileService
from models.auth import UserCreate, UserUpdate

logger = structlog.get_logger()

# Exemplos de JSON para persistência
JSON_EXAMPLES = {
    "user_create": {
        "username": "teste_usuario",
        "email": "teste@exemplo.com",
        "first_name": "João",
        "last_name": "Silva",
        "password": "senha123"
    },
    
    "user_update": {
        "first_name": "João Pedro",
        "last_name": "Silva Santos",
        "is_active": True
    },
    
    "profile_data_create": {
        "full_name": "João Pedro Silva Santos",
        "date_of_birth": "1990-05-15",
        "cpf": "123.456.789-01",
        "phone": "+55-11-99999-9999",
        "address": "Rua das Flores, 123",
        "city": "São Paulo",
        "state": "SP",
        "country": "Brasil",
        "postal_code": "01234-567",
        "bio": "Desenvolvedor apaixonado por tecnologia"
    },
    
    "profile_data_update": {
        "full_name": "João Pedro Silva Santos",
        "phone": "+55-11-88888-8888",
        "address": "Av. Paulista, 1000",
        "city": "São Paulo",
        "state": "SP"
    },
    
    "preferences_create": {
        "language": "pt-BR",
        "timezone": "America/Sao_Paulo",
        "theme": "dark",
        "notifications_enabled": True,
        "email_notifications": True,
        "push_notifications": False,
        "sms_notifications": False,
        "sound_enabled": True,
        "auto_refresh": True,
        "refresh_interval": 10000
    },
    
    "preferences_update": {
        "theme": "light",
        "notifications_enabled": False,
        "refresh_interval": 5000
    },
    
    "settings_create": {
        "two_factor_enabled": True,
        "privacy_level": "private",
        "data_sharing": False,
        "marketing_emails": False,
        "newsletter_subscription": True
    },
    
    "settings_update": {
        "two_factor_enabled": False,
        "privacy_level": "public",
        "data_sharing": True
    },
    
    "activity_log": {
        "activity_type": "LOGIN",
        "description": "Login realizado com sucesso",
        "metadata": {
            "ip_address": "192.168.1.100",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "login_method": "password"
        },
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    },
    
    "acl_check": {
        "user_id": 1,
        "resource": "trading",
        "action": "write",
        "scope": "own"
    }
}

class PersistenceTester:
    """Classe para testar persistência de dados"""
    
    def __init__(self):
        self.engine = create_engine(settings.DATABASE_URI)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.auth_service = AuthService()
        self.acl_service = ACLService()
        self.user_profile_service = UserProfileService()
        
    def test_user_creation(self):
        """Testa criação de usuário"""
        logger.info("=== TESTE: Criação de Usuário ===")
        
        db = self.SessionLocal()
        try:
            # Criar usuário
            user_data = UserCreate(**JSON_EXAMPLES["user_create"])
            user = User(
                username=user_data.username,
                email=user_data.email,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                hashed_password=self.auth_service.get_password_hash(user_data.password),
                is_active=True,
                is_verified=True
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            logger.info(f"✅ Usuário criado: ID={user.id}, Username={user.username}")
            
            # Testar busca
            found_user = db.query(User).filter(User.username == user_data.username).first()
            if found_user:
                logger.info(f"✅ Usuário encontrado: {found_user.username}")
            else:
                logger.error("❌ Usuário não encontrado")
            
            return user
            
        except Exception as e:
            logger.error(f"❌ Erro na criação de usuário: {str(e)}")
            db.rollback()
            raise
        finally:
            db.close()
    
    def test_user_update(self, user_id: int):
        """Testa atualização de usuário"""
        logger.info("=== TESTE: Atualização de Usuário ===")
        
        db = self.SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.error("❌ Usuário não encontrado para atualização")
                return
            
            # Atualizar dados
            update_data = JSON_EXAMPLES["user_update"]
            for field, value in update_data.items():
                setattr(user, field, value)
            
            db.commit()
            db.refresh(user)
            
            logger.info(f"✅ Usuário atualizado: {user.first_name} {user.last_name}")
            
        except Exception as e:
            logger.error(f"❌ Erro na atualização de usuário: {str(e)}")
            db.rollback()
            raise
        finally:
            db.close()
    
    def test_profile_data_creation(self, user_id: int):
        """Testa criação de dados de perfil"""
        logger.info("=== TESTE: Criação de Dados de Perfil ===")
        
        db = self.SessionLocal()
        try:
            # Criar dados de perfil
            profile_data = JSON_EXAMPLES["profile_data_create"]
            profile = UserProfileData(
                user_id=user_id,
                full_name=profile_data["full_name"],
                date_of_birth=datetime.strptime(profile_data["date_of_birth"], "%Y-%m-%d").date(),
                cpf=profile_data["cpf"],
                phone=profile_data["phone"],
                address=profile_data["address"],
                city=profile_data["city"],
                state=profile_data["state"],
                country=profile_data["country"],
                postal_code=profile_data["postal_code"],
                bio=profile_data["bio"]
            )
            
            db.add(profile)
            db.commit()
            db.refresh(profile)
            
            logger.info(f"✅ Dados de perfil criados: {profile.full_name}")
            
            return profile
            
        except Exception as e:
            logger.error(f"❌ Erro na criação de dados de perfil: {str(e)}")
            db.rollback()
            raise
        finally:
            db.close()
    
    def test_preferences_creation(self, user_id: int):
        """Testa criação de preferências"""
        logger.info("=== TESTE: Criação de Preferências ===")
        
        db = self.SessionLocal()
        try:
            # Criar preferências
            prefs_data = JSON_EXAMPLES["preferences_create"]
            preferences = UserPreferences(
                user_id=user_id,
                language=prefs_data["language"],
                timezone=prefs_data["timezone"],
                theme=prefs_data["theme"],
                notifications_enabled=prefs_data["notifications_enabled"],
                email_notifications=prefs_data["email_notifications"],
                push_notifications=prefs_data["push_notifications"],
                sms_notifications=prefs_data["sms_notifications"],
                sound_enabled=prefs_data["sound_enabled"],
                auto_refresh=prefs_data["auto_refresh"],
                refresh_interval=prefs_data["refresh_interval"]
            )
            
            db.add(preferences)
            db.commit()
            db.refresh(preferences)
            
            logger.info(f"✅ Preferências criadas: Tema={preferences.theme}, Idioma={preferences.language}")
            
            return preferences
            
        except Exception as e:
            logger.error(f"❌ Erro na criação de preferências: {str(e)}")
            db.rollback()
            raise
        finally:
            db.close()
    
    def test_settings_creation(self, user_id: int):
        """Testa criação de configurações"""
        logger.info("=== TESTE: Criação de Configurações ===")
        
        db = self.SessionLocal()
        try:
            # Criar configurações
            settings_data = JSON_EXAMPLES["settings_create"]
            user_settings = UserSettings(
                user_id=user_id,
                two_factor_enabled=settings_data["two_factor_enabled"],
                privacy_level=settings_data["privacy_level"],
                data_sharing=settings_data["data_sharing"],
                marketing_emails=settings_data["marketing_emails"],
                newsletter_subscription=settings_data["newsletter_subscription"]
            )
            
            db.add(user_settings)
            db.commit()
            db.refresh(user_settings)
            
            logger.info(f"✅ Configurações criadas: 2FA={user_settings.two_factor_enabled}, Privacidade={user_settings.privacy_level}")
            
            return user_settings
            
        except Exception as e:
            logger.error(f"❌ Erro na criação de configurações: {str(e)}")
            db.rollback()
            raise
        finally:
            db.close()
    
    def test_activity_logging(self, user_id: int):
        """Testa registro de atividades"""
        logger.info("=== TESTE: Registro de Atividades ===")
        
        db = self.SessionLocal()
        try:
            # Registrar atividade
            activity_data = JSON_EXAMPLES["activity_log"]
            activity = UserActivity(
                user_id=user_id,
                activity_type=activity_data["activity_type"],
                description=activity_data["description"],
                metadata=json.dumps(activity_data["metadata"]),
                ip_address=activity_data["ip_address"],
                user_agent=activity_data["user_agent"]
            )
            
            db.add(activity)
            db.commit()
            db.refresh(activity)
            
            logger.info(f"✅ Atividade registrada: {activity.activity_type} - {activity.description}")
            
            return activity
            
        except Exception as e:
            logger.error(f"❌ Erro no registro de atividade: {str(e)}")
            db.rollback()
            raise
        finally:
            db.close()
    
    def test_acl_creation(self):
        """Testa criação de ACL (perfis e permissões)"""
        logger.info("=== TESTE: Criação de ACL ===")
        
        db = self.SessionLocal()
        try:
            # Criar perfil
            profile = Profile(
                name="trader_teste",
                description="Trader de teste com acesso completo"
            )
            db.add(profile)
            db.commit()
            db.refresh(profile)
            
            # Criar permissão
            permission = Permission(
                name="trading:write",
                description="Executar operações de trading",
                resource="trading",
                action="write",
                scope="own"
            )
            db.add(permission)
            db.commit()
            db.refresh(permission)
            
            # Associar permissão ao perfil
            profile_permission = ProfilePermission(
                profile_id=profile.id,
                permission_id=permission.id
            )
            db.add(profile_permission)
            db.commit()
            
            logger.info(f"✅ ACL criado: Perfil={profile.name}, Permissão={permission.name}")
            
            return profile, permission
            
        except Exception as e:
            logger.error(f"❌ Erro na criação de ACL: {str(e)}")
            db.rollback()
            raise
        finally:
            db.close()
    
    def test_complete_user_profile(self, user_id: int):
        """Testa perfil completo do usuário"""
        logger.info("=== TESTE: Perfil Completo do Usuário ===")
        
        db = self.SessionLocal()
        try:
            # Buscar usuário com todos os relacionamentos
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.error("❌ Usuário não encontrado")
                return
            
            # Buscar dados relacionados
            profile_data = db.query(UserProfileData).filter(UserProfileData.user_id == user_id).first()
            preferences = db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()
            settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
            activities = db.query(UserActivity).filter(UserActivity.user_id == user_id).all()
            
            logger.info(f"✅ Perfil completo carregado:")
            logger.info(f"   - Usuário: {user.username} ({user.first_name} {user.last_name})")
            logger.info(f"   - Dados pessoais: {'Sim' if profile_data else 'Não'}")
            logger.info(f"   - Preferências: {'Sim' if preferences else 'Não'}")
            logger.info(f"   - Configurações: {'Sim' if settings else 'Não'}")
            logger.info(f"   - Atividades: {len(activities)} registros")
            
        except Exception as e:
            logger.error(f"❌ Erro ao carregar perfil completo: {str(e)}")
            raise
        finally:
            db.close()
    
    def generate_json_examples(self):
        """Gera exemplos de JSON para documentação"""
        logger.info("=== GERANDO EXEMPLOS JSON ===")
        
        examples_file = "json_examples.json"
        with open(examples_file, 'w', encoding='utf-8') as f:
            json.dump(JSON_EXAMPLES, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Exemplos JSON salvos em: {examples_file}")
        
        # Mostrar exemplos no console
        print("\n" + "="*50)
        print("EXEMPLOS DE JSON PARA PERSISTÊNCIA")
        print("="*50)
        
        for key, value in JSON_EXAMPLES.items():
            print(f"\n{key.upper()}:")
            print(json.dumps(value, indent=2, ensure_ascii=False))
    
    def run_all_tests(self):
        """Executa todos os testes"""
        logger.info("🚀 INICIANDO TESTES DE PERSISTÊNCIA")
        
        try:
            # Teste 1: Criação de usuário
            user = self.test_user_creation()
            
            # Teste 2: Atualização de usuário
            self.test_user_update(user.id)
            
            # Teste 3: Criação de dados de perfil
            self.test_profile_data_creation(user.id)
            
            # Teste 4: Criação de preferências
            self.test_preferences_creation(user.id)
            
            # Teste 5: Criação de configurações
            self.test_settings_creation(user.id)
            
            # Teste 6: Registro de atividades
            self.test_activity_logging(user.id)
            
            # Teste 7: Criação de ACL
            self.test_acl_creation()
            
            # Teste 8: Perfil completo
            self.test_complete_user_profile(user.id)
            
            # Gerar exemplos JSON
            self.generate_json_examples()
            
            logger.info("🎉 TODOS OS TESTES CONCLUÍDOS COM SUCESSO!")
            
        except Exception as e:
            logger.error(f"❌ ERRO NOS TESTES: {str(e)}")
            raise

def main():
    """Função principal"""
    tester = PersistenceTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
