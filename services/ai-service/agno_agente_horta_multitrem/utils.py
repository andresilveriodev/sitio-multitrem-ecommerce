"""
Utilitários para consultas e relatórios do sistema.
"""
from models import Cliente, Pedido, Agendamento, Pagamento, Produto, get_session
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import os

DB_PATH = os.getenv("DATABASE_PATH", "tmp/data.db")


def listar_clientes() -> List[Dict]:
    """Lista todos os clientes cadastrados."""
    session = get_session(DB_PATH)
    try:
        clientes = session.query(Cliente).order_by(Cliente.created_at.desc()).all()
        return [cliente.to_dict() for cliente in clientes]
    finally:
        session.close()


def listar_pedidos(status: Optional[str] = None, cliente_id: Optional[int] = None) -> List[Dict]:
    """Lista pedidos com filtros opcionais."""
    session = get_session(DB_PATH)
    try:
        query = session.query(Pedido)
        
        if status:
            query = query.filter_by(status=status)
        if cliente_id:
            query = query.filter_by(cliente_id=cliente_id)
        
        pedidos = query.order_by(Pedido.created_at.desc()).all()
        return [pedido.to_dict() for pedido in pedidos]
    finally:
        session.close()


def listar_agendamentos(status: Optional[str] = None) -> List[Dict]:
    """Lista agendamentos com filtro opcional."""
    session = get_session(DB_PATH)
    try:
        query = session.query(Agendamento)
        
        if status:
            query = query.filter_by(status=status)
        
        agendamentos = query.order_by(Agendamento.data_entrega, Agendamento.horario).all()
        return [agendamento.to_dict() for agendamento in agendamentos]
    finally:
        session.close()


def listar_pagamentos(status: Optional[str] = None) -> List[Dict]:
    """Lista pagamentos com filtro opcional."""
    session = get_session(DB_PATH)
    try:
        query = session.query(Pagamento)
        
        if status:
            query = query.filter_by(status=status)
        
        pagamentos = query.order_by(Pagamento.created_at.desc()).all()
        return [pagamento.to_dict() for pagamento in pagamentos]
    finally:
        session.close()


def obter_estatisticas() -> Dict:
    """Obtém estatísticas gerais do sistema."""
    session = get_session(DB_PATH)
    try:
        total_clientes = session.query(Cliente).count()
        total_pedidos = session.query(Pedido).count()
        total_agendamentos = session.query(Agendamento).count()
        total_pagamentos = session.query(Pagamento).count()
        
        # Pedidos por status
        pedidos_pendentes = session.query(Pedido).filter_by(status="pendente").count()
        pedidos_confirmados = session.query(Pedido).filter_by(status="confirmado").count()
        pedidos_entregues = session.query(Pedido).filter_by(status="entregue").count()
        
        # Valor total de pedidos
        pedidos_confirmados_obj = session.query(Pedido).filter_by(status="confirmado").all()
        valor_total = sum(pedido.valor_total for pedido in pedidos_confirmados_obj)
        
        # Pagamentos por método
        pagamentos_pix = session.query(Pagamento).filter_by(metodo_pagamento="pix").count()
        pagamentos_cartao = session.query(Pagamento).filter(
            Pagamento.metodo_pagamento.in_(["cartao_credito", "cartao_debito"])
        ).count()
        pagamentos_dinheiro = session.query(Pagamento).filter_by(metodo_pagamento="dinheiro").count()
        
        return {
            "total_clientes": total_clientes,
            "total_pedidos": total_pedidos,
            "total_agendamentos": total_agendamentos,
            "total_pagamentos": total_pagamentos,
            "pedidos": {
                "pendentes": pedidos_pendentes,
                "confirmados": pedidos_confirmados,
                "entregues": pedidos_entregues,
            },
            "valor_total_confirmado": valor_total,
            "pagamentos": {
                "pix": pagamentos_pix,
                "cartao": pagamentos_cartao,
                "dinheiro": pagamentos_dinheiro,
            }
        }
    finally:
        session.close()


