"""
Stock Repository
"""

from datetime import datetime
from sqlalchemy import desc, text
from models.stock import Stock


class StockRepository:
    def __init__(self, session):
        self.session = session

    def add(self, stock):
        self.session.add(stock)
        self.session.commit()

    def add_multiple(self, stocks):
        self.session.add_all(stocks)
        self.session.commit()

    def get_all(self):
        return self.session.query(Stock).all()

    def find_by_id(self, id):
        return self.session.query(Stock).filter(Stock.id == id).first()

    def find_by_symbol(self, symbol):
        return self.session.query(Stock).filter(Stock.symbol == symbol).order_by(desc(Stock.id)).first()

    def update(self, stock, updates):
        for key, value in updates.items():
            setattr(stock, key, value)
        self.session.commit()

    def delete(self, stock):
        self.session.delete(stock)
        self.session.commit()

    def get_active_stocks_by_date(self, data_str):
        data = datetime.strptime(data_str, "%Y-%m-%d")
        sql = text("""
            SELECT symbol, id
            FROM mktdata.stock
            WHERE (end_business IS NULL OR end_business > :data)
              AND symbol IS NOT NULL
        """)
        result = self.session.execute(sql, {"data": data})
        return {
            (row.symbol or '').strip().upper(): row.id
            for row in result
            if row.symbol
        }




