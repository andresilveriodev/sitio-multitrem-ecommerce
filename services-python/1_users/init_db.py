#!/usr/bin/env python3
"""
Script para inicializar o banco de dados do Auth Service
Cria tabelas e dados iniciais para ACL
"""

import asyncio
import structlog
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import settings
from models.acl import Base, User, Profile, Permission
from models.user_profile import UserProfileData, UserPreferences, UserSettings, UserActivity
from services.acl_service import acl_service

logger = structlog.get_logger()

def init_database():
    """Inicializa o banco de dados"""
    try:
        logger.info("Iniciando inicialização do banco de dados")
        
        # Criar engine do banco
        engine = create_engine(
            settings.DATABASE_URI,
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
            pool_timeout=settings.DATABASE_POOL_TIMEOUT,
            pool_recycle=settings.DATABASE_POOL_RECYCLE
        )
        
        # Criar todas as tabelas
        Base.metadata.create_all(bind=engine)
        logger.info("Tabelas criadas com sucesso")
        
        # Criar sessão
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Criar dados iniciais
        create_initial_data(db)
        
        db.close()
        logger.info("Inicialização do banco de dados concluída")
        
    except Exception as e:
        logger.error("Erro na inicialização do banco de dados", error=str(e))
        raise

def create_initial_data(db):
    """Cria dados iniciais para ACL"""
    try:
        logger.info("Criando dados iniciais para ACL")
        
        # Criar permissões básicas
        permissions = create_basic_permissions(db)
        
        # Criar perfis básicos
        profiles = create_basic_profiles(db, permissions)
        
        logger.info("Dados iniciais criados com sucesso")
        
    except Exception as e:
        logger.error("Erro ao criar dados iniciais", error=str(e))
        db.rollback()
        raise

def create_basic_permissions(db):
    """Cria permissões básicas do sistema"""
    permissions = {}
    
    # Permissões de ACL
    acl_permissions = [
        ("acl_read_all", "Ler todas as permissões ACL", "acl", "read", "all"),
        ("acl_write_all", "Gerenciar permissões ACL", "acl", "write", "all"),
        ("acl_read_own", "Ler próprias permissões", "acl", "read", "own"),
    ]
    
    for name, description, resource, action, scope in acl_permissions:
        # Forçar criação de nova permissão
        permission = Permission(
            name=name,
            description=description,
            resource=resource,
            action=action,
            scope=scope
        )
        db.add(permission)
        permissions[name] = permission
    
    # Permissões de Relatórios
    report_permissions = [
        ("reports_read", "Ler relatórios próprios", "reports", "read", "own"),
        ("reports_write", "Gerar relatórios próprios", "reports", "write", "own"),
        ("reports_read_all", "Ler todos os relatórios", "reports", "read", "all"),
        ("reports_write_all", "Gerar todos os relatórios", "reports", "write", "all"),
    ]
    
    for name, description, resource, action, scope in report_permissions:
        # Forçar criação de nova permissão
        permission = Permission(
            name=name,
            description=description,
            resource=resource,
            action=action,
            scope=scope
        )
        db.add(permission)
        permissions[name] = permission
    
    logger.info(f"Criadas {len(permissions)} permissões básicas")
    
    return permissions

def create_basic_profiles(db, permissions):
    """Cria perfis básicos do sistema"""
    profiles = {}
    
    # Perfil de Administrador
    admin_profile = db.query(Profile).filter(Profile.name == "admin").first()
    if not admin_profile:
        admin_profile = Profile(
            name="admin",
            description="Administrador do sistema com acesso total"
        )
        db.add(admin_profile)
        profiles["admin"] = admin_profile
    
    # Perfil de Analista
    analyst_profile = db.query(Profile).filter(Profile.name == "analyst").first()
    if not analyst_profile:
        analyst_profile = Profile(
            name="analyst",
            description="Analista com acesso a dados e relatórios"
        )
        db.add(analyst_profile)
        profiles["analyst"] = analyst_profile
    
    # Perfil de Visualizador
    viewer_profile = db.query(Profile).filter(Profile.name == "viewer").first()
    if not viewer_profile:
        viewer_profile = Profile(
            name="viewer",
            description="Visualizador com acesso limitado a leitura"
        )
        db.add(viewer_profile)
        profiles["viewer"] = viewer_profile
    
    db.commit()
    
    # Atribuir permissões aos perfis
    assign_permissions_to_profiles(db, profiles, permissions)
    
    logger.info(f"Criados {len(profiles)} perfis básicos")
    
    return profiles

def assign_permissions_to_profiles(db, profiles, permissions):
    """Atribui permissões aos perfis"""
    from models.acl import ProfilePermission
    
    # Admin: todas as permissões
    admin_profile = profiles["admin"]
    for permission in permissions.values():
        # Verificar se já existe a associação
        existing = db.query(ProfilePermission).filter(
            ProfilePermission.profile_id == admin_profile.id,
            ProfilePermission.permission_id == permission.id
        ).first()
        if not existing:
            profile_permission = ProfilePermission(
                profile_id=admin_profile.id,
                permission_id=permission.id
            )
            db.add(profile_permission)
    
    # Analista: permissões de leitura e relatórios
    analyst_profile = profiles["analyst"]
    analyst_permissions = [
        "reports_read_all", "reports_write_all"
    ]
    for perm_name in analyst_permissions:
        if perm_name in permissions:
            permission = permissions[perm_name]
            existing = db.query(ProfilePermission).filter(
                ProfilePermission.profile_id == analyst_profile.id,
                ProfilePermission.permission_id == permission.id
            ).first()
            if not existing:
                profile_permission = ProfilePermission(
                    profile_id=analyst_profile.id,
                    permission_id=permission.id
                )
                db.add(profile_permission)
    
    # Viewer: apenas leitura limitada
    viewer_profile = profiles["viewer"]
    viewer_permissions = [
        "reports_read"
    ]
    for perm_name in viewer_permissions:
        if perm_name in permissions:
            permission = permissions[perm_name]
            existing = db.query(ProfilePermission).filter(
                ProfilePermission.profile_id == viewer_profile.id,
                ProfilePermission.permission_id == permission.id
            ).first()
            if not existing:
                profile_permission = ProfilePermission(
                    profile_id=viewer_profile.id,
                    permission_id=permission.id
                )
                db.add(profile_permission)
    
    db.commit()
    logger.info("Permissões atribuídas aos perfis")

if __name__ == "__main__":
    init_database()

