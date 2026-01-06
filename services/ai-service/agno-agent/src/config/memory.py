from agno.memory.manager import MemoryManager
from agno.db.postgres import PostgresDb
from agno.models.openai import OpenAIChat
import os
from dotenv import load_dotenv

load_dotenv()

def get_agent_memory():
    """
    Configura a memoria persistente para o agente.
    Permite lembrar informacoes importantes sobre o usuario.
    Compativel com as variaveis de ambiente do projeto Sitio Multitrem.
    """
    db_user = os.getenv('DATABASE_USER', os.getenv('DB_USER', 'postgres'))
    db_pass = os.getenv('DATABASE_PASSWORD', os.getenv('DB_PASSWORD', ''))
    db_host = os.getenv('DATABASE_HOST', os.getenv('DB_HOST', 'localhost'))
    db_port = os.getenv('DATABASE_PORT', os.getenv('DB_PORT', '5432'))
    db_name = os.getenv('DATABASE_NAME', os.getenv('DB_NAME', 'sitio_multitrem'))
    
    db_url = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    
    # Usar modelo configurado no .env ou padrao
    model_id = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    
    # Configurar o banco de dados para memoria
    db = PostgresDb(
        table_name="agent_memories",
        db_url=db_url
    )
    
    return MemoryManager(
        model=OpenAIChat(id=model_id),
        db=db
    )