def buscar_cliente_por_email(email: str) -> Optional[Dict]:
    """Busca um cliente pelo email."""
    session = get_session(DB_PATH)
    try:
        cliente = session.query(Cliente).filter_by(email=email).first()
        return cliente.to_dict() if cliente else None
    finally:
        session.close()


def buscar_pedidos_por_cliente(cliente_id: int) -> List[Dict]:
    """Busca todos os pedidos de um cliente."""
    session = get_session(DB_PATH)
    try:
        pedidos = session.query(Pedido).filter_by(cliente_id=cliente_id).order_by(Pedido.created_at.desc()).all()
        return [pedido.to_dict() for pedido in pedidos]
    finally:
        session.close()


def atualizar_status_pedido(pedido_id: int, novo_status: str) -> Dict:
    """Atualiza o status de um pedido."""
    session = get_session(DB_PATH)
    try:
        pedido = session.query(Pedido).filter_by(id=pedido_id).first()
        if not pedido:
            return {"success": False, "message": f"Pedido {pedido_id} não encontrado."}
        
        pedido.status = novo_status
        pedido.updated_at = datetime.now()
        session.commit()
        
        return {"success": True, "message": f"Status do pedido {pedido_id} atualizado para {novo_status}", "pedido": pedido.to_dict()}
    except Exception as e:
        session.rollback()
        return {"success": False, "message": f"Erro ao atualizar pedido: {str(e)}"}
    finally:
        session.close()


def atualizar_status_agendamento(agendamento_id: int, novo_status: str) -> Dict:
    """Atualiza o status de um agendamento."""
    session = get_session(DB_PATH)
    try:
        agendamento = session.query(Agendamento).filter_by(id=agendamento_id).first()
        if not agendamento:
            return {"success": False, "message": f"Agendamento {agendamento_id} não encontrado."}
        
        agendamento.status = novo_status
        agendamento.updated_at = datetime.now()
        session.commit()
        
        return {"success": True, "message": f"Status do agendamento {agendamento_id} atualizado para {novo_status}", "agendamento": agendamento.to_dict()}
    except Exception as e:
        session.rollback()
        return {"success": False, "message": f"Erro ao atualizar agendamento: {str(e)}"}
    finally:
        session.close()


def obter_relatorio_vendas(data_inicio: Optional[str] = None, data_fim: Optional[str] = None) -> Dict:
    """Gera relatório de vendas no período especificado."""
    session = get_session(DB_PATH)
    try:
        query = session.query(Pedido).filter_by(status="confirmado")
        
        if data_inicio:
            data_inicio_dt = datetime.strptime(data_inicio, "%Y-%m-%d")
            query = query.filter(Pedido.created_at >= data_inicio_dt)
        
        if data_fim:
            data_fim_dt = datetime.strptime(data_fim, "%Y-%m-%d") + timedelta(days=1)
            query = query.filter(Pedido.created_at < data_fim_dt)
        
        pedidos = query.all()
        
        total_vendas = len(pedidos)
        valor_total = sum(pedido.valor_total for pedido in pedidos)
        
        # Produtos mais vendidos
        produtos_vendidos = {}
        for pedido in pedidos:
            for produto in pedido.produtos:
                nome = produto.get("nome", "Desconhecido")
                quantidade = produto.get("quantidade", 0)
                if nome in produtos_vendidos:
                    produtos_vendidos[nome] += quantidade
                else:
                    produtos_vendidos[nome] = quantidade
        
        produtos_ordenados = sorted(produtos_vendidos.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "periodo": {
                "inicio": data_inicio or "Início",
                "fim": data_fim or "Hoje"
            },
            "total_vendas": total_vendas,
            "valor_total": valor_total,
            "ticket_medio": valor_total / total_vendas if total_vendas > 0 else 0,
            "produtos_mais_vendidos": [{"nome": nome, "quantidade": qtd} for nome, qtd in produtos_ordenados[:10]]
        }
    finally:
        session.close()
