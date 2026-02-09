"""
ResumeDay model
"""

from sqlalchemy import Column, Integer, String, ForeignKey, BigInteger, Float, Date, PrimaryKeyConstraint, Identity
from database.db import Base


class ResumeDay(Base):
    __tablename__ = 'resume_day'
    __table_args__ = (
        PrimaryKeyConstraint('key', 'data'),
        {'schema': 'mktdata'}
    )

    id = Column(BigInteger, Identity(always=True), primary_key=False)  # Auxiliar, não é PK

    key = Column(String(255))  # PK => Exemplo: "PETR4.2025-03-27"
    data = Column(Date, nullable=False)
    symbol = Column(String(20), nullable=False, index=True)
    abertura = Column(Float)
    ajuste = Column(Float)
    contratos_abertos = Column(Integer)
    maximo = Column(Float)
    medio = Column(Float)
    minimo = Column(Float)
    negocios_after = Column(Integer)
    negocios_regular = Column(Integer)
    oscilacao = Column(Float)
    prazo = Column(Integer)
    preco_historico = Column(Float)
    qtde_after = Column(Integer)
    qtde_regular = Column(Integer)
    qtde_total = Column(Integer)
    total_negocios = Column(Integer)
    ultimo = Column(Float)
    volume_after = Column(Float)
    volume_regular = Column(Float)
    volume_total = Column(Float)
    stock_fk = Column(BigInteger, ForeignKey('mktdata.stock.id'), nullable=False)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}




