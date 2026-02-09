#!/usr/bin/env python3
import ast
import sys

def check_syntax(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Tentar compilar o código
        ast.parse(content)
        print(f"✅ Sintaxe do arquivo {file_path} está correta!")
        return True
        
    except SyntaxError as e:
        print(f"❌ Erro de sintaxe em {file_path}:")
        print(f"   Linha {e.lineno}: {e.text}")
        print(f"   Erro: {e.msg}")
        return False
    except Exception as e:
        print(f"❌ Erro ao verificar {file_path}: {e}")
        return False

if __name__ == "__main__":
    files_to_check = [
        "app/routers/analytics_resource.py",
        "app/routers/chatbot_resource.py",
        "app/routers/ai_resource.py"
    ]
    
    all_ok = True
    for file_path in files_to_check:
        if not check_syntax(file_path):
            all_ok = False
    
    if all_ok:
        print("\n🎉 Todos os arquivos têm sintaxe correta!")
    else:
        print("\n❌ Alguns arquivos têm erros de sintaxe!")
        sys.exit(1)
