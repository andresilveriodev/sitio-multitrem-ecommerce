import logging
import sys
from datetime import datetime
import os

def setup_logger(name: str = "chatbot_middleware", level: str = "INFO") -> logging.Logger:
    """
    Configura e retorna um logger personalizado
    
    Args:
        name: Nome do logger
        level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        logging.Logger: Logger configurado
    """
    
    # Cria o logger
    logger = logging.getLogger(name)
    
    # Define o nível de log
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Remove handlers existentes para evitar duplicação
    if logger.handlers:
        logger.handlers.clear()
    
    # Formato das mensagens de log
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Handler para arquivo (opcional)
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_file = os.path.join(log_dir, f"chatbot_middleware_{datetime.now().strftime('%Y%m%d')}.log")
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Evita propagação para o logger raiz
    logger.propagate = False
    
    return logger

def get_logger(name: str = "chatbot_middleware") -> logging.Logger:
    """
    Retorna um logger existente ou cria um novo
    
    Args:
        name: Nome do logger
    
    Returns:
        logging.Logger: Logger configurado
    """
    logger = logging.getLogger(name)
    
    # Se o logger não tem handlers, configura-o
    if not logger.handlers:
        return setup_logger(name)
    
    return logger

# Configuração global do logging
def configure_logging():
    """
    Configura o sistema de logging global da aplicação
    """
    # Nível de log baseado na variável de ambiente
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Configura o logger principal
    main_logger = setup_logger("chatbot_middleware", log_level)
    
    # Configura loggers específicos
    setup_logger("uvicorn", log_level)
    setup_logger("fastapi", log_level)
    setup_logger("sqlalchemy", "WARNING")  # Reduz verbosidade do SQLAlchemy
    
    main_logger.info(f"Sistema de logging configurado com nível: {log_level}")
    
    return main_logger

# Logger padrão da aplicação
app_logger = get_logger("chatbot_middleware")