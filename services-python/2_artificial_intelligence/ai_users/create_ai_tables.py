#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para criar as tabelas de gerenciamento de IA
"""

import os
import sys
from sqlalchemy import create_engine, text
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração do banco de dados
DATABASE_URL = "postgresql://postgres:123456@localhost:5434/sitio_multitrem"

def create_ai_management_tables():
    """Cria as tabelas de gerenciamento de IA"""
    
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # Criar schema ai_management se não existir
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS ai_management"))
            conn.commit()
            
            # 1. Tabela ai_models (com schema)
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS ai_management.ai_models (
                    id SERIAL PRIMARY KEY,
                    model_id VARCHAR(100) UNIQUE NOT NULL,
                    name VARCHAR(200) NOT NULL,
                    provider VARCHAR(100) NOT NULL,
                    is_paid BOOLEAN DEFAULT FALSE,
                    cost_per_1k_tokens DECIMAL(10,6) DEFAULT 0,
                    max_tokens_per_request INTEGER DEFAULT 4096,
                    is_available BOOLEAN DEFAULT TRUE,
                    description TEXT,
                    features JSONB,
                    rate_limits JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            
            # 2. Tabela ai_subscriptions (com schema)
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS ai_management.ai_subscriptions (
                    id SERIAL PRIMARY KEY,
                    plan_id VARCHAR(100) UNIQUE NOT NULL,
                    name VARCHAR(200) NOT NULL,
                    price DECIMAL(10,2) DEFAULT 0,
                    currency VARCHAR(10) DEFAULT 'BRL',
                    billing_cycle VARCHAR(20) DEFAULT 'monthly',
                    is_active BOOLEAN DEFAULT TRUE,
                    features JSONB,
                    limits JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            conn.commit()
            logger.info("✅ Tabelas principais (ai_models e ai_subscriptions) criadas com sucesso")
            
            # 3. Tabela user_subscriptions (com schema) - depende de public.users
            try:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS ai_management.user_subscriptions (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES public.users(id),
                        username VARCHAR(50) NOT NULL,
                        subscription_id INTEGER NOT NULL REFERENCES ai_management.ai_subscriptions(id),
                        status VARCHAR(20) DEFAULT 'active',
                        current_period_start TIMESTAMP,
                        current_period_end TIMESTAMP,
                        cancel_at_period_end BOOLEAN DEFAULT FALSE,
                        usage_limits JSONB,
                        current_usage JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """))
                conn.commit()
                logger.info("✅ Tabela user_subscriptions criada com sucesso")
            except Exception as e:
                conn.rollback()
                logger.warning(f"⚠️ Não foi possível criar user_subscriptions (tabela public.users não existe): {e}")
            
            # 4. Tabela user_ai_settings (com schema) - depende de public.users
            try:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS ai_management.user_ai_settings (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER UNIQUE NOT NULL REFERENCES public.users(id),
                        username VARCHAR(50) NOT NULL,
                        default_model VARCHAR(100) NOT NULL DEFAULT 'ollama',
                        preferred_models JSONB,
                        auto_fallback BOOLEAN DEFAULT TRUE,
                        notifications JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """))
                conn.commit()
                logger.info("✅ Tabela user_ai_settings criada com sucesso")
            except Exception as e:
                conn.rollback()
                logger.warning(f"⚠️ Não foi possível criar user_ai_settings (tabela public.users não existe): {e}")
            
            # 5. Tabela ai_usage_alerts (com schema) - depende de public.users
            try:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS ai_management.ai_usage_alerts (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES public.users(id),
                        username VARCHAR(50) NOT NULL,
                        alert_type VARCHAR(20) NOT NULL,
                        threshold DECIMAL(10,2) NOT NULL,
                        current_value DECIMAL(10,2) NOT NULL,
                        message TEXT NOT NULL,
                        is_triggered BOOLEAN DEFAULT FALSE,
                        is_read BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """))
                conn.commit()
                logger.info("✅ Tabela ai_usage_alerts criada com sucesso")
            except Exception as e:
                conn.rollback()
                logger.warning(f"⚠️ Não foi possível criar ai_usage_alerts (tabela public.users não existe): {e}")
            
            # Fechar conexão atual e criar nova para continuar
            conn.close()
            
            # Nova conexão para índices e dados iniciais
            with engine.connect() as conn2:
                # Índices para performance (com schema)
                conn2.execute(text("CREATE INDEX IF NOT EXISTS idx_ai_models_model_id ON ai_management.ai_models(model_id);"))
                conn2.execute(text("CREATE INDEX IF NOT EXISTS idx_ai_models_provider ON ai_management.ai_models(provider);"))
                conn2.execute(text("CREATE INDEX IF NOT EXISTS idx_ai_subscriptions_plan_id ON ai_management.ai_subscriptions(plan_id);"))
                conn2.commit()
                
                # Índices para tabelas que dependem de users (criar apenas se as tabelas existirem)
                try:
                    conn2.execute(text("CREATE INDEX IF NOT EXISTS idx_user_subscriptions_user_id ON ai_management.user_subscriptions(user_id);"))
                    conn2.execute(text("CREATE INDEX IF NOT EXISTS idx_user_subscriptions_status ON ai_management.user_subscriptions(status);"))
                    conn2.commit()
                except:
                    conn2.rollback()
                try:
                    conn2.execute(text("CREATE INDEX IF NOT EXISTS idx_user_ai_settings_user_id ON ai_management.user_ai_settings(user_id);"))
                    conn2.commit()
                except:
                    conn2.rollback()
                try:
                    conn2.execute(text("CREATE INDEX IF NOT EXISTS idx_ai_usage_alerts_user_id ON ai_management.ai_usage_alerts(user_id);"))
                    conn2.execute(text("CREATE INDEX IF NOT EXISTS idx_ai_usage_alerts_type ON ai_management.ai_usage_alerts(alert_type);"))
                    conn2.commit()
                except:
                    conn2.rollback()
                
                # Dados iniciais - Modelos de IA (com schema)
                conn2.execute(text("""
                    INSERT INTO ai_management.ai_models (model_id, name, provider, is_paid, cost_per_1k_tokens, max_tokens_per_request, description, features, rate_limits) 
                    VALUES 
                    ('ollama', 'Ollama Local', 'Ollama', false, 0, 8192, 'Modelo local gratuito', '["chat", "analysis"]', '{"requestsPerMinute": 60, "requestsPerHour": 1000}'),
                    ('deepseek', 'DeepSeek', 'DeepSeek', true, 0.0001, 4096, 'Modelo econômico para análise', '["chat", "analysis", "coding"]', '{"requestsPerMinute": 30, "requestsPerHour": 500}'),
                    ('gpt-4o-mini', 'GPT-4o Mini', 'OpenAI', true, 0.00015, 4096, 'Modelo rápido e eficiente', '["chat", "analysis", "coding"]', '{"requestsPerMinute": 50, "requestsPerHour": 800}'),
                    ('gpt-5-mini', 'GPT-5 Mini', 'OpenAI', true, 0.0003, 8192, 'Modelo avançado', '["chat", "analysis", "coding", "reasoning"]', '{"requestsPerMinute": 20, "requestsPerHour": 300}')
                    ON CONFLICT (model_id) DO NOTHING;
                """))
                
                # Dados iniciais - Planos de assinatura (com schema)
                conn2.execute(text("""
                    INSERT INTO ai_management.ai_subscriptions (plan_id, name, price, features, limits) 
                    VALUES 
                    ('free', 'Plano Gratuito', 0, '["chat", "basic_analysis"]', '{"maxRequestsPerMonth": 100, "maxTokensPerMonth": 50000, "maxCostPerMonth": 0}'),
                    ('basic', 'Plano Básico', 29.90, '["chat", "analysis", "coding"]', '{"maxRequestsPerMonth": 1000, "maxTokensPerMonth": 500000, "maxCostPerMonth": 50}'),
                    ('premium', 'Plano Premium', 99.90, '["chat", "analysis", "coding", "advanced_features"]', '{"maxRequestsPerMonth": 5000, "maxTokensPerMonth": 2000000, "maxCostPerMonth": 200}'),
                    ('enterprise', 'Plano Enterprise', 299.90, '["all_features", "priority_support"]', '{"maxRequestsPerMonth": 50000, "maxTokensPerMonth": 10000000, "maxCostPerMonth": 1000}')
                    ON CONFLICT (plan_id) DO NOTHING;
                """))
                
                conn2.commit()
                logger.info("✅ Tabelas de gerenciamento de IA criadas com sucesso!")
            
    except Exception as e:
        logger.error(f"❌ Erro ao criar tabelas: {e}")
        raise

if __name__ == "__main__":
    create_ai_management_tables()
