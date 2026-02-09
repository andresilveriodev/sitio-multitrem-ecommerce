#!/usr/bin/env python3
import sys
import os

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_router_import():
    try:
        print("🔍 Testando import do router de analytics...")
        
        # Testar import do router
        from app.routers.analytics_resource import router as analytics_router
        print("✅ Router de analytics importado com sucesso!")
        
        # Verificar se o router tem endpoints
        print(f"📋 Router tem {len(analytics_router.routes)} rotas:")
        for route in analytics_router.routes:
            print(f"  • {route.methods} {route.path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao importar router: {e}")
        return False

def test_main_import():
    try:
        print("\n🔍 Testando import do main.py...")
        
        # Testar import do main
        from main import app
        print("✅ Main.py importado com sucesso!")
        
        # Verificar rotas registradas
        print(f"📋 App tem {len(app.routes)} rotas registradas:")
        for route in app.routes:
            if hasattr(route, 'path'):
                print(f"  • {route.path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao importar main.py: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testando carregamento dos routers...")
    print("=" * 50)
    
    success = True
    success &= test_router_import()
    success &= test_main_import()
    
    if success:
        print("\n🎉 Todos os testes passaram!")
    else:
        print("\n❌ Alguns testes falharam!")
        sys.exit(1)
