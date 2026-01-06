from agno.db.postgres import PostgresDb
import os
from dotenv import load_dotenv

load_dotenv()

def get_postgres_db():
    """
    Configura o DB PostgreSQL para persistir sessoes.
    Compativel com as variaveis de ambiente do projeto Sitio Multitrem.
    """
    db_user = os.getenv('DATABASE_USER', os.getenv('DB_USER', 'postgres'))
    db_pass = os.getenv('DATABASE_PASSWORD', os.getenv('DB_PASSWORD', ''))
    db_host = os.getenv('DATABASE_HOST', os.getenv('DB_HOST', 'localhost'))
    db_port = os.getenv('DATABASE_PORT', os.getenv('DB_PORT', '5432'))
    db_name = os.getenv('DATABASE_NAME', os.getenv('DB_NAME', 'sitio_multitrem'))
    
    db_url = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    
    return PostgresDb(
        table_name="agent_sessions",
        db_url=db_url
    )

