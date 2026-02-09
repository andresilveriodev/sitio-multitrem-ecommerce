"""
ResumeDay Repository
"""

from sqlalchemy import desc
from sqlalchemy.exc import SQLAlchemyError
from models.resume_day import ResumeDay


class ResumeDayRepository:
    def __init__(self, session):
        self.session = session

    def add(self, resume_day):
        self.session.add(resume_day)
        self.session.commit()

    def get_all(self):
        return self.session.query(ResumeDay).all()

    def find_by_id(self, id):
        return self.session.query(ResumeDay).filter(ResumeDay.id == id).first()

    def update(self, resume_day, data):
        for key, value in data.items():
            setattr(resume_day, key, value)
        self.session.commit()

    def delete(self, resume_day):
        self.session.delete(resume_day)
        self.session.commit()

    def find_by_symbol(self, symbol):
        return self.session.query(ResumeDay).filter(ResumeDay.symbol == symbol).order_by(desc(ResumeDay.id)).first()

    def exists_by_key(self, key):
        return self.session.query(ResumeDay).filter(ResumeDay.key == key).first() is not None

    def find_by_symbol_and_date_range(self, symbol: str, start_date=None, end_date=None):
        """
        Busca registros de resume_day por símbolo e intervalo de datas
        """
        query = self.session.query(ResumeDay).filter(ResumeDay.symbol == symbol)
        
        if start_date:
            query = query.filter(ResumeDay.data >= start_date)
        if end_date:
            query = query.filter(ResumeDay.data <= end_date)
        
        return query.order_by(desc(ResumeDay.data)).all()

    def find_latest_by_symbol(self, symbol: str, limit: int = 1):
        """
        Busca os últimos registros de um símbolo
        """
        return self.session.query(ResumeDay).filter(
            ResumeDay.symbol == symbol
        ).order_by(desc(ResumeDay.data)).limit(limit).all()




