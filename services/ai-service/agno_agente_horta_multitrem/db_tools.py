"""
Tools com persistência real no banco de dados.
"""
from models import (
    Cliente, Pedido, Agendamento, Pagamento, Produto,
    init_db, get_session
)
from datetime import datetime
from typing import Optional, List, Dict
import os


# Inicializar banco de dados
DB_PATH = os.getenv("DATABASE_PATH", "tmp/data.db")
init_db(DB_PATH)


def registrar_cliente(
    nome: str,
    email: str,
    telefone: str,
    endereco: Optional[str] = None
) -> dict:
    """
    Registra um novo cliente no sistema.
    
    Args:
        nome: Nome completo do cliente
        email: Email do cliente
        telefone: Telefone de contato
        endereco: Endereço completo (opcional)
    
    Returns:
        dict: Informações do cliente registrado
    """
    session = get_session(DB_PATH)
    try:
        # Verificar se o email já existe
        cliente_existente = session.query(Cliente).filter_by(email=email).first()
        if cliente_existente:
            return {
                "success": False,
                "message": f"Cliente com email {email} já está cadastrado.",
                "cliente": cliente_existente.to_dict()
            }
        
        # Criar novo cliente
        cliente = Cliente(
            nome=nome,
            email=email,
            telefone=telefone,
            endereco=endereco
        )
        
        session.add(cliente)
        session.commit()
        
        return {
            "success": True,
            "message": f"Cliente {nome} registrado com sucesso!",
            "cliente": cliente.to_dict()
        }
    except Exception as e:
        session.rollback()
        return {
            "success": False,
            "message": f"Erro ao registrar cliente: {str(e)}"
        }
    finally:
        session.close()


def criar_pedido(
    cliente_id: int | str,
    produtos: List[Dict],
    valor_total: float,
    observacoes: Optional[str] = None
) -> dict:
    """
    Cria um novo pedido de produtos orgânicos.
    
    Args:
        cliente_id: ID do cliente
        produtos: Lista de produtos no formato [{"nome": "Tomate", "quantidade": 2, "preco": 15.00}]
        valor_total: Valor total do pedido
        observacoes: Observações adicionais do pedido
    
    Returns:
        dict: Informações do pedido criado
    """
    session = get_session(DB_PATH)
    try:
        # Converter cliente_id para int se for string
        cliente_id_int = int(cliente_id) if isinstance(cliente_id, str) else cliente_id
        
        # Verificar se o cliente existe
        cliente = session.query(Cliente).filter_by(id=cliente_id_int).first()
        if not cliente:
            return {
                "success": False,
                "message": f"Cliente com ID {cliente_id} não encontrado."
            }
        
        # Criar pedido
        pedido = Pedido(
            cliente_id=cliente_id_int,
            produtos=produtos,
            valor_total=valor_total,
            observacoes=observacoes,
            status="pendente"
        )
        
        session.add(pedido)
        session.commit()
        
        return {
            "success": True,
            "message": "Pedido criado com sucesso!",
            "pedido": pedido.to_dict()
        }
    except Exception as e:
        session.rollback()
        return {
            "success": False,
            "message": f"Erro ao criar pedido: {str(e)}"
        }
    finally:
        session.close()


def agendar_entrega(
    pedido_id: int | str,
    data_entrega: str,
    horario: str,
    endereco_entrega: str
) -> dict:
    """
    Agenda uma entrega de produtos orgânicos.
    
    Args:
        pedido_id: ID do pedido
        data_entrega: Data da entrega (formato: YYYY-MM-DD)
        horario: Horário da entrega (formato: HH:MM)
        endereco_entrega: Endereço completo para entrega
    
    Returns:
        dict: Informações do agendamento
    """
    session = get_session(DB_PATH)
    try:
        # Converter pedido_id para int se for string
        pedido_id_int = int(pedido_id) if isinstance(pedido_id, str) else pedido_id
        
        # Verificar se o pedido existe
        pedido = session.query(Pedido).filter_by(id=pedido_id_int).first()
        if not pedido:
            return {
                "success": False,
                "message": f"Pedido com ID {pedido_id_int} não encontrado."
            }
        
        # Criar agendamento
        agendamento = Agendamento(
            pedido_id=pedido_id_int,
            data_entrega=data_entrega,
            horario=horario,
            endereco_entrega=endereco_entrega,
            status="agendado"
        )
        
        session.add(agendamento)
        session.commit()
        
        return {
            "success": True,
            "message": f"Entrega agendada para {data_entrega} às {horario}",
            "agendamento": agendamento.to_dict()
        }
    except Exception as e:
        session.rollback()
        return {
            "success": False,
            "message": f"Erro ao agendar entrega: {str(e)}"
        }
    finally:
        session.close()


