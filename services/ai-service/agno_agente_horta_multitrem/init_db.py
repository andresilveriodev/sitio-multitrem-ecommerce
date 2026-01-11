"""
Script para inicializar o banco de dados.
"""
from models import init_db
from db_tools import popular_produtos_iniciais
import os
import sys

# Configurar encoding para UTF-8 no Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

if __name__ == "__main__":
    db_path = os.getenv("DATABASE_PATH", "tmp/data.db")
    
    print("Inicializando banco de dados da Horta Organica...")
    
    # Criar tabelas
    print("Criando tabelas...")
    init_db(db_path)
    print("Tabelas criadas com sucesso!")
    
    # Popular produtos iniciais
    print("Populando produtos iniciais...")
    resultado = popular_produtos_iniciais()
    if resultado["success"]:
        print(f"OK: {resultado['message']}")
    else:
        print(f"AVISO: {resultado['message']}")
    
    print("\nBanco de dados inicializado com sucesso!")
    print(f"Localizacao: {os.path.abspath(db_path)}")
