#!/usr/bin/env python3
"""
Script para testar todos os endpoints da API
"""

import asyncio
import json
import httpx
import structlog
from datetime import datetime

logger = structlog.get_logger()

# Configurações
BASE_URL = "http://localhost:8001"
API_BASE = f"{BASE_URL}/api/v1"

# Dados de teste
TEST_USER = {
    "username": "teste_api",
    "email": "teste_api@exemplo.com",
    "first_name": "João",
    "last_name": "Silva",
    "password": "senha123"
}

TEST_PROFILE_DATA = {
    "full_name": "João Silva",
    "date_of_birth": "1990-05-15",
    "cpf": "123.456.789-01",
    "phone": "+55-11-99999-9999",
    "address": "Rua das Flores, 123",
    "city": "São Paulo",
    "state": "SP",
    "country": "Brasil",
    "postal_code": "01234-567",
    "bio": "Desenvolvedor de software"
}

TEST_PREFERENCES = {
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
}

TEST_SETTINGS = {
    "two_factor_enabled": True,
    "privacy_level": "private",
    "data_sharing": False,
    "marketing_emails": False,
    "newsletter_subscription": True
}

class APITester:
    """Classe para testar endpoints da API"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.access_token = None
        self.user_id = None
    
    async def test_health_check(self):
        """Testa endpoint de health check"""
        logger.info("=== TESTE: Health Check ===")
        
        try:
            response = await self.client.get(f"{BASE_URL}/health")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Health check OK: {data}")
                return True
            else:
                logger.error(f"❌ Health check falhou: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro no health check: {str(e)}")
            return False
    
    async def test_user_registration(self):
        """Testa registro de usuário"""
        logger.info("=== TESTE: Registro de Usuário ===")
        
        try:
            response = await self.client.post(
                f"{API_BASE}/auth/register",
                json=TEST_USER
            )
            
            if response.status_code == 201:
                data = response.json()
                logger.info(f"✅ Usuário registrado: {data['username']}")
                return True
            else:
                logger.error(f"❌ Registro falhou: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro no registro: {str(e)}")
            return False
    
    async def test_user_login(self):
        """Testa login de usuário"""
        logger.info("=== TESTE: Login de Usuário ===")
        
        try:
            response = await self.client.post(
                f"{API_BASE}/auth/login",
                data={
                    "username": TEST_USER["username"],
                    "password": TEST_USER["password"]
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data["access_token"]
                logger.info(f"✅ Login realizado: Token obtido")
                return True
            else:
                logger.error(f"❌ Login falhou: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro no login: {str(e)}")
            return False
    
    async def test_get_current_user(self):
        """Testa obtenção do usuário atual"""
        logger.info("=== TESTE: Obter Usuário Atual ===")
        
        if not self.access_token:
            logger.error("❌ Token não disponível")
            return False
        
        try:
            response = await self.client.get(
                f"{API_BASE}/auth/user",
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.user_id = data["id"]
                logger.info(f"✅ Usuário atual obtido: {data['username']}")
                return True
            else:
                logger.error(f"❌ Obter usuário falhou: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao obter usuário: {str(e)}")
            return False
    
    async def test_create_profile_data(self):
        """Testa criação de dados de perfil"""
        logger.info("=== TESTE: Criar Dados de Perfil ===")
        
        if not self.access_token or not self.user_id:
            logger.error("❌ Token ou user_id não disponível")
            return False
        
        try:
            response = await self.client.post(
                f"{API_BASE}/users/{self.user_id}/profile",
                json=TEST_PROFILE_DATA,
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            
            if response.status_code == 201:
                data = response.json()
                logger.info(f"✅ Dados de perfil criados: {data['full_name']}")
                return True
            else:
                logger.error(f"❌ Criar perfil falhou: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao criar perfil: {str(e)}")
            return False
    
    async def test_get_profile_data(self):
        """Testa obtenção de dados de perfil"""
        logger.info("=== TESTE: Obter Dados de Perfil ===")
        
        if not self.access_token or not self.user_id:
            logger.error("❌ Token ou user_id não disponível")
            return False
        
        try:
            response = await self.client.get(
                f"{API_BASE}/users/{self.user_id}/profile",
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Dados de perfil obtidos: {data['full_name']}")
                return True
            else:
                logger.error(f"❌ Obter perfil falhou: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao obter perfil: {str(e)}")
            return False
    
    async def test_update_preferences(self):
        """Testa atualização de preferências"""
        logger.info("=== TESTE: Atualizar Preferências ===")
        
        if not self.access_token or not self.user_id:
            logger.error("❌ Token ou user_id não disponível")
            return False
        
        try:
            response = await self.client.put(
                f"{API_BASE}/users/{self.user_id}/preferences",
                json=TEST_PREFERENCES,
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Preferências atualizadas: {data['theme']}")
                return True
            else:
                logger.error(f"❌ Atualizar preferências falhou: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar preferências: {str(e)}")
            return False
    
    async def test_get_preferences(self):
        """Testa obtenção de preferências"""
        logger.info("=== TESTE: Obter Preferências ===")
        
        if not self.access_token or not self.user_id:
            logger.error("❌ Token ou user_id não disponível")
            return False
        
        try:
            response = await self.client.get(
                f"{API_BASE}/users/{self.user_id}/preferences",
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Preferências obtidas: {data['theme']}")
                return True
            else:
                logger.error(f"❌ Obter preferências falhou: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao obter preferências: {str(e)}")
            return False
    
    async def test_update_settings(self):
        """Testa atualização de configurações"""
        logger.info("=== TESTE: Atualizar Configurações ===")
        
        if not self.access_token or not self.user_id:
            logger.error("❌ Token ou user_id não disponível")
            return False
        
        try:
            response = await self.client.put(
                f"{API_BASE}/users/{self.user_id}/settings",
                json=TEST_SETTINGS,
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Configurações atualizadas: {data['privacy_level']}")
                return True
            else:
                logger.error(f"❌ Atualizar configurações falhou: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar configurações: {str(e)}")
            return False
    
    async def test_get_settings(self):
        """Testa obtenção de configurações"""
        logger.info("=== TESTE: Obter Configurações ===")
        
        if not self.access_token or not self.user_id:
            logger.error("❌ Token ou user_id não disponível")
            return False
        
        try:
            response = await self.client.get(
                f"{API_BASE}/users/{self.user_id}/settings",
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Configurações obtidas: {data['privacy_level']}")
                return True
            else:
                logger.error(f"❌ Obter configurações falhou: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao obter configurações: {str(e)}")
            return False
    
    async def test_get_complete_profile(self):
        """Testa obtenção de perfil completo"""
        logger.info("=== TESTE: Obter Perfil Completo ===")
        
        if not self.access_token or not self.user_id:
            logger.error("❌ Token ou user_id não disponível")
            return False
        
        try:
            response = await self.client.get(
                f"{API_BASE}/users/{self.user_id}/complete",
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Perfil completo obtido: {data['username']}")
                logger.info(f"   - Dados pessoais: {'Sim' if data.get('profile_data') else 'Não'}")
                logger.info(f"   - Preferências: {'Sim' if data.get('preferences') else 'Não'}")
                logger.info(f"   - Configurações: {'Sim' if data.get('settings') else 'Não'}")
                return True
            else:
                logger.error(f"❌ Obter perfil completo falhou: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao obter perfil completo: {str(e)}")
            return False
    
    async def test_get_activities(self):
        """Testa obtenção de atividades"""
        logger.info("=== TESTE: Obter Atividades ===")
        
        if not self.access_token or not self.user_id:
            logger.error("❌ Token ou user_id não disponível")
            return False
        
        try:
            response = await self.client.get(
                f"{API_BASE}/users/{self.user_id}/activities",
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Atividades obtidas: {len(data)} registros")
                return True
            else:
                logger.error(f"❌ Obter atividades falhou: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao obter atividades: {str(e)}")
            return False
    
    async def test_acl_check(self):
        """Testa verificação de ACL"""
        logger.info("=== TESTE: Verificação ACL ===")
        
        if not self.access_token:
            logger.error("❌ Token não disponível")
            return False
        
        try:
            acl_data = {
                "user_id": self.user_id,
                "resource": "trading",
                "action": "write",
                "scope": "own"
            }
            
            response = await self.client.post(
                f"{API_BASE}/acl/check",
                json=acl_data,
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ ACL verificado: {data['allowed']}")
                return True
            else:
                logger.error(f"❌ Verificação ACL falhou: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro na verificação ACL: {str(e)}")
            return False
    
    async def test_user_logout(self):
        """Testa logout de usuário"""
        logger.info("=== TESTE: Logout de Usuário ===")
        
        if not self.access_token:
            logger.error("❌ Token não disponível")
            return False
        
        try:
            response = await self.client.post(
                f"{API_BASE}/auth/logout",
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            
            if response.status_code == 200:
                logger.info("✅ Logout realizado com sucesso")
                return True
            else:
                logger.error(f"❌ Logout falhou: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro no logout: {str(e)}")
            return False
    
    async def generate_api_examples(self):
        """Gera exemplos de chamadas da API"""
        logger.info("=== GERANDO EXEMPLOS DE API ===")
        
        api_examples = {
            "endpoints": {
                "health_check": f"GET {BASE_URL}/health",
                "user_registration": f"POST {API_BASE}/auth/register",
                "user_login": f"POST {API_BASE}/auth/login",
                "get_current_user": f"GET {API_BASE}/auth/user",
                "create_profile": f"POST {API_BASE}/users/{{user_id}}/profile",
                "get_profile": f"GET {API_BASE}/users/{{user_id}}/profile",
                "update_preferences": f"PUT {API_BASE}/users/{{user_id}}/preferences",
                "get_preferences": f"GET {API_BASE}/users/{{user_id}}/preferences",
                "update_settings": f"PUT {API_BASE}/users/{{user_id}}/settings",
                "get_settings": f"GET {API_BASE}/users/{{user_id}}/settings",
                "get_complete_profile": f"GET {API_BASE}/users/{{user_id}}/complete",
                "get_activities": f"GET {API_BASE}/users/{{user_id}}/activities",
                "acl_check": f"POST {API_BASE}/acl/check",
                "user_logout": f"POST {API_BASE}/auth/logout"
            },
            "request_examples": {
                "user_registration": TEST_USER,
                "user_login": {
                    "username": "teste_api",
                    "password": "senha123"
                },
                "profile_data": TEST_PROFILE_DATA,
                "preferences": TEST_PREFERENCES,
                "settings": TEST_SETTINGS,
                "acl_check": {
                    "user_id": 1,
                    "resource": "trading",
                    "action": "write",
                    "scope": "own"
                }
            },
            "headers": {
                "content_type": "Content-Type: application/json",
                "authorization": "Authorization: Bearer {access_token}"
            }
        }
        
        # Salvar exemplos em arquivo
        with open("api_examples.json", "w", encoding="utf-8") as f:
            json.dump(api_examples, f, indent=2, ensure_ascii=False)
        
        logger.info("✅ Exemplos de API salvos em: api_examples.json")
        
        # Mostrar exemplos no console
        print("\n" + "="*50)
        print("EXEMPLOS DE ENDPOINTS DA API")
        print("="*50)
        
        for name, endpoint in api_examples["endpoints"].items():
            print(f"\n{name.upper()}:")
            print(f"  {endpoint}")
    
    async def run_all_tests(self):
        """Executa todos os testes da API"""
        logger.info("🚀 INICIANDO TESTES DA API")
        
        try:
            # Teste 1: Health check
            await self.test_health_check()
            
            # Teste 2: Registro de usuário
            await self.test_user_registration()
            
            # Teste 3: Login
            if await self.test_user_login():
                
                # Teste 4: Obter usuário atual
                await self.test_get_current_user()
                
                # Teste 5: Criar dados de perfil
                await self.test_create_profile_data()
                
                # Teste 6: Obter dados de perfil
                await self.test_get_profile_data()
                
                # Teste 7: Atualizar preferências
                await self.test_update_preferences()
                
                # Teste 8: Obter preferências
                await self.test_get_preferences()
                
                # Teste 9: Atualizar configurações
                await self.test_update_settings()
                
                # Teste 10: Obter configurações
                await self.test_get_settings()
                
                # Teste 11: Obter perfil completo
                await self.test_get_complete_profile()
                
                # Teste 12: Obter atividades
                await self.test_get_activities()
                
                # Teste 13: Verificação ACL
                await self.test_acl_check()
                
                # Teste 14: Logout
                await self.test_user_logout()
            
            # Gerar exemplos de API
            await self.generate_api_examples()
            
            logger.info("🎉 TODOS OS TESTES DA API CONCLUÍDOS!")
            
        except Exception as e:
            logger.error(f"❌ ERRO NOS TESTES DA API: {str(e)}")
            raise
        finally:
            await self.client.aclose()

async def main():
    """Função principal"""
    tester = APITester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())

