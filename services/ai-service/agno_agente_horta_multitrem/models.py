"""
Modelos de banco de dados para o sistema de horta orgânica.
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from typing import Optional

Base = declarative_base()


class Cliente(Base):
    """Modelo para clientes da horta orgânica."""
    __tablename__ = 'clientes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(200), nullable=False)
    email = Column(String(200), unique=True, nullable=False)
    telefone = Column(String(20), nullable=False)
    endereco = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self):
        """Converte o objeto para dicionário."""
        return {
            "id": self.id,
            "nome": self.nome,
            "email": self.email,
            "telefone": self.telefone,
            "endereco": self.endereco,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Pedido(Base):
    """Modelo para pedidos de produtos orgânicos."""
    __tablename__ = 'pedidos'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    cliente_id = Column(Integer, nullable=False)
    produtos = Column(JSON, nullable=False)  # Lista de produtos
    valor_total = Column(Float, nullable=False)
    observacoes = Column(Text, nullable=True)
    status = Column(String(50), default="pendente")  # pendente, confirmado, cancelado, entregue
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self):
        """Converte o objeto para dicionário."""
        return {
            "id": self.id,
            "cliente_id": self.cliente_id,
            "produtos": self.produtos,
            "valor_total": self.valor_total,
            "observacoes": self.observacoes,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Agendamento(Base):
    """Modelo para agendamentos de entrega."""
    __tablename__ = 'agendamentos'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pedido_id = Column(Integer, nullable=False)
    data_entrega = Column(String(10), nullable=False)  # YYYY-MM-DD
    horario = Column(String(5), nullable=False)  # HH:MM
    endereco_entrega = Column(Text, nullable=False)
    status = Column(String(50), default="agendado")  # agendado, confirmado, entregue, cancelado
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self):
        """Converte o objeto para dicionário."""
        return {
            "id": self.id,
            "pedido_id": self.pedido_id,
            "data_entrega": self.data_entrega,
            "horario": self.horario,
            "endereco_entrega": self.endereco_entrega,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Pagamento(Base):
    """Modelo para pagamentos de pedidos."""
    __tablename__ = 'pagamentos'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pedido_id = Column(Integer, nullable=False)
    metodo_pagamento = Column(String(50), nullable=False)  # pix, cartao_credito, cartao_debito, dinheiro
    valor = Column(Float, nullable=False)
    status = Column(String(50), default="processado")  # processado, confirmado, cancelado, reembolsado
    dados_pagamento = Column(JSON, nullable=True)  # Dados adicionais do pagamento
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self):
        """Converte o objeto para dicionário."""
        return {
            "id": self.id,
            "pedido_id": self.pedido_id,
            "metodo_pagamento": self.metodo_pagamento,
            "valor": self.valor,
            "status": self.status,
            "dados_pagamento": self.dados_pagamento,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Produto(Base):
    """Modelo para produtos orgânicos disponíveis."""
    __tablename__ = 'produtos'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(200), nullable=False, unique=True)
    categoria = Column(String(50), nullable=False)  # legumes, frutas, verduras, ervas
    preco = Column(Float, nullable=False)
    unidade = Column(String(20), nullable=False)  # kg, unidade, maço, vaso, bandeja
    disponivel = Column(String(10), default="True")  # True, False
    descricao = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self):
        """Converte o objeto para dicionário."""
        return {
            "id": self.id,
            "nome": self.nome,
            "categoria": self.categoria,
            "preco": self.preco,
            "unidade": self.unidade,
            "disponivel": self.disponivel == "True",
            "descricao": self.descricao,
        }


# Função para criar o engine e as tabelas
def init_db(db_path: str = "tmp/data.db"):
    """
    Inicializa o banco de dados criando todas as tabelas.
    
    Args:
        db_path: Caminho para o arquivo do banco de dados
    """
    # Criar diretório se não existir
    import os
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    engine = create_engine(f'sqlite:///{db_path}', echo=False)
    Base.metadata.create_all(engine)
    return engine


def get_session(db_path: str = "tmp/data.db"):
    """
    Cria uma sessão do banco de dados.
    
    Args:
        db_path: Caminho para o arquivo do banco de dados
    
    Returns:
        Session: Sessão do SQLAlchemy
    """
    engine = create_engine(f'sqlite:///{db_path}', echo=False)
    Session = sessionmaker(bind=engine)
    return Session()
