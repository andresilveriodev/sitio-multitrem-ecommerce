"""
Serviço de clientes
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
import structlog

from models.commerce import Customer, CustomerAddress, CustomerContact
from schemas.customer import (
    CustomerCreate, CustomerUpdate, CustomerAddressCreate, CustomerAddressUpdate,
    CustomerContactCreate, CustomerContactUpdate
)

logger = structlog.get_logger()


class CustomerService:
    """Serviço para gerenciar clientes e endereços"""
    
    @staticmethod
    def get_customers(db: Session, skip: int = 0, limit: int = 100, search: Optional[str] = None) -> List[Customer]:
        """
        Lista clientes com busca opcional
        Busca por: nome do cliente (establishment), telefone, documento OU nome de contato
        """
        query = db.query(Customer)
        
        if search:
            search_term = f"%{search}%"
            # Busca no cliente (nome do estabelecimento, telefone, documento)
            # E também em contatos vinculados (nome do contato)
            query = query.outerjoin(CustomerContact).filter(
                or_(
                    Customer.name.ilike(search_term),
                    Customer.phone_e164.ilike(search_term),
                    Customer.document.ilike(search_term),
                    CustomerContact.name.ilike(search_term)
                )
            ).distinct()  # Evita duplicatas quando há múltiplos contatos
        
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
    
    @staticmethod
    def get_customer_contacts(db: Session, customer_id: int) -> List[CustomerContact]:
        """Lista contatos de um cliente"""
        return db.query(CustomerContact).filter(CustomerContact.customer_id == customer_id).all()
    
    @staticmethod
    def get_customer_contact(db: Session, contact_id: int) -> Optional[CustomerContact]:
        """Busca um contato por ID"""
        return db.query(CustomerContact).filter(CustomerContact.id == contact_id).first()
    
    @staticmethod
    def get_customer_contact_by_phone(db: Session, phone_e164: str) -> Optional[CustomerContact]:
        """Busca um contato por telefone"""
        return db.query(CustomerContact).filter(CustomerContact.phone_e164 == phone_e164).first()
    
    @staticmethod
    def get_customer_contact_by_email(db: Session, email: str) -> Optional[CustomerContact]:
        """Busca um contato por email"""
        return db.query(CustomerContact).filter(CustomerContact.email == email).first()
    
    @staticmethod
    def create_customer_contact(db: Session, contact: CustomerContactCreate) -> CustomerContact:
        """Cria um novo contato"""
        db_contact = CustomerContact(**contact.model_dump())
        db.add(db_contact)
        db.commit()
        db.refresh(db_contact)
        logger.info("Contato criado", contact_id=db_contact.id, customer_id=contact.customer_id)
        return db_contact
    
    @staticmethod
    def update_customer_contact(db: Session, contact_id: int, contact: CustomerContactUpdate) -> Optional[CustomerContact]:
        """Atualiza um contato"""
        db_contact = db.query(CustomerContact).filter(CustomerContact.id == contact_id).first()
        if not db_contact:
            return None
        
        update_data = contact.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_contact, field, value)
        
        db.commit()
        db.refresh(db_contact)
        logger.info("Contato atualizado", contact_id=contact_id)
        return db_contact
    
    @staticmethod
    def delete_customer_contact(db: Session, contact_id: int) -> bool:
        """Remove um contato"""
        db_contact = db.query(CustomerContact).filter(CustomerContact.id == contact_id).first()
        if not db_contact:
            return False
        
        db.delete(db_contact)
        db.commit()
        logger.info("Contato removido", contact_id=contact_id)
        return True