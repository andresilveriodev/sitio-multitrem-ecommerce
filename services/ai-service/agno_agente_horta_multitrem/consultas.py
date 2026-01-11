"""
Script para consultas rápidas ao banco de dados.
Útil para administradores verificarem dados do sistema.
"""
from utils import (
    listar_clientes,
    listar_pedidos,
    listar_agendamentos,
    listar_pagamentos,
    obter_estatisticas,
    buscar_cliente_por_email,
    buscar_pedidos_por_cliente,
    obter_relatorio_vendas
)
from models import get_session, Produto
import os
from datetime import datetime, timedelta


def mostrar_clientes():
    """Mostra todos os clientes cadastrados."""
    print("\n" + "="*60)
    print("👥 CLIENTES CADASTRADOS")
    print("="*60)
    
    clientes = listar_clientes()
    if not clientes:
        print("\nNenhum cliente cadastrado ainda.")
        return
    
    for i, cliente in enumerate(clientes, 1):
        print(f"\n{i}. {cliente['nome']}")
        print(f"   📧 Email: {cliente['email']}")
        print(f"   📱 Telefone: {cliente['telefone']}")
        if cliente['endereco']:
            print(f"   📍 Endereço: {cliente['endereco']}")
        print(f"   📅 Cadastrado em: {cliente['created_at']}")


def mostrar_pedidos(status=None):
    """Mostra pedidos com filtro opcional."""
    print("\n" + "="*60)
    print(f"📦 PEDIDOS" + (f" - Status: {status.upper()}" if status else ""))
    print("="*60)
    
    pedidos = listar_pedidos(status=status)
    if not pedidos:
        print("\nNenhum pedido encontrado.")
        return
    
    for i, pedido in enumerate(pedidos, 1):
        print(f"\n{i}. Pedido #{pedido['id']}")
        print(f"   👤 Cliente ID: {pedido['cliente_id']}")
        print(f"   💰 Valor Total: R$ {pedido['valor_total']:.2f}")
        print(f"   📊 Status: {pedido['status']}")
        print(f"   📦 Produtos:")
        for produto in pedido['produtos']:
            print(f"      - {produto.get('quantidade', 0)}x {produto.get('nome', 'N/A')} - R$ {produto.get('preco', 0):.2f}")
        print(f"   📅 Criado em: {pedido['created_at']}")


def mostrar_agendamentos(status=None):
    """Mostra agendamentos com filtro opcional."""
    print("\n" + "="*60)
    print(f"📅 AGENDAMENTOS" + (f" - Status: {status.upper()}" if status else ""))
    print("="*60)
    
    agendamentos = listar_agendamentos(status=status)
    if not agendamentos:
        print("\nNenhum agendamento encontrado.")
        return
    
    for i, agendamento in enumerate(agendamentos, 1):
        print(f"\n{i}. Agendamento #{agendamento['id']}")
        print(f"   📦 Pedido ID: {agendamento['pedido_id']}")
        print(f"   📅 Data: {agendamento['data_entrega']} às {agendamento['horario']}")
        print(f"   📍 Endereço: {agendamento['endereco_entrega']}")
        print(f"   📊 Status: {agendamento['status']}")


def mostrar_pagamentos(status=None):
    """Mostra pagamentos com filtro opcional."""
    print("\n" + "="*60)
    print(f"💳 PAGAMENTOS" + (f" - Status: {status.upper()}" if status else ""))
    print("="*60)
    
    pagamentos = listar_pagamentos(status=status)
    if not pagamentos:
        print("\nNenhum pagamento encontrado.")
        return
    
    for i, pagamento in enumerate(pagamentos, 1):
        print(f"\n{i}. Pagamento #{pagamento['id']}")
        print(f"   📦 Pedido ID: {pagamento['pedido_id']}")
        print(f"   💰 Valor: R$ {pagamento['valor']:.2f}")
        print(f"   💳 Método: {pagamento['metodo_pagamento']}")
        print(f"   📊 Status: {pagamento['status']}")
        print(f"   📅 Data: {pagamento['created_at']}")


def mostrar_produtos():
    """Mostra todos os produtos cadastrados."""
    print("\n" + "="*60)
    print("🛒 PRODUTOS CADASTRADOS")
    print("="*60)
    
    session = get_session(os.getenv("DATABASE_PATH", "tmp/data.db"))
    try:
        produtos = session.query(Produto).order_by(Produto.categoria, Produto.nome).all()
        if not produtos:
            print("\nNenhum produto cadastrado ainda.")
            return
        
        categoria_atual = None
        for produto in produtos:
            if produto.categoria != categoria_atual:
                categoria_atual = produto.categoria
                print(f"\n📂 {categoria_atual.upper()}:")
            
            status = "✅ Disponível" if produto.disponivel == "True" else "❌ Indisponível"
            print(f"   - {produto.nome}: R$ {produto.preco:.2f}/{produto.unidade} {status}")
    finally:
        session.close()


