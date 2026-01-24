"""
Script para cadastrar clientes no banco de dados com IDs e números de WhatsApp corretos.
"""
from models import init_db, get_session, Cliente
from db_tools import registrar_cliente, atualizar_cliente, buscar_cliente_por_telefone
import os
import sys

# Configurar encoding para UTF-8 no Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def cadastrar_clientes_iniciais():
    """
    Cadastra os clientes iniciais no banco de dados.
    - ID 1: André Silvério - 556281062311
    - ID 2: Waldeth Oliveira - 556299753008
    """
    db_path = os.getenv("DATABASE_PATH", "tmp/data.db")
    
    # Garantir que o banco existe
    init_db(db_path)
    
    session = get_session(db_path)
    
    try:
        print("=" * 60)
        print("CADASTRANDO/CORRIGINDO CLIENTES NO BANCO DE DADOS")
        print("=" * 60)
        
        telefone_andre = "556281062311"
        telefone_waldeth = "556299753008"
        
        # Primeiro, remover duplicatas e corrigir dados
        print("\n🔍 Verificando e corrigindo registros existentes...")
        
        # Buscar todos os clientes com esses telefones
        clientes_andre = session.query(Cliente).filter(
            (Cliente.telefone == telefone_andre) | 
            (Cliente.telefone == "62981062311") |
            (Cliente.telefone.like(f"%{telefone_andre[-9:]}%"))
        ).all()
        
        clientes_waldeth = session.query(Cliente).filter(
            (Cliente.telefone == telefone_waldeth) |
            (Cliente.telefone.like(f"%{telefone_waldeth[-9:]}%"))
        ).all()
        
        # Remover duplicatas do André (manter apenas o que será ID 1)
        if len(clientes_andre) > 1:
            print(f"   ⚠️  Encontrados {len(clientes_andre)} registros para André, removendo duplicatas...")
            for cliente in clientes_andre[1:]:  # Manter o primeiro, remover os outros
                session.delete(cliente)
                print(f"   🗑️  Removido registro duplicado ID {cliente.id}")
        
        # Remover duplicatas da Waldeth (manter apenas o que será ID 2)
        if len(clientes_waldeth) > 1:
            print(f"   ⚠️  Encontrados {len(clientes_waldeth)} registros para Waldeth, removendo duplicatas...")
            for cliente in clientes_waldeth[1:]:  # Manter o primeiro, remover os outros
                session.delete(cliente)
                print(f"   🗑️  Removido registro duplicado ID {cliente.id}")
        
        session.commit()
        
        # Cliente 1: André Silvério
        print("\n1. Configurando André Silvério (ID 1)...")
        cliente_id_1 = session.query(Cliente).filter_by(id=1).first()
        cliente_por_telefone = session.query(Cliente).filter_by(telefone=telefone_andre).first()
        
        # Remover cliente do ID 1 se não for o André correto
        if cliente_id_1 and cliente_id_1.telefone != telefone_andre:
            print(f"   🗑️  Removendo cliente incorreto do ID 1: {cliente_id_1.nome} (telefone: {cliente_id_1.telefone})")
            session.delete(cliente_id_1)
            session.commit()
            cliente_id_1 = None
        
        # Remover duplicatas do André
        if cliente_por_telefone and cliente_por_telefone.id != 1:
            print(f"   🗑️  Removendo duplicata do André (ID {cliente_por_telefone.id})")
            session.delete(cliente_por_telefone)
            session.commit()
            cliente_por_telefone = None
        
        # Criar ou atualizar cliente no ID 1
        if cliente_id_1:
            cliente_id_1.nome = "André Silvério"
            cliente_id_1.email = f"andre.silverio_{telefone_andre}@whatsapp.com"
            cliente_id_1.telefone = telefone_andre
            session.commit()
            print(f"   ✅ Cliente atualizado: ID 1 - André Silvério - {telefone_andre}")
        else:
            # Usar SQL direto para inserir com ID específico
            from sqlalchemy import text
            session.execute(text("""
                INSERT INTO clientes (id, nome, email, telefone, created_at, updated_at)
                VALUES (1, :nome, :email, :telefone, datetime('now'), datetime('now'))
            """), {
                "nome": "André Silvério",
                "email": f"andre.silverio_{telefone_andre}@whatsapp.com",
                "telefone": telefone_andre
            })
            session.commit()
            print(f"   ✅ Cliente criado: ID 1 - André Silvério - {telefone_andre}")
        
        # Cliente 2: Waldeth Oliveira
        print("\n2. Configurando Waldeth Oliveira (ID 2)...")
        cliente_id_2 = session.query(Cliente).filter_by(id=2).first()
        cliente_por_telefone = session.query(Cliente).filter_by(telefone=telefone_waldeth).first()
        
        # Remover cliente do ID 2 se não for a Waldeth correta
        if cliente_id_2 and cliente_id_2.telefone != telefone_waldeth:
            print(f"   🗑️  Removendo cliente incorreto do ID 2: {cliente_id_2.nome} (telefone: {cliente_id_2.telefone})")
            session.delete(cliente_id_2)
            session.commit()
            cliente_id_2 = None
        
        # Remover duplicatas da Waldeth
        if cliente_por_telefone and cliente_por_telefone.id != 2:
            print(f"   🗑️  Removendo duplicata da Waldeth (ID {cliente_por_telefone.id})")
            session.delete(cliente_por_telefone)
            session.commit()
            cliente_por_telefone = None
        
        # Criar ou atualizar cliente no ID 2
        if cliente_id_2:
            cliente_id_2.nome = "Waldeth Oliveira"
            cliente_id_2.email = f"waldeth.oliveira_{telefone_waldeth}@whatsapp.com"
            cliente_id_2.telefone = telefone_waldeth
            session.commit()
            print(f"   ✅ Cliente atualizado: ID 2 - Waldeth Oliveira - {telefone_waldeth}")
        else:
            # Usar SQL direto para inserir com ID específico
            from sqlalchemy import text
            session.execute(text("""
                INSERT INTO clientes (id, nome, email, telefone, created_at, updated_at)
                VALUES (2, :nome, :email, :telefone, datetime('now'), datetime('now'))
            """), {
                "nome": "Waldeth Oliveira",
                "email": f"waldeth.oliveira_{telefone_waldeth}@whatsapp.com",
                "telefone": telefone_waldeth
            })
            session.commit()
            print(f"   ✅ Cliente criado: ID 2 - Waldeth Oliveira - {telefone_waldeth}")
        
        # Listar todos os clientes cadastrados
        print("\n" + "=" * 60)
        print("CLIENTES CADASTRADOS:")
        print("=" * 60)
        clientes = session.query(Cliente).order_by(Cliente.id).all()
        for cliente in clientes:
            print(f"ID {cliente.id}: {cliente.nome} - {cliente.telefone} - {cliente.email}")
        
        print("\n✅ Cadastro de clientes concluído com sucesso!")
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ Erro ao cadastrar clientes: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


if __name__ == "__main__":
    cadastrar_clientes_iniciais()