def processar_pagamento(
    pedido_id: int | str,
    metodo_pagamento: str,
    valor: float,
    dados_pagamento: Optional[dict] = None
) -> dict:
    """
    Processa o pagamento de um pedido.
    
    Args:
        pedido_id: ID do pedido
        metodo_pagamento: Método de pagamento (pix, cartao_credito, cartao_debito, dinheiro)
        valor: Valor a ser pago
        dados_pagamento: Dados adicionais do pagamento (opcional)
    
    Returns:
        dict: Informações do pagamento processado
    """
    session = get_session(DB_PATH)
    try:
        # Converter pedido_id para int se for string
        pedido_id_int = int(pedido_id) if isinstance(pedido_id, str) else pedido_id
        
        # Verificar se o pedido existe
        pedido = session.query(Pedido).filter_by(id=pedido_id_int).first()
        if not pedido:
            return {
                "success": False,
                "message": f"Pedido com ID {pedido_id_int} não encontrado."
            }
        
        # Validar método de pagamento
        metodos_validos = ["pix", "cartao_credito", "cartao_debito", "dinheiro"]
        if metodo_pagamento.lower() not in metodos_validos:
            return {
                "success": False,
                "message": f"Método de pagamento inválido. Use: {', '.join(metodos_validos)}"
            }
        
        # Criar pagamento
        pagamento = Pagamento(
            pedido_id=pedido_id_int,
            metodo_pagamento=metodo_pagamento.lower(),
            valor=valor,
            dados_pagamento=dados_pagamento,
            status="processado"
        )
        
        session.add(pagamento)
        session.commit()
        
        return {
            "success": True,
            "message": f"Pagamento de R$ {valor:.2f} processado com sucesso via {metodo_pagamento}",
            "pagamento": pagamento.to_dict()
        }
    except Exception as e:
        session.rollback()
        return {
            "success": False,
            "message": f"Erro ao processar pagamento: {str(e)}"
        }
    finally:
        session.close()


def consultar_produtos_disponiveis(categoria: Optional[str] = None) -> dict:
    """
    Consulta os produtos orgânicos disponíveis na horta.
    
    Args:
        categoria: Categoria de produtos (legumes, frutas, verduras, ervas) - opcional
    
    Returns:
        dict: Lista de produtos disponíveis
    """
    session = get_session(DB_PATH)
    try:
        query = session.query(Produto).filter_by(disponivel="True")
        
        if categoria:
            query = query.filter_by(categoria=categoria.lower())
        
        produtos = query.all()
        
        if not produtos:
            # Se não houver produtos no banco, retornar produtos padrão
            return _get_produtos_padrao(categoria)
        
        produtos_dict = {}
        for produto in produtos:
            cat = produto.categoria
            if cat not in produtos_dict:
                produtos_dict[cat] = []
            produtos_dict[cat].append(produto.to_dict())
        
        if categoria:
            return {
                "success": True,
                "categoria": categoria,
                "produtos": produtos_dict.get(categoria.lower(), [])
            }
        
        return {
            "success": True,
            "produtos": produtos_dict
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Erro ao consultar produtos: {str(e)}",
            "produtos": _get_produtos_padrao(categoria)
        }
    finally:
        session.close()


def consultar_pedido(pedido_id: int | str) -> dict:
    """
    Consulta informações de um pedido específico.
    
    Args:
        pedido_id: ID do pedido
    
    Returns:
        dict: Informações do pedido
    """
    session = get_session(DB_PATH)
    try:
        # Converter pedido_id para int se for string
        pedido_id_int = int(pedido_id) if isinstance(pedido_id, str) else pedido_id
        
        pedido = session.query(Pedido).filter_by(id=pedido_id_int).first()
        
        if not pedido:
            return {
                "success": False,
                "message": f"Pedido com ID {pedido_id_int} não encontrado."
            }
        
        # Buscar informações relacionadas
        cliente = session.query(Cliente).filter_by(id=pedido.cliente_id).first()
        agendamento = session.query(Agendamento).filter_by(pedido_id=pedido_id_int).first()
        pagamento = session.query(Pagamento).filter_by(pedido_id=pedido_id_int).first()
        
        resultado = {
            "success": True,
            "pedido": pedido.to_dict(),
            "cliente": cliente.to_dict() if cliente else None,
            "agendamento": agendamento.to_dict() if agendamento else None,
            "pagamento": pagamento.to_dict() if pagamento else None,
        }
        
        return resultado
    except Exception as e:
        return {
            "success": False,
            "message": f"Erro ao consultar pedido: {str(e)}"
        }
    finally:
        session.close()


