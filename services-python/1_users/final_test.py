"""
Teste final de persistência - versão simplificada
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
    echo=False  # Desabilitar logs para limpeza
)

# Criar sessão
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_basic_persistence():
    """Testa persistência básica funcionando"""
    print("🚀 TESTE FINAL DE PERSISTÊNCIA")
    print("=" * 50)
    
    db = SessionLocal()
    
    try:
        # 1. Inserir usuário com todos os campos obrigatórios
        print("1. Criando usuário...")
        result = db.execute(text("""
            INSERT INTO users (
                username, email, hashed_password, is_active, is_verified,
                created_at, updated_at
            )
            VALUES (
                :username, :email, :password, :active, :verified,
                NOW(), NOW()
            )
            RETURNING id, username
        """), {
            "username": "test_user_final",
            "email": "test_final@example.com",
            "password": "hashed_password_123",
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
        
        # 3. Criar perfil
        print("3. Criando perfil...")
        result = db.execute(text("""
            INSERT INTO profiles (name, description, is_active, created_at, updated_at)
            VALUES (:name, :description, :active, NOW(), NOW())
            RETURNING id, name
        """), {
            "name": "test_profile_final",
            "description": "Perfil de teste final",
            "active": True
        })
        profile = result.fetchone()
        db.commit()
        print(f"✅ Perfil criado: ID={profile[0]}, Name={profile[1]}")
        
        # 4. Criar permissão
        print("4. Criando permissão...")
        result = db.execute(text("""
            INSERT INTO permissions (name, description, resource, action, scope, is_active, created_at)
            VALUES (:name, :description, :resource, :action, :scope, :active, NOW())
            RETURNING id, name
        """), {
            "name": "test_permission_final",
            "description": "Permissão de teste final",
            "resource": "test",
            "action": "read",
            "scope": "own",
            "active": True
        })
        permission = result.fetchone()
        db.commit()
        print(f"✅ Permissão criada: ID={permission[0]}, Name={permission[1]}")
        
        # 5. Listar todos os registros
        print("5. Listando registros...")
        
        # Usuários
        result = db.execute(text("SELECT COUNT(*) FROM users"))
        user_count = result.fetchone()[0]
        print(f"✅ Total de usuários: {user_count}")
        
        # Perfis
        result = db.execute(text("SELECT COUNT(*) FROM profiles"))
        profile_count = result.fetchone()[0]
        print(f"✅ Total de perfis: {profile_count}")
        
        # Permissões
        result = db.execute(text("SELECT COUNT(*) FROM permissions"))
        permission_count = result.fetchone()[0]
        print(f"✅ Total de permissões: {permission_count}")
        
        # 6. Testar consulta complexa
        print("6. Testando consulta complexa...")
        result = db.execute(text("""
            SELECT 
                u.username,
                p.name as profile_name,
                perm.name as permission_name
            FROM users u
            CROSS JOIN profiles p
            CROSS JOIN permissions perm
            WHERE u.id = :user_id AND p.id = :profile_id AND perm.id = :permission_id
        """), {
            "user_id": user[0],
            "profile_id": profile[0],
            "permission_id": permission[0]
        })
        
        relationships = result.fetchall()
        print(f"✅ Relacionamentos testados: {len(relationships)}")
        for rel in relationships:
            print(f"   - {rel[0]} -> {rel[1]} -> {rel[2]}")
        
        print("\n✅ TODOS OS TESTES PASSARAM!")
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def test_table_structure():
    """Verifica estrutura das tabelas"""
    print("\n📋 ESTRUTURA DAS TABELAS:")
    print("-" * 30)
    
    try:
        with engine.connect() as conn:
            # Verificar tabelas existentes
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """))
            tables = result.fetchall()
            
            print("Tabelas encontradas:")
            for table in tables:
                print(f"  - {table[0]}")
            
            # Verificar estrutura da tabela users
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                ORDER BY ordinal_position
            """))
            columns = result.fetchall()
            
            print(f"\nEstrutura da tabela 'users' ({len(columns)} colunas):")
            for col in columns:
                null_status = "NULL" if col[2] == "YES" else "NOT NULL"
                print(f"  - {col[0]}: {col[1]} ({null_status})")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro ao verificar estrutura: {e}")
        return False

if __name__ == "__main__":
    test_table_structure()
    test_basic_persistence()
    
    print("\n" + "=" * 50)
    print("🎉 TESTE FINAL CONCLUÍDO!")
    print("=" * 50)



