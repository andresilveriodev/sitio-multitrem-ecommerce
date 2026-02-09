from app.db import engine, Base
from sqlalchemy import text
from models.usage import Usage, UsageSummary
from models.transaction import AITransaction
from models.conversation import Conversation

def test_table_creation():
    try:
        print("Testando conexão...")
        conn = engine.connect()
        print("✅ Conexão estabelecida")
        
        print("\nTestando criação do schema...")
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS chatbot"))
        conn.commit()
        print("✅ Schema chatbot criado/verificado")
        
        print("\nTestando criação das tabelas...")
        
        # Testar cada modelo individualmente
        print("1. Testando modelo Usage...")
        Usage.__table__.create(bind=engine, checkfirst=True)
        print("✅ Tabela Usage criada")
        
        print("2. Testando modelo UsageSummary...")
        UsageSummary.__table__.create(bind=engine, checkfirst=True)
        print("✅ Tabela UsageSummary criada")
        
        print("3. Testando modelo AITransaction...")
        AITransaction.__table__.create(bind=engine, checkfirst=True)
        print("✅ Tabela AITransaction criada")
        
        print("4. Testando modelo Conversation...")
        Conversation.__table__.create(bind=engine, checkfirst=True)
        print("✅ Tabela Conversation criada")
        
        print("\n✅ Todas as tabelas foram criadas com sucesso!")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        print(f"Tipo do erro: {type(e).__name__}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_table_creation()


