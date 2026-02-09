"""
Stock model
"""

from datetime import datetime
from sqlalchemy import Column, BigInteger, Boolean, String, Integer, REAL, TIMESTAMP
from database.db import Base


class Stock(Base):
    __tablename__ = 'stock'
    __table_args__ = {'schema': 'mktdata'}

    id = Column(BigInteger, primary_key=True, nullable=False)
    advancedPremium = Column('advanced_premium', Boolean, nullable=True)
    automatic = Column(Boolean, nullable=True)
    corporationName = Column('corporation_name', String(255), nullable=True)
    createdFile = Column('created_file', String(255), nullable=True)
    description = Column(String(255), nullable=True)
    distributionIdentification = Column('distribution_identification', Integer, nullable=True)
    endBusiness = Column('end_business', String(255), nullable=True)
    governanceIndicator = Column('governance_indicator', String(255), nullable=True)
    isin = Column(String(255), nullable=True)
    liquidationInDays = Column('liquidation_in_days', Integer, nullable=True)
    listedMarket = Column('listed_market', String(255), nullable=True)
    market = Column(Integer, nullable=True)
    model = Column(String(255), nullable=True)
    priceFactor = Column('price_factor', Integer, nullable=True)
    productAssociated = Column('product_associated', String(255), nullable=True)
    productDescription = Column('product_description', String(255), nullable=True)
    proprietary = Column(Integer, nullable=True)
    protectionFlag = Column('protection_flag', Boolean, nullable=True)
    referenceStock = Column('reference_stock', BigInteger, nullable=True)
    securityCategory = Column('security_category', Integer, nullable=True)
    segment = Column(Integer, nullable=True)
    specificationCode = Column('specification_code', String(255), nullable=True)
    spreadMedium = Column('spread_medium', REAL, nullable=True)
    spreadMediumBussines = Column('spread_medium_bussines', REAL, nullable=True)
    standardLot = Column('standard_lot', Integer, nullable=True)
    startBusiness = Column('start_business', String(255), nullable=True)
    strike = Column(REAL, nullable=True)
    strikeInitial = Column('strike_initial', REAL, nullable=True)
    symbol = Column(String(255), nullable=True)
    type = Column(String(255), nullable=True)
    updated = Column(TIMESTAMP, nullable=True)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self):
        return f"<Stock(id={self.id}, corporation_name={self.corporationName})>"




