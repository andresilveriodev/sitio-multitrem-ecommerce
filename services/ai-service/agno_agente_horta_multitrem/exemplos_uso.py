"""
Exemplos de uso do sistema de agentes da horta orgânica.
Execute este arquivo para testar as funcionalidades.
"""
from horta_organica_agent import agente_sitio_multitrem
from utils import obter_estatisticas, listar_clientes, listar_pedidos
import time


def exemplo_1_duvida_produto():
    """Exemplo 1: Fazer uma pergunta sobre produtos orgânicos."""
    print("\n" + "="*60)
    print("EXEMPLO 1: Dúvida sobre produto orgânico")
    print("="*60)
    
    pergunta = "Quais são os benefícios dos produtos orgânicos?"
    print(f"\n👤 Usuário: {pergunta}\n")
    
    resposta = agente_sitio_multitrem.run(pergunta)
    print(f"🤖 Assistente: {resposta.content}\n")


def exemplo_2_consulta_produtos():
    """Exemplo 2: Consultar produtos disponíveis."""
    print("\n" + "="*60)
    print("EXEMPLO 2: Consulta de produtos")
    print("="*60)
    
    pergunta = "Quais produtos vocês têm disponíveis?"
    print(f"\n👤 Usuário: {pergunta}\n")
    
    resposta = agente_sitio_multitrem.run(
        pergunta,
        session_id="exemplo_2",
        user_id="usuario_teste"
    )
    print(f"🤖 Assistente: {resposta.content}\n")


def exemplo_3_pedido_completo():
    """Exemplo 3: Fazer um pedido completo."""
    print("\n" + "="*60)
    print("EXEMPLO 3: Pedido completo")
    print("="*60)
    
    # Passo 1: Consultar produtos e fazer pedido
    print("\n🛒 Passo 1: Consultar produtos e fazer pedido")
    pergunta1 = "Quero saber mais sobre os produtos"
    print(f"👤 Usuário: {pergunta1}\n")
    
    resposta1 = agente_sitio_multitrem.run(
        pergunta1,
        session_id="exemplo_3",
        user_id="joao_silva"
    )
    print(f"🤖 Assistente: {resposta1.content}\n")
    time.sleep(1)
    
    # Passo 2: Fazer pedido específico
    print("\n🛒 Passo 2: Fazer pedido específico")
    pergunta2 = "Quero comprar 4 alfaces, 2 rúculas e 12 ovos"
    print(f"👤 Usuário: {pergunta2}\n")
    
    resposta2 = agente_sitio_multitrem.run(
        pergunta2,
        session_id="exemplo_3",
        user_id="joao_silva"
    )
    print(f"🤖 Assistente: {resposta2.content}\n")
    time.sleep(1)
    
    # Passo 3: Agendar entrega
    print("\n📅 Passo 3: Agendar entrega")
    pergunta3 = "Quero entregar na segunda-feira. Meu nome é João Silva, email joao@email.com, telefone (11) 99999-9999, endereço Rua das Flores, 123, Bairro Centro, Cidade São Paulo"
    print(f"👤 Usuário: {pergunta3}\n")
    
    resposta3 = agente_sitio_multitrem.run(
        pergunta3,
        session_id="exemplo_3",
        user_id="joao_silva"
    )
    print(f"🤖 Assistente: {resposta3.content}\n")
    time.sleep(1)
    
    # Passo 4: Processar pagamento
    print("\n💳 Passo 4: Processar pagamento")
    pergunta4 = "Quero pagar com PIX"
    print(f"👤 Usuário: {pergunta4}\n")
    
    resposta4 = agente_sitio_multitrem.run(
        pergunta4,
        session_id="exemplo_3",
        user_id="joao_silva"
    )
    print(f"🤖 Assistente: {resposta4.content}\n")


def exemplo_4_suporte():
    """Exemplo 4: Suporte técnico."""
    print("\n" + "="*60)
    print("EXEMPLO 4: Suporte técnico")
    print("="*60)
    
    pergunta = "Como devo armazenar os produtos orgânicos para manter a frescura?"
    print(f"\n👤 Usuário: {pergunta}\n")
    
    resposta = agente_sitio_multitrem.run(
        pergunta,
        session_id="exemplo_4",
        user_id="usuario_teste"
    )
    print(f"🤖 Assistente: {resposta.content}\n")


