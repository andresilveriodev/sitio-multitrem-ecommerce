"""
Options Service - Consultas de opções
"""

from datetime import date
from sqlalchemy import and_, func
from sqlalchemy.orm import Session
from fastapi import HTTPException
from models.stock import Stock
import calendar


class OptionsService:
    """Serviço para consultas de opções"""

    @staticmethod
    def get_filtered_options(
        session: Session,
        symbol: str,
        type_: str = None,
        models: list = None,
        strike_min: float = None,
        strike_max: float = None,
        vencimentos: list = None
    ):
        """
        Busca opções filtradas por critérios
        """
        # Busca o ativo principal
        stock = session.query(Stock).filter(
            Stock.symbol == symbol,
            Stock.market == 10,
            func.DATE(Stock.endBusiness) > date.today()
        ).order_by(func.DATE(Stock.startBusiness).desc()).first()

        if not stock:
            raise HTTPException(
                status_code=404,
                detail="Ativo principal não encontrado ou não vigente"
            )

        # Filtros para opções
        filters = [
            Stock.referenceStock == stock.id,
            Stock.market.in_([70, 80]),
            func.DATE(Stock.endBusiness) >= date.today()
        ]

        if type_:
            filters.append(Stock.type == type_)
        if models:
            filters.append(Stock.model.in_(models))
        if strike_min is not None:
            filters.append(Stock.strike >= strike_min)
        if strike_max is not None:
            filters.append(Stock.strike <= strike_max)
        if vencimentos:
            filters.append(Stock.endBusiness.in_(vencimentos))

        options = session.query(Stock).filter(and_(*filters)).all()

        if not options:
            raise HTTPException(
                status_code=404,
                detail="Nenhuma opção encontrada"
            )

        return stock, options

    @staticmethod
    def get_options_list(
        session: Session,
        symbol: str,
        type_: str = "CALL",
        models: list = None,
        strike_min: float = None,
        strike_max: float = None,
        vencimentos: list = None
    ):
        """
        Retorna lista de opções
        """
        stock, options = OptionsService.get_filtered_options(
            session, symbol, type_, models, strike_min, strike_max, vencimentos
        )

        return [
            {
                "id": opt.id,
                "symbol": opt.symbol,
                "strike": float(opt.strike) if opt.strike else None,
                "model": opt.model,
                "type": opt.type,
                "endBusiness": opt.endBusiness.strftime("%Y-%m-%d") if opt.endBusiness else None
            }
            for opt in options
        ]

    @staticmethod
    def get_option_map(
        session: Session,
        symbol: str,
        type_: str = None,
        models: list = None,
        strike_min: float = None,
        strike_max: float = None,
        vencimentos: list = None
    ):
        """
        Retorna mapa de opções organizado por strike e vencimento
        """
        stock, options = OptionsService.get_filtered_options(
            session, symbol, type_, models, strike_min, strike_max, vencimentos
        )

        strikes = sorted(set([opt.strike for opt in options if opt.strike]))
        expirations = sorted(set([opt.endBusiness for opt in options if opt.endBusiness]))

        meses = {}
        for exp in expirations:
            key = f"{exp.year}-{exp.month:02}"
            if key not in meses:
                meses[key] = {
                    "month": calendar.month_abbr[exp.month],
                    "year": str(exp.year),
                    "expirations": []
                }
            meses[key]["expirations"].append(exp.strftime("%Y-%m-%d"))

        columns = [meses[key] for key in sorted(meses.keys())]

        matrix = {str(strike): {} for strike in strikes}
        for strike in strikes:
            for exp in expirations:
                matrix[str(strike)][exp.strftime("%Y-%m-%d")] = []

        for opt in options:
            if opt.strike and opt.endBusiness:
                matrix[str(opt.strike)][opt.endBusiness.strftime("%Y-%m-%d")].append({
                    "id": opt.id,
                    "symbol": opt.symbol,
                    "strike": float(opt.strike),
                    "expiration": opt.endBusiness.strftime("%Y-%m-%d"),
                    "model": opt.model,
                    "type": opt.type
                })

        return {
            "strikes": strikes,
            "columns": columns,
            "matrix": matrix
        }

    @staticmethod
    def get_option_board(
        session: Session,
        symbol: str,
        type_: str = None,
        models: list = None,
        strike_min: float = None,
        strike_max: float = None,
        vencimentos: list = None
    ):
        """
        Retorna board de opções agrupado por strike e vencimento
        """
        _, options = OptionsService.get_filtered_options(
            session, symbol, type_, models, strike_min, strike_max, vencimentos
        )

        agrupadas = {}
        for opt in options:
            if opt.strike and opt.endBusiness:
                key = (float(opt.strike), opt.endBusiness.strftime("%Y-%m-%d"))
                if key not in agrupadas:
                    agrupadas[key] = {
                        "strike": opt.strike,
                        "vencimento": opt.endBusiness.strftime("%Y-%m-%d")
                    }

                entrada = agrupadas[key]

                if opt.type == 'CALL':
                    entrada.update({
                        "codigoCall": opt.symbol,
                        "modeloCall": opt.model,
                        "compraCall": None,
                        "volCompraCall": None,
                        "vendaCall": None,
                        "volVendaCall": None
                    })
                elif opt.type == 'PUT':
                    entrada.update({
                        "codigoPut": opt.symbol,
                        "modeloPut": opt.model,
                        "compraPut": None,
                        "volCompraPut": None,
                        "vendaPut": None,
                        "volVendaPut": None
                    })

        return list(agrupadas.values())