def mostrar_estatisticas():
    """Mostra estatísticas gerais do sistema."""
    print("\n" + "="*60)
    print("📊 ESTATÍSTICAS DO SISTEMA")
    print("="*60)
    
    stats = obter_estatisticas()
    
    print(f"\n👥 Total de Clientes: {stats['total_clientes']}")
    print(f"📦 Total de Pedidos: {stats['total_pedidos']}")
    print(f"📅 Total de Agendamentos: {stats['total_agendamentos']}")
    print(f"💳 Total de Pagamentos: {stats['total_pagamentos']}")
    
    print("\n📋 Pedidos por Status:")
    print(f"   ⏳ Pendentes: {stats['pedidos']['pendentes']}")
    print(f"   ✅ Confirmados: {stats['pedidos']['confirmados']}")
    print(f"   🚚 Entregues: {stats['pedidos']['entregues']}")
    
    print(f"\n💰 Valor Total Confirmado: R$ {stats['valor_total_confirmado']:.2f}")
    
    print("\n💳 Pagamentos por Método:")
    print(f"   📱 PIX: {stats['pagamentos']['pix']}")
    print(f"   💳 Cartão: {stats['pagamentos']['cartao']}")
    print(f"   💵 Dinheiro: {stats['pagamentos']['dinheiro']}")


def mostrar_relatorio_vendas():
    """Gera relatório de vendas."""
    print("\n" + "="*60)
    print("📈 RELATÓRIO DE VENDAS")
    print("="*60)
    
    print("\nDigite o período para o relatório (ou deixe em branco para todos os dados):")
    data_inicio = input("Data início (YYYY-MM-DD) ou Enter para todos: ").strip() or None
    data_fim = input("Data fim (YYYY-MM-DD) ou Enter para hoje: ").strip() or None
    
    relatorio = obter_relatorio_vendas(data_inicio, data_fim)
    
    print(f"\n📅 Período: {relatorio['periodo']['inicio']} até {relatorio['periodo']['fim']}")
    print(f"📦 Total de Vendas: {relatorio['total_vendas']}")
    print(f"💰 Valor Total: R$ {relatorio['valor_total']:.2f}")
    print(f"📊 Ticket Médio: R$ {relatorio['ticket_medio']:.2f}")
    
    if relatorio['produtos_mais_vendidos']:
        print("\n🏆 Produtos Mais Vendidos:")
        for i, produto in enumerate(relatorio['produtos_mais_vendidos'], 1):
            print(f"   {i}. {produto['nome']}: {produto['quantidade']} unidades")


def buscar_cliente():
    """Busca um cliente por email."""
    print("\n" + "="*60)
    print("🔍 BUSCAR CLIENTE")
    print("="*60)
    
    email = input("\nDigite o email do cliente: ").strip()
    cliente = buscar_cliente_por_email(email)
    
    if cliente:
        print(f"\n✅ Cliente encontrado:")
        print(f"   Nome: {cliente['nome']}")
        print(f"   Email: {cliente['email']}")
        print(f"   Telefone: {cliente['telefone']}")
        if cliente['endereco']:
            print(f"   Endereço: {cliente['endereco']}")
        
        # Mostrar pedidos do cliente
        pedidos = buscar_pedidos_por_cliente(cliente['id'])
        if pedidos:
            print(f"\n📦 Pedidos deste cliente ({len(pedidos)}):")
            for pedido in pedidos:
                print(f"   - Pedido #{pedido['id']}: R$ {pedido['valor_total']:.2f} - {pedido['status']}")
    else:
        print(f"\n❌ Cliente com email {email} não encontrado.")


def menu_principal():
    """Menu principal de consultas."""
    print("\n" + "="*60)
    print("🔍 SISTEMA DE CONSULTAS - HORTA ORGÂNICA")
    print("="*60)
    print("\nEscolha uma opção:")
    print("  1. Listar clientes")
    print("  2. Listar pedidos")
    print("  3. Listar agendamentos")
    print("  4. Listar pagamentos")
    print("  5. Listar produtos")
    print("  6. Estatísticas gerais")
    print("  7. Relatório de vendas")
    print("  8. Buscar cliente por email")
    print("  0. Sair")
    
    escolha = input("\nDigite sua escolha: ").strip()
    
    if escolha == "1":
        mostrar_clientes()
    elif escolha == "2":
        status = input("Filtrar por status (pendente/confirmado/entregue) ou Enter para todos: ").strip() or None
        mostrar_pedidos(status)
    elif escolha == "3":
        status = input("Filtrar por status (agendado/confirmado/entregue) ou Enter para todos: ").strip() or None
        mostrar_agendamentos(status)
    elif escolha == "4":
        status = input("Filtrar por status (processado/confirmado) ou Enter para todos: ").strip() or None
        mostrar_pagamentos(status)
    elif escolha == "5":
        mostrar_produtos()
    elif escolha == "6":
        mostrar_estatisticas()
    elif escolha == "7":
        mostrar_relatorio_vendas()
    elif escolha == "8":
        buscar_cliente()
    elif escolha == "0":
        print("\n👋 Até logo!")
        return
    else:
        print("\n❌ Opção inválida!")
    
    input("\nPressione Enter para continuar...")
    menu_principal()


if __name__ == "__main__":
    print("\n🔍 Bem-vindo ao Sistema de Consultas da Horta Orgânica!")
    
    try:
        menu_principal()
    except KeyboardInterrupt:
        print("\n\n👋 Execução interrompida pelo usuário.")
    except Exception as e:
        print(f"\n❌ Erro: {str(e)}")
        print("Verifique se o banco de dados está inicializado.")
