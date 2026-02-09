"""
Script de teste simples para verificar persistências básicas
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config import settings

# Criar engine do banco de dados
engine = create_engine(
    settings.DATABASE_URI,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    pool_recycle=settings.DATABASE_POOL_RECYCLE,
    echo=True
)

# Criar sessão
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_database_connection():
    """Testa conexão com o banco"""
    print("=== TESTE DE CONEXÃO COM BANCO ===")
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Conexão estabelecida: {version}")
            return True
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        return False

def test_table_structure():
    """Testa estrutura das tabelas"""
    print("\n=== TESTE DE ESTRUTURA DAS TABELAS ===")
    
    try:
        with engine.connect() as conn:
            # Verificar tabela users
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                ORDER BY ordinal_position
            """))
            columns = result.fetchall()
            print("✅ Tabela 'users' encontrada:")
            for col in columns:
                print(f"   - {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")
            
            # Verificar tabela profiles
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'profiles' 
                ORDER BY ordinal_position
            """))
            columns = result.fetchall()
            print("✅ Tabela 'profiles' encontrada:")
            for col in columns:
                print(f"   - {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")
            
            # Verificar tabela permissions
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'permissions' 
                ORDER BY ordinal_position
            """))
            columns = result.fetchall()
            print("✅ Tabela 'permissions' encontrada:")
            for col in columns:
                print(f"   - {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")
            
            return True
    except Exception as e:
        print(f"❌ Erro ao verificar estrutura: {e}")
        return False

