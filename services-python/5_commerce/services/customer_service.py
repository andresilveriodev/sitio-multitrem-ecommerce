"""
Serviço de clientes
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
import structlog

from models.commerce import Customer, CustomerAddress
from schemas.customer import CustomerCreate, CustomerUpdate, CustomerAddressCreate, CustomerAddressUpdate

logger = structlog.get_logger()


class CustomerService:
    """Serviço para gerenciar clientes e endereços"""
    
    @staticmethod
    def get_customers(db: Session, skip: int = 0, limit: int = 100, search: Optional[str] = None) -> List[Customer]:
        """Lista clientes"""
        query = db.query(Customer)
        
        if search:
            query = query.filter(
                or_(
                    Customer.name.ilike(f"%{search}%"),
                    Customer.phone_e164.ilike(f"%{search}%"),
                    Customer.document.ilike(f"%{search}%")
                )
            )
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def get_customer(db: Session, customer_id: int) -> Optional[Customer]:
        """Busca um cliente por ID"""
        return db.query(Customer).filter(Customer.id == customer_id).first()
    
    @staticmethod
    def get_customer_by_phone(db: Session, phone_e164: str) -> Optional[Customer]:
        """Busca um cliente por telefone"""
        return db.query(Customer).filter(Customer.phone_e164 == phone_e164).first()
    
    @staticmethod
    def create_customer(db: Session, customer: CustomerCreate) -> Customer:
        """Cria um novo cliente"""
        db_customer = Customer(**customer.model_dump())
        db.add(db_customer)
        db.commit()
        db.refresh(db_customer)
        logger.info("Cliente criado", customer_id=db_customer.id, phone=customer.phone_e164)
        return db_customer
    
    @staticmethod
    def update_customer(db: Session, customer_id: int, customer: CustomerUpdate) -> Optional[Customer]:
        """Atualiza um cliente"""
        db_customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not db_customer:
            return None
        
        update_data = customer.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_customer, field, value)
        
        db.commit()
        db.refresh(db_customer)
        logger.info("Cliente atualizado", customer_id=customer_id)
        return db_customer
    
    @staticmethod
    def get_customer_addresses(db: Session, customer_id: int) -> List[CustomerAddress]:
        """Lista endereços de um cliente"""
        return db.query(CustomerAddress).filter(CustomerAddress.customer_id == customer_id).all()
    
    @staticmethod
    def get_customer_address(db: Session, address_id: int) -> Optional[CustomerAddress]:
        """Busca um endereço por ID"""
        return db.query(CustomerAddress).filter(CustomerAddress.id == address_id).first()
    
    @staticmethod
    def create_customer_address(db: Session, address: CustomerAddressCreate) -> CustomerAddress:
        """Cria um novo endereço"""
        # Se for marcado como default, remove default dos outros endereços
        if address.is_default:
            db.query(CustomerAddress).filter(
                CustomerAddress.customer_id == address.customer_id
            ).update({"is_default": False})
        
        db_address = CustomerAddress(**address.model_dump())
        db.add(db_address)
        db.commit()
        db.refresh(db_address)
        logger.info("Endereço criado", address_id=db_address.id, customer_id=address.customer_id)
        return db_address
    
    @staticmethod
    def update_customer_address(db: Session, address_id: int, address: CustomerAddressUpdate) -> Optional[CustomerAddress]:
        """Atualiza um endereço"""
        db_address = db.query(CustomerAddress).filter(CustomerAddress.id == address_id).first()
        if not db_address:
            return None
        
        update_data = address.model_dump(exclude_unset=True)
        
        # Se for marcado como default, remove default dos outros endereços
        if update_data.get("is_default") is True:
            db.query(CustomerAddress).filter(
                and_(
                    CustomerAddress.customer_id == db_address.customer_id,
                    CustomerAddress.id != address_id
                )
            ).update({"is_default": False})
        
        for field, value in update_data.items():
            setattr(db_address, field, value)
        
        db.commit()
        db.refresh(db_address)
        logger.info("Endereço atualizado", address_id=address_id)
        return db_address
