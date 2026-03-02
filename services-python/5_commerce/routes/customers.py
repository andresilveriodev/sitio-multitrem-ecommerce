"""
Rotas para clientes e endereços
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from db_session import get_db_session
from services.customer_service import CustomerService
from schemas.customer import (
    CustomerCreate, CustomerUpdate, CustomerResponse,
    CustomerAddressCreate, CustomerAddressUpdate, CustomerAddressResponse,
    CustomerContactCreate, CustomerContactUpdate, CustomerContactResponse
)

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("", response_model=List[CustomerResponse])
def list_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db_session)
):
    """Lista clientes"""
    return CustomerService.get_customers(db, skip=skip, limit=limit, search=search)


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: int, db: Session = Depends(get_db_session)):
    """Busca um cliente por ID"""
    customer = CustomerService.get_customer(db, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return customer


@router.get("/phone/{phone_e164}", response_model=CustomerResponse)
def get_customer_by_phone(phone_e164: str, db: Session = Depends(get_db_session)):
    """Busca um cliente por telefone"""
    customer = CustomerService.get_customer_by_phone(db, phone_e164)
    if not customer:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return customer


@router.post("", response_model=CustomerResponse, status_code=201)
def create_customer(customer: CustomerCreate, db: Session = Depends(get_db_session)):
    """Cria um novo cliente"""
    return CustomerService.create_customer(db, customer)


@router.put("/{customer_id}", response_model=CustomerResponse)
def update_customer(
    customer_id: int,
    customer: CustomerUpdate,
    db: Session = Depends(get_db_session)
):
    """Atualiza um cliente"""
    updated = CustomerService.update_customer(db, customer_id, customer)
    if not updated:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return updated


@router.get("/{customer_id}/addresses", response_model=List[CustomerAddressResponse])
def list_customer_addresses(customer_id: int, db: Session = Depends(get_db_session)):
    """Lista endereços de um cliente"""
    return CustomerService.get_customer_addresses(db, customer_id)


@router.get("/addresses/{address_id}", response_model=CustomerAddressResponse)
def get_customer_address(address_id: int, db: Session = Depends(get_db_session)):
    """Busca um endereço por ID"""
    address = CustomerService.get_customer_address(db, address_id)
    if not address:
        raise HTTPException(status_code=404, detail="Endereço não encontrado")
    return address


@router.post("/addresses", response_model=CustomerAddressResponse, status_code=201)
def create_customer_address(address: CustomerAddressCreate, db: Session = Depends(get_db_session)):
    """Cria um novo endereço"""
    return CustomerService.create_customer_address(db, address)


@router.put("/addresses/{address_id}", response_model=CustomerAddressResponse)
def update_customer_address(
    address_id: int,
    address: CustomerAddressUpdate,
    db: Session = Depends(get_db_session)
):
    """Atualiza um endereço"""
    updated = CustomerService.update_customer_address(db, address_id, address)
    if not updated:
        raise HTTPException(status_code=404, detail="Endereço não encontrado")
    return updated


@router.get("/{customer_id}/contacts", response_model=List[CustomerContactResponse])
def list_customer_contacts(customer_id: int, db: Session = Depends(get_db_session)):
    """Lista contatos de um cliente"""
    return CustomerService.get_customer_contacts(db, customer_id)


@router.get("/contacts/{contact_id}", response_model=CustomerContactResponse)
def get_customer_contact(contact_id: int, db: Session = Depends(get_db_session)):
    """Busca um contato por ID"""
    contact = CustomerService.get_customer_contact(db, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contato não encontrado")
    return contact


@router.get("/contacts/phone/{phone_e164}", response_model=CustomerContactResponse)
def get_customer_contact_by_phone(phone_e164: str, db: Session = Depends(get_db_session)):
    """Busca um contato por telefone"""
    contact = CustomerService.get_customer_contact_by_phone(db, phone_e164)
    if not contact:
        raise HTTPException(status_code=404, detail="Contato não encontrado")
    return contact


@router.post("/contacts", response_model=CustomerContactResponse, status_code=201)
def create_customer_contact(contact: CustomerContactCreate, db: Session = Depends(get_db_session)):
    """Cria um novo contato"""
    return CustomerService.create_customer_contact(db, contact)


@router.put("/contacts/{contact_id}", response_model=CustomerContactResponse)
def update_customer_contact(
    contact_id: int,
    contact: CustomerContactUpdate,
    db: Session = Depends(get_db_session)
):
    """Atualiza um contato"""
    updated = CustomerService.update_customer_contact(db, contact_id, contact)
    if not updated:
        raise HTTPException(status_code=404, detail="Contato não encontrado")
    return updated


@router.delete("/contacts/{contact_id}", status_code=204)
def delete_customer_contact(contact_id: int, db: Session = Depends(get_db_session)):
    """Remove um contato"""
    deleted = CustomerService.delete_customer_contact(db, contact_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Contato não encontrado")
    return None