def test_basic_operations():
    """Testa operações básicas"""
    print("\n=== TESTE DE OPERAÇÕES BÁSICAS ===")
    
    db = SessionLocal()
    
    try:
        # 1. Inserir usuário
        print("1. Inserindo usuário...")
        result = db.execute(text("""
            INSERT INTO users (username, email, hashed_password, is_active, is_verified)
            VALUES (:username, :email, :password, :active, :verified)
            RETURNING id, username
        """), {
            "username": "test_user",
            "email": "test@example.com",
            "password": "hashed_password",
            "active": True,
            "verified": True
        })
        user = result.fetchone()
        db.commit()
        print(f"✅ Usuário criado: ID={user[0]}, Username={user[1]}")
        
        # 2. Buscar usuário
        print("2. Buscando usuário...")
        result = db.execute(text("SELECT id, username, email FROM users WHERE id = :id"), {"id": user[0]})
        found_user = result.fetchone()
        if found_user:
            print(f"✅ Usuário encontrado: {found_user[1]} ({found_user[2]})")
        else:
            print("❌ Usuário não encontrado")
        
        # 3. Inserir perfil
        print("3. Inserindo perfil...")
        result = db.execute(text("""
            INSERT INTO profiles (name, description, is_active)
            VALUES (:name, :description, :active)
            RETURNING id, name
        """), {
            "name": "test_profile",
            "description": "Perfil de teste",
            "active": True
        })
        profile = result.fetchone()
        db.commit()
        print(f"✅ Perfil criado: ID={profile[0]}, Name={profile[1]}")
        
        # 4. Inserir permissão
        print("4. Inserindo permissão...")
        result = db.execute(text("""
            INSERT INTO permissions (name, description, resource, action, scope, is_active)
            VALUES (:name, :description, :resource, :action, :scope, :active)
            RETURNING id, name
        """), {
            "name": "test_permission",
            "description": "Permissão de teste",
            "resource": "test",
            "action": "read",
            "scope": "own",
            "active": True
        })
        permission = result.fetchone()
        db.commit()
        print(f"✅ Permissão criada: ID={permission[0]}, Name={permission[1]}")
        
        # 5. Relacionar usuário e perfil
        print("5. Relacionando usuário e perfil...")
        result = db.execute(text("""
            INSERT INTO user_profiles (user_id, profile_id, assigned_by)
            VALUES (:user_id, :profile_id, :assigned_by)
            RETURNING id
        """), {
            "user_id": user[0],
            "profile_id": profile[0],
            "assigned_by": user[0]
        })
        user_profile = result.fetchone()
        db.commit()
        print(f"✅ Relacionamento criado: ID={user_profile[0]}")
        
        # 6. Relacionar perfil e permissão
        print("6. Relacionando perfil e permissão...")
        result = db.execute(text("""
            INSERT INTO profile_permissions (profile_id, permission_id)
            VALUES (:profile_id, :permission_id)
            RETURNING id
        """), {
            "profile_id": profile[0],
            "permission_id": permission[0]
        })
        profile_permission = result.fetchone()
        db.commit()
        print(f"✅ Relacionamento criado: ID={profile_permission[0]}")
        
        # 7. Consulta complexa
        print("7. Executando consulta complexa...")
        result = db.execute(text("""
            SELECT u.username, p.name as profile_name, perm.name as permission_name
            FROM users u
            JOIN user_profiles up ON u.id = up.user_id
            JOIN profiles p ON up.profile_id = p.id
            JOIN profile_permissions pp ON p.id = pp.profile_id
            JOIN permissions perm ON pp.permission_id = perm.id
            WHERE u.id = :user_id
        """), {"user_id": user[0]})
        
        relationships = result.fetchall()
        print(f"✅ Relacionamentos encontrados: {len(relationships)}")
        for rel in relationships:
            print(f"   - {rel[0]} -> {rel[1]} -> {rel[2]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro nas operações básicas: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def test_user_profile_data():
    """Testa dados pessoais do usuário"""
    print("\n=== TESTE DE DADOS PESSOAIS ===")
    
    db = SessionLocal()
    
    try:
        # Buscar usuário existente
        result = db.execute(text("SELECT id FROM users LIMIT 1"))
        user = result.fetchone()
        
        if not user:
            print("❌ Nenhum usuário encontrado para teste")
            return False
        
        user_id = user[0]
        
        # 1. Inserir dados pessoais
        print("1. Inserindo dados pessoais...")
        result = db.execute(text("""
            INSERT INTO user_profiles_data (user_id, full_name, cpf, phone, address, city, state, country)
            VALUES (:user_id, :full_name, :cpf, :phone, :address, :city, :state, :country)
            RETURNING id, full_name
        """), {
            "user_id": user_id,
            "full_name": "João Pedro Silva",
            "cpf": "123.456.789-00",
            "phone": "(11) 99999-9999",
            "address": "Rua das Flores, 123",
            "city": "São Paulo",
            "state": "SP",
            "country": "Brasil"
        })
        profile_data = result.fetchone()
        db.commit()
        print(f"✅ Dados pessoais criados: {profile_data[1]}")
        
        # 2. Inserir preferências
        print("2. Inserindo preferências...")
        result = db.execute(text("""
            INSERT INTO user_preferences (user_id, language, timezone, theme, notifications_enabled)
            VALUES (:user_id, :language, :timezone, :theme, :notifications)
            RETURNING id, theme
        """), {
            "user_id": user_id,
            "language": "pt-BR",
            "timezone": "America/Sao_Paulo",
            "theme": "dark",
            "notifications": True
        })
        preferences = result.fetchone()
        db.commit()
        print(f"✅ Preferências criadas: tema={preferences[1]}")
        
        # 3. Inserir configurações
        print("3. Inserindo configurações...")
        result = db.execute(text("""
            INSERT INTO user_settings (user_id, two_factor_enabled, privacy_level, data_sharing)
            VALUES (:user_id, :two_factor, :privacy, :data_sharing)
            RETURNING id, privacy_level
        """), {
            "user_id": user_id,
            "two_factor": False,
            "privacy": "public",
            "data_sharing": True
        })
        settings = result.fetchone()
        db.commit()
        print(f"✅ Configurações criadas: privacidade={settings[1]}")
        
        # 4. Inserir atividade
        print("4. Inserindo atividade...")
        result = db.execute(text("""
            INSERT INTO user_activities (user_id, activity_type, description, ip_address)
            VALUES (:user_id, :activity_type, :description, :ip_address)
            RETURNING id, activity_type
        """), {
            "user_id": user_id,
            "activity_type": "profile_updated",
            "description": "Perfil atualizado",
            "ip_address": "127.0.0.1"
        })
        activity = result.fetchone()
        db.commit()
        print(f"✅ Atividade criada: {activity[1]}")
        
        # 5. Consulta completa do usuário
        print("5. Consultando dados completos do usuário...")
        result = db.execute(text("""
            SELECT 
                u.username,
                upd.full_name,
                upref.theme,
                uset.privacy_level,
                COUNT(ua.id) as activities_count
            FROM users u
            LEFT JOIN user_profiles_data upd ON u.id = upd.user_id
            LEFT JOIN user_preferences upref ON u.id = upref.user_id
            LEFT JOIN user_settings uset ON u.id = uset.user_id
            LEFT JOIN user_activities ua ON u.id = ua.user_id
            WHERE u.id = :user_id
            GROUP BY u.id, u.username, upd.full_name, upref.theme, uset.privacy_level
        """), {"user_id": user_id})
        
        user_data = result.fetchone()
        if user_data:
            print(f"✅ Dados completos: {user_data[0]} - {user_data[1]} - {user_data[2]} - {user_data[3]} - {user_data[4]} atividades")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro nos dados pessoais: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def main():
    """Executa todos os testes"""
    print("🚀 INICIANDO TESTES SIMPLES DE PERSISTÊNCIA")
    print("=" * 60)
    
    # Testes básicos
    test_database_connection()
    test_table_structure()
    test_basic_operations()
    test_user_profile_data()
    
    print("\n" + "=" * 60)
    print("✅ TESTES SIMPLES CONCLUÍDOS!")
    print("=" * 60)

if __name__ == "__main__":
    main()



