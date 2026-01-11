"""
Tools com persistência real no banco de dados.
"""
from models import (
    Cliente, Pedido, Agendamento, Pagamento, Produto,
    init_db, get_session
)
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import os


# Inicializar banco de dados
DB_PATH = os.getenv("DATABASE_PATH", "tmp/data.db")
init_db(DB_PATH)


def registrar_cliente(
    nome: str,
    email: str,
    telefone: Optional[str] = None,
    endereco: Optional[str] = None
) -> dict:
    """
    Registra um novo cliente no sistema.
    ⚠️ Telefone é opcional pois pode ser obtido do WhatsApp automaticamente.
    
    Args:
        nome: Nome completo do cliente
        email: Email do cliente
        telefone: Telefone de contato (opcional - será preenchido do WhatsApp se não fornecido)
        endereco: Endereço completo (opcional)
    
    Returns:
        dict: Informações do cliente registrado
    """
    session = get_session(DB_PATH)
    try:
        # Verificar se o email já existe
        cliente_existente = session.query(Cliente).filter_by(email=email).first()
        if cliente_existente:
            # Retornar cliente existente (não é erro, apenas informação)
            return {
                "success": True,
                "message": f"Cliente com email {email} já está cadastrado.",
                "cliente": cliente_existente.to_dict(),
                "ja_cadastrado": True
            }
        
        # Se telefone não fornecido, usar placeholder (será atualizado depois com dados do WhatsApp)
        if not telefone:
            telefone = "A definir"  # Placeholder - será atualizado quando tiver acesso ao telefone do WhatsApp
        
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
    Processa o pagamento de um pedido via PIX.
    
    ⚠️ IMPORTANTE: Aceitamos apenas PIX no momento.
    Esta função deve ser chamada APENAS após receber o comprovante do cliente.
    
    Args:
        pedido_id: ID do pedido
        metodo_pagamento: Método de pagamento (deve ser 'pix')
        valor: Valor a ser pago
        dados_pagamento: Dados adicionais do pagamento (opcional, pode incluir {'comprovante_recebido': True})
    
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
        
        # Validar método de pagamento (apenas PIX aceito no momento)
        metodo_lower = metodo_pagamento.lower()
        if metodo_lower != "pix":
            return {
                "success": False,
                "message": f"Método de pagamento '{metodo_pagamento}' não disponível. Aceitamos apenas PIX no momento."
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


def buscar_cliente_por_email(email: str) -> dict:
    """
    Busca um cliente cadastrado pelo email.
    
    Args:
        email: Email do cliente
    
    Returns:
        dict: Informações do cliente se encontrado, None caso contrário
    """
    session = get_session(DB_PATH)
    try:
        cliente = session.query(Cliente).filter_by(email=email).first()
        if cliente:
            return {
                "success": True,
                "cliente": cliente.to_dict(),
                "message": f"Cliente encontrado: {cliente.nome}"
            }
        else:
            return {
                "success": False,
                "message": f"Cliente com email {email} não encontrado.",
                "cliente": None
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Erro ao buscar cliente: {str(e)}",
            "cliente": None
        }
    finally:
        session.close()


def extrair_telefone_do_user_id(user_id: str) -> str:
    """
    Extrai o número de telefone do user_id do WhatsApp.
    Formato esperado: 'whatsapp_5562981062311' ou '5562981062311'
    
    Args:
        user_id: ID do usuário do WhatsApp
    
    Returns:
        str: Número de telefone normalizado (sem prefixo whatsapp_)
    """
    # Remover prefixo "whatsapp_" se existir
    telefone = user_id.replace('whatsapp_', '')
    return telefone


def buscar_cliente_por_telefone(telefone: str) -> dict:
    """
    Busca um cliente cadastrado pelo telefone.
    Normaliza diferentes formatos de telefone para busca.
    
    Args:
        telefone: Telefone do cliente (pode vir em vários formatos)
                  Exemplos: "5562981062311", "+55 62 981062311", "whatsapp_5562981062311", etc.
    
    Returns:
        dict: Informações do cliente se encontrado
    """
    session = get_session(DB_PATH)
    try:
        # Normalizar telefone: remover espaços, +, -, (, ), e caracteres especiais
        telefone_normalizado = telefone.replace(' ', '').replace('+', '').replace('-', '').replace('(', '').replace(')', '').replace('@s.whatsapp.net', '')
        
        # Remover prefixo "whatsapp_" se existir (do user_id)
        if telefone_normalizado.startswith('whatsapp_'):
            telefone_normalizado = telefone_normalizado.replace('whatsapp_', '')
        
        # Buscar no banco (pode estar em diferentes formatos)
        # Tentar busca exata primeiro
        cliente = session.query(Cliente).filter_by(telefone=telefone_normalizado).first()
        
        if not cliente:
            # Tentar busca parcial (caso tenha formatação diferente)
            # Buscar telefones que contenham os últimos 9 dígitos (sem DDD)
            if len(telefone_normalizado) >= 9:
                ultimos_digitos = telefone_normalizado[-9:]  # Últimos 9 dígitos
                clientes = session.query(Cliente).filter(Cliente.telefone.like(f'%{ultimos_digitos}')).all()
                if clientes:
                    cliente = clientes[0]  # Pegar o primeiro encontrado
        
        if cliente:
            return {
                "success": True,
                "cliente": cliente.to_dict(),
                "message": f"Cliente encontrado: {cliente.nome}"
            }
        else:
            return {
                "success": False,
                "message": f"Cliente com telefone {telefone} não encontrado.",
                "cliente": None
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Erro ao buscar cliente: {str(e)}",
            "cliente": None
        }
    finally:
        session.close()


def buscar_cliente_por_nome_email(nome: str, email: str) -> dict:
    """
    Busca um cliente cadastrado pelo nome e email.
    Usado quando cliente fornece nome e email para verificar cadastro.
    
    Args:
        nome: Nome completo do cliente
        email: Email do cliente
    
    Returns:
        dict: Informações do cliente se encontrado
    """
    session = get_session(DB_PATH)
    try:
        # Buscar por email (mais confiável e único)
        cliente = session.query(Cliente).filter_by(email=email).first()
        
        if cliente:
            # Verificar se o nome corresponde (case insensitive, removendo espaços extras)
            nome_cadastrado = cliente.nome.lower().strip()
            nome_fornecido = nome.lower().strip()
            
            if nome_cadastrado == nome_fornecido:
                return {
                    "success": True,
                    "cliente": cliente.to_dict(),
                    "message": f"Cliente encontrado: {cliente.nome}",
                    "nome_confere": True
                }
            else:
                # Email existe mas nome diferente - retornar mesmo assim (pode ser apelido)
                return {
                    "success": True,
                    "cliente": cliente.to_dict(),
                    "message": f"Cliente encontrado pelo email. Nome cadastrado: {cliente.nome}",
                    "nome_confere": False,
                    "nome_diferente": True
                }
        else:
            return {
                "success": False,
                "message": f"Cliente com email {email} não encontrado.",
                "cliente": None
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Erro ao buscar cliente: {str(e)}",
            "cliente": None
        }
    finally:
        session.close()


def atualizar_cliente(
    cliente_id: int | str,
    nome: Optional[str] = None,
    email: Optional[str] = None,
    telefone: Optional[str] = None,
    endereco: Optional[str] = None
) -> dict:
    """
    Atualiza dados de um cliente existente.
    
    Args:
        cliente_id: ID do cliente
        nome: Novo nome (opcional)
        email: Novo email (opcional)
        telefone: Novo telefone (opcional)
        endereco: Novo endereço (opcional)
    
    Returns:
        dict: Informações do cliente atualizado
    """
    session = get_session(DB_PATH)
    try:
        cliente_id_int = int(cliente_id) if isinstance(cliente_id, str) else cliente_id
        cliente = session.query(Cliente).filter_by(id=cliente_id_int).first()
        
        if not cliente:
            return {
                "success": False,
                "message": f"Cliente com ID {cliente_id_int} não encontrado."
            }
        
        # Atualizar apenas campos fornecidos
        if nome:
            cliente.nome = nome
        if email:
            cliente.email = email
        if telefone:
            cliente.telefone = telefone
        if endereco:
            cliente.endereco = endereco
        
        cliente.updated_at = datetime.now()
        session.commit()
        
        return {
            "success": True,
            "message": f"Dados do cliente {cliente.nome} atualizados com sucesso!",
            "cliente": cliente.to_dict()
        }
    except Exception as e:
        session.rollback()
        return {
            "success": False,
            "message": f"Erro ao atualizar cliente: {str(e)}"
        }
    finally:
        session.close()


def obter_datas_disponiveis_entrega(numero_semanas: int = 2) -> dict:
    """
    Calcula as próximas datas disponíveis para entrega.
    Dias disponíveis: Segunda, Quarta, Sexta e Sábado (manhã).
    Sempre começa do próximo dia disponível (não inclui o dia atual).
    
    Args:
        numero_semanas: Número de semanas à frente para calcular (padrão: 2)
    
    Returns:
        dict: Lista de datas disponíveis formatadas
    """
    try:
        # Data atual (apenas data, sem hora)
        hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Dias da semana disponíveis (0=Segunda, 2=Quarta, 4=Sexta, 5=Sábado)
        dias_disponiveis = [0, 2, 4, 5]  # Segunda, Quarta, Sexta, Sábado
        nomes_dias = {
            0: "Segunda-feira",
            2: "Quarta-feira", 
            4: "Sexta-feira",
            5: "Sábado"
        }
        
        datas_formatadas = []
        # Começar do próximo dia (não incluir hoje)
        data_atual = hoje + timedelta(days=1)
        
        # Calcular próximas datas disponíveis (máximo 2 semanas = 14 dias)
        max_dias = numero_semanas * 7
        dias_verificados = 0
        
        while len(datas_formatadas) < max_dias and dias_verificados < max_dias * 2:
            dia_semana = data_atual.weekday()
            
            if dia_semana in dias_disponiveis:
                # Formato: DD/MM/YYYY - Nome do dia
                data_str = data_atual.strftime("%d/%m/%Y")
                nome_dia = nomes_dias[dia_semana]
                data_iso = data_atual.strftime("%Y-%m-%d")  # Para uso no banco
                
                datas_formatadas.append({
                    "data": data_str,
                    "data_iso": data_iso,
                    "dia_semana": nome_dia,
                    "horario": "manhã"
                })
            
            data_atual += timedelta(days=1)
            dias_verificados += 1
        
        return {
            "success": True,
            "datas": datas_formatadas,
            "total": len(datas_formatadas),
            "message": f"Encontradas {len(datas_formatadas)} datas disponíveis para as próximas {numero_semanas} semanas"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Erro ao calcular datas disponíveis: {str(e)}",
            "datas": []
        }


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


def buscar_pedidos_por_telefone(telefone: str) -> dict:
    """
    Busca todos os pedidos de um cliente pelo telefone.
    Primeiro busca o cliente pelo telefone, depois busca seus pedidos.
    
    Args:
        telefone: Telefone do cliente (pode vir em vários formatos)
    
    Returns:
        dict: Lista de pedidos do cliente se encontrado
    """
    session = get_session(DB_PATH)
    try:
        # Normalizar telefone
        telefone_normalizado = telefone.replace(' ', '').replace('+', '').replace('-', '').replace('(', '').replace(')', '').replace('@s.whatsapp.net', '')
        if telefone_normalizado.startswith('whatsapp_'):
            telefone_normalizado = telefone_normalizado.replace('whatsapp_', '')
        
        # Buscar cliente pelo telefone
        cliente = session.query(Cliente).filter_by(telefone=telefone_normalizado).first()
        
        if not cliente:
            # Tentar busca parcial
            if len(telefone_normalizado) >= 9:
                ultimos_digitos = telefone_normalizado[-9:]
                clientes = session.query(Cliente).filter(Cliente.telefone.like(f'%{ultimos_digitos}')).all()
                if clientes:
                    cliente = clientes[0]
        
        if not cliente:
            return {
                "success": False,
                "message": f"Cliente com telefone {telefone} não encontrado.",
                "pedidos": []
            }
        
        # Buscar pedidos do cliente
        pedidos = session.query(Pedido).filter_by(cliente_id=cliente.id).order_by(Pedido.created_at.desc()).all()
        
        # Buscar agendamentos para cada pedido
        pedidos_com_agendamentos = []
        for pedido in pedidos:
            pedido_dict = pedido.to_dict()
            agendamento = session.query(Agendamento).filter_by(pedido_id=pedido.id).first()
            if agendamento:
                pedido_dict["agendamento"] = agendamento.to_dict()
            else:
                pedido_dict["agendamento"] = None
            pedidos_com_agendamentos.append(pedido_dict)
        
        return {
            "success": True,
            "cliente": cliente.to_dict(),
            "pedidos": pedidos_com_agendamentos,
            "total": len(pedidos),
            "message": f"Encontrados {len(pedidos)} pedido(s) para o cliente {cliente.nome}"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Erro ao buscar pedidos: {str(e)}",
            "pedidos": []
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
