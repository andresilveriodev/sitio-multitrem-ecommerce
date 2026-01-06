import os
from dotenv import load_dotenv

load_dotenv()

# Configuracoes do OpenAI
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
OPENAI_TEMPERATURE = float(os.getenv('OPENAI_TEMPERATURE', '0.7'))
OPENAI_MAX_TOKENS = int(os.getenv('OPENAI_MAX_TOKENS', '500'))

# Configuracoes do Groq (alternativa gratuita)
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# URLs dos Microsservicos
PRODUCT_SERVICE_URL = os.getenv('PRODUCT_SERVICE_URL', 'http://localhost:3001')
CART_SERVICE_URL = os.getenv('CART_SERVICE_URL', 'http://localhost:3002')
ORDER_SERVICE_URL = os.getenv('ORDER_SERVICE_URL', 'http://localhost:3003')
PAYMENT_SERVICE_URL = os.getenv('PAYMENT_SERVICE_URL', 'http://localhost:3004')
AUTH_SERVICE_URL = os.getenv('AUTH_SERVICE_URL', 'http://localhost:3005')
WHATSAPP_SERVICE_URL = os.getenv('WHATSAPP_SERVICE_URL', 'http://localhost:3006')
AI_SERVICE_URL = os.getenv('AI_SERVICE_URL', 'http://localhost:3007')
GATEWAY_URL = os.getenv('GATEWAY_URL', 'http://localhost:8000')

# Configuracoes do Banco de Dados
DATABASE_HOST = os.getenv('DATABASE_HOST', os.getenv('DB_HOST', 'localhost'))
DATABASE_PORT = os.getenv('DATABASE_PORT', os.getenv('DB_PORT', '5432'))
DATABASE_NAME = os.getenv('DATABASE_NAME', os.getenv('DB_NAME', 'sitio_multitrem'))
DATABASE_USER = os.getenv('DATABASE_USER', os.getenv('DB_USER', 'postgres'))
DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD', os.getenv('DB_PASSWORD', ''))

# Configuracoes do Redis
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')

# Configuracoes do Servidor
PORT = int(os.getenv('PORT', '3007'))
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
NODE_ENV = os.getenv('NODE_ENV', 'development')

def get_database_url():
    """Retorna a URL de conexao do banco de dados."""
    return f"postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"