def exemplo_5_estatisticas():
    """Exemplo 5: Consultar estatísticas do sistema."""
    print("\n" + "="*60)
    print("EXEMPLO 5: Estatísticas do sistema")
    print("="*60)
    
    stats = obter_estatisticas()
    
    print("\n📊 Estatísticas Gerais:")
    print(f"  👥 Total de Clientes: {stats['total_clientes']}")
    print(f"  📦 Total de Pedidos: {stats['total_pedidos']}")
    print(f"  📅 Total de Agendamentos: {stats['total_agendamentos']}")
    print(f"  💳 Total de Pagamentos: {stats['total_pagamentos']}")
    
    print("\n📋 Pedidos por Status:")
    print(f"  ⏳ Pendentes: {stats['pedidos']['pendentes']}")
    print(f"  ✅ Confirmados: {stats['pedidos']['confirmados']}")
    print(f"  🚚 Entregues: {stats['pedidos']['entregues']}")
    
    print(f"\n💰 Valor Total Confirmado: R$ {stats['valor_total_confirmado']:.2f}")
    
    print("\n💳 Pagamentos por Método:")
    print(f"  📱 PIX: {stats['pagamentos']['pix']}")
    print(f"  💳 Cartão: {stats['pagamentos']['cartao']}")
    print(f"  💵 Dinheiro: {stats['pagamentos']['dinheiro']}")


def exemplo_6_listar_dados():
    """Exemplo 6: Listar dados do sistema."""
    print("\n" + "="*60)
    print("EXEMPLO 6: Listar dados")
    print("="*60)
    
    print("\n👥 Clientes Cadastrados:")
    clientes = listar_clientes()
    if clientes:
        for cliente in clientes[:5]:  # Mostrar apenas os 5 primeiros
            print(f"  - {cliente['nome']} ({cliente['email']})")
    else:
        print("  Nenhum cliente cadastrado ainda.")
    
    print("\n📦 Pedidos Recentes:")
    pedidos = listar_pedidos()
    if pedidos:
        for pedido in pedidos[:5]:  # Mostrar apenas os 5 primeiros
            print(f"  - Pedido #{pedido['id']}: R$ {pedido['valor_total']:.2f} - Status: {pedido['status']}")
    else:
        print("  Nenhum pedido realizado ainda.")


def menu_principal():
    """Menu principal para escolher exemplos."""
    print("\n" + "="*60)
    print("🌱 SISTEMA DE AGENTES - HORTA ORGÂNICA")
    print("="*60)
    print("\nEscolha um exemplo para executar:")
    print("  1. Dúvida sobre produto orgânico")
    print("  2. Consulta de produtos disponíveis")
    print("  3. Pedido completo (cadastro + pedido + pagamento + entrega)")
    print("  4. Suporte técnico")
    print("  5. Estatísticas do sistema")
    print("  6. Listar dados cadastrados")
    print("  7. Executar todos os exemplos")
    print("  0. Sair")
    
    escolha = input("\nDigite sua escolha: ").strip()
    
    if escolha == "1":
        exemplo_1_duvida_produto()
    elif escolha == "2":
        exemplo_2_consulta_produtos()
    elif escolha == "3":
        exemplo_3_pedido_completo()
    elif escolha == "4":
        exemplo_4_suporte()
    elif escolha == "5":
        exemplo_5_estatisticas()
    elif escolha == "6":
        exemplo_6_listar_dados()
    elif escolha == "7":
        exemplo_1_duvida_produto()
        exemplo_2_consulta_produtos()
        exemplo_3_pedido_completo()
        exemplo_4_suporte()
        exemplo_5_estatisticas()
        exemplo_6_listar_dados()
    elif escolha == "0":
        print("\n👋 Até logo!")
        return
    else:
        print("\n❌ Opção inválida!")
    
    input("\nPressione Enter para continuar...")
    menu_principal()


if __name__ == "__main__":
    print("\n🌱 Bem-vindo ao Sistema de Exemplos da Horta Orgânica!")
    print("⚠️  Certifique-se de que o sistema está configurado corretamente.")
    print("⚠️  Você precisa ter uma OPENAI_API_KEY configurada no arquivo .env")
    
    resposta = input("\nDeseja continuar? (s/n): ").strip().lower()
    if resposta == "s":
        try:
            menu_principal()
        except KeyboardInterrupt:
            print("\n\n👋 Execução interrompida pelo usuário.")
        except Exception as e:
            print(f"\n❌ Erro durante execução: {str(e)}")
            print("Verifique se o banco de dados está inicializado e a API key está configurada.")
    else:
        print("\n👋 Até logo!")