def _get_produtos_padrao(categoria: Optional[str] = None) -> dict:
    """Retorna produtos padrão caso o banco esteja vazio."""
    produtos = {
        "legumes": [
            {"nome": "Tomate Orgânico", "preco": 15.00, "unidade": "kg", "disponivel": True},
            {"nome": "Cenoura Orgânica", "preco": 12.00, "unidade": "kg", "disponivel": True},
            {"nome": "Beterraba Orgânica", "preco": 10.00, "unidade": "kg", "disponivel": True},
            {"nome": "Abobrinha Orgânica", "preco": 8.00, "unidade": "kg", "disponivel": True},
            {"nome": "Pepino Orgânico", "preco": 7.00, "unidade": "kg", "disponivel": True},
        ],
        "frutas": [
            {"nome": "Morango Orgânico", "preco": 25.00, "unidade": "bandeja", "disponivel": True},
            {"nome": "Banana Orgânica", "preco": 8.00, "unidade": "kg", "disponivel": True},
            {"nome": "Mamão Orgânico", "preco": 12.00, "unidade": "unidade", "disponivel": True},
            {"nome": "Limão Orgânico", "preco": 6.00, "unidade": "kg", "disponivel": True},
        ],
        "verduras": [
            {"nome": "Alface Orgânica", "preco": 6.00, "unidade": "unidade", "disponivel": True},
            {"nome": "Rúcula Orgânica", "preco": 7.00, "unidade": "maço", "disponivel": True},
            {"nome": "Espinafre Orgânico", "preco": 8.00, "unidade": "maço", "disponivel": True},
            {"nome": "Couve Orgânica", "preco": 5.00, "unidade": "maço", "disponivel": True},
            {"nome": "Repolho Orgânico", "preco": 9.00, "unidade": "unidade", "disponivel": True},
        ],
        "ervas": [
            {"nome": "Manjericão Orgânico", "preco": 5.00, "unidade": "vaso", "disponivel": True},
            {"nome": "Salsinha Orgânica", "preco": 4.00, "unidade": "maço", "disponivel": True},
            {"nome": "Cebolinha Orgânica", "preco": 4.00, "unidade": "maço", "disponivel": True},
            {"nome": "Coentro Orgânico", "preco": 4.50, "unidade": "maço", "disponivel": True},
            {"nome": "Hortelã Orgânica", "preco": 5.50, "unidade": "vaso", "disponivel": True},
        ]
    }
    
    if categoria and categoria.lower() in produtos:
        return {
            "success": True,
            "categoria": categoria,
            "produtos": produtos[categoria.lower()]
        }
    
    return {
        "success": True,
        "produtos": produtos
    }


def popular_produtos_iniciais():
    """Popula o banco de dados com produtos iniciais."""
    session = get_session(DB_PATH)
    try:
        # Verificar se já existem produtos
        if session.query(Produto).count() > 0:
            return {"success": True, "message": "Produtos já existem no banco."}
        
        produtos_iniciais = [
            # Legumes
            Produto(nome="Tomate Orgânico", categoria="legumes", preco=15.00, unidade="kg", disponivel="True"),
            Produto(nome="Cenoura Orgânica", categoria="legumes", preco=12.00, unidade="kg", disponivel="True"),
            Produto(nome="Beterraba Orgânica", categoria="legumes", preco=10.00, unidade="kg", disponivel="True"),
            Produto(nome="Abobrinha Orgânica", categoria="legumes", preco=8.00, unidade="kg", disponivel="True"),
            Produto(nome="Pepino Orgânico", categoria="legumes", preco=7.00, unidade="kg", disponivel="True"),
            
            # Frutas
            Produto(nome="Morango Orgânico", categoria="frutas", preco=25.00, unidade="bandeja", disponivel="True"),
            Produto(nome="Banana Orgânica", categoria="frutas", preco=8.00, unidade="kg", disponivel="True"),
            Produto(nome="Mamão Orgânico", categoria="frutas", preco=12.00, unidade="unidade", disponivel="True"),
            Produto(nome="Limão Orgânico", categoria="frutas", preco=6.00, unidade="kg", disponivel="True"),
            
            # Verduras
            Produto(nome="Alface Orgânica", categoria="verduras", preco=6.00, unidade="unidade", disponivel="True"),
            Produto(nome="Rúcula Orgânica", categoria="verduras", preco=7.00, unidade="maço", disponivel="True"),
            Produto(nome="Espinafre Orgânico", categoria="verduras", preco=8.00, unidade="maço", disponivel="True"),
            Produto(nome="Couve Orgânica", categoria="verduras", preco=5.00, unidade="maço", disponivel="True"),
            Produto(nome="Repolho Orgânico", categoria="verduras", preco=9.00, unidade="unidade", disponivel="True"),
            
            # Ervas
            Produto(nome="Manjericão Orgânico", categoria="ervas", preco=5.00, unidade="vaso", disponivel="True"),
            Produto(nome="Salsinha Orgânica", categoria="ervas", preco=4.00, unidade="maço", disponivel="True"),
            Produto(nome="Cebolinha Orgânica", categoria="ervas", preco=4.00, unidade="maço", disponivel="True"),
            Produto(nome="Coentro Orgânico", categoria="ervas", preco=4.50, unidade="maço", disponivel="True"),
            Produto(nome="Hortelã Orgânica", categoria="ervas", preco=5.50, unidade="vaso", disponivel="True"),
        ]
        
        for produto in produtos_iniciais:
            session.add(produto)
        
        session.commit()
        return {"success": True, "message": f"{len(produtos_iniciais)} produtos adicionados ao banco."}
    except Exception as e:
        session.rollback()
        return {"success": False, "message": f"Erro ao popular produtos: {str(e)}"}
    finally:
        session.close()
