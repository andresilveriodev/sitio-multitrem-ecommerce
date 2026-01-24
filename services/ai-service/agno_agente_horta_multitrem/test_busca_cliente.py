"""
Script para testar a busca de cliente por telefone
"""
import sys
import os

# Adicionar o diretório atual ao path
sys.path.insert(0, os.path.dirname(__file__))

from db_tools import buscar_cliente_por_telefone, extrair_telefone_do_user_id

def test_busca_cliente():
    """Testa a busca de cliente por telefone"""
    
    print("=" * 60)
    print("TESTE DE BUSCA DE CLIENTE POR TELEFONE")
    print("=" * 60)
    
    # Teste 1: Extrair telefone do user_id
    print("\n1. Testando extrair_telefone_do_user_id:")
    user_id = "whatsapp_556281062311"
    telefone = extrair_telefone_do_user_id(user_id)
    print(f"   user_id: {user_id}")
    print(f"   telefone extraído: {telefone}")
    assert telefone == "556281062311", f"Erro: esperado '556281062311', obtido '{telefone}'"
    print("   ✅ Teste 1 passou!")
    
    # Teste 2: Buscar cliente André (ID 1)
    print("\n2. Testando buscar_cliente_por_telefone para André (556281062311):")
    resultado = buscar_cliente_por_telefone("556281062311")
    print(f"   Resultado: {resultado}")
    if resultado['success']:
        print(f"   ✅ Cliente encontrado: {resultado['cliente']['nome']} (ID: {resultado['cliente']['id']})")
        assert resultado['cliente']['id'] == 1, f"Erro: esperado ID 1, obtido ID {resultado['cliente']['id']}"
        assert resultado['cliente']['nome'] == "André Silvério", f"Erro: esperado 'André Silvério', obtido '{resultado['cliente']['nome']}'"
    else:
        print(f"   ❌ Cliente não encontrado: {resultado['message']}")
        assert False, "Cliente deveria ser encontrado!"
    
    # Teste 3: Buscar cliente Waldeth (ID 2)
    print("\n3. Testando buscar_cliente_por_telefone para Waldeth (556299753008):")
    resultado = buscar_cliente_por_telefone("556299753008")
    print(f"   Resultado: {resultado}")
    if resultado['success']:
        print(f"   ✅ Cliente encontrado: {resultado['cliente']['nome']} (ID: {resultado['cliente']['id']})")
        assert resultado['cliente']['id'] == 2, f"Erro: esperado ID 2, obtido ID {resultado['cliente']['id']}"
        assert resultado['cliente']['nome'] == "Waldeth Oliveira", f"Erro: esperado 'Waldeth Oliveira', obtido '{resultado['cliente']['nome']}'"
    else:
        print(f"   ❌ Cliente não encontrado: {resultado['message']}")
        assert False, "Cliente deveria ser encontrado!"
    
    # Teste 4: Buscar com user_id completo
    print("\n4. Testando buscar_cliente_por_telefone com user_id completo (whatsapp_556281062311):")
    resultado = buscar_cliente_por_telefone("whatsapp_556281062311")
    print(f"   Resultado: {resultado}")
    if resultado['success']:
        print(f"   ✅ Cliente encontrado: {resultado['cliente']['nome']} (ID: {resultado['cliente']['id']})")
        assert resultado['cliente']['id'] == 1, f"Erro: esperado ID 1, obtido ID {resultado['cliente']['id']}"
    else:
        print(f"   ❌ Cliente não encontrado: {resultado['message']}")
        assert False, "Cliente deveria ser encontrado!"
    
    # Teste 5: Verificar que números diferentes não dão match
    print("\n5. Testando que número errado não encontra cliente:")
    resultado = buscar_cliente_por_telefone("556281062311")
    if resultado['success']:
        cliente_id = resultado['cliente']['id']
        # Tentar buscar com número similar mas diferente
        resultado2 = buscar_cliente_por_telefone("556299753008")
        if resultado2['success']:
            cliente_id2 = resultado2['cliente']['id']
            assert cliente_id != cliente_id2, "Erro: números diferentes não deveriam retornar o mesmo cliente!"
            print(f"   ✅ Números diferentes retornam clientes diferentes (ID {cliente_id} vs ID {cliente_id2})")
    
    print("\n" + "=" * 60)
    print("✅ TODOS OS TESTES PASSARAM!")
    print("=" * 60)

if __name__ == "__main__":
    test_busca_cliente()
