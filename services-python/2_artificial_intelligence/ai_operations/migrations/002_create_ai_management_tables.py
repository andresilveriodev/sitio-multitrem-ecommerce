"""Migração 002: Criar tabelas de gerenciamento de IA"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.config import DATABASE_URI as DATABASE_URL
import logging

logger = logging.getLogger(__name__)

def create_ai_management_tables():
    """Cria as tabelas de gerenciamento de IA"""
    
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # 1. Tabela ai_models
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ai_models (
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
        
        # 2. Tabela ai_subscriptions
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ai_subscriptions (
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
        
        # 3. Tabela user_subscriptions
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS user_subscriptions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                subscription_id INTEGER NOT NULL REFERENCES ai_subscriptions(id),
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
        
        # 4. Tabela user_ai_settings
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS user_ai_settings (
                id SERIAL PRIMARY KEY,
                user_id INTEGER UNIQUE NOT NULL REFERENCES users(id),
                default_model VARCHAR(100) NOT NULL DEFAULT 'ollama',
                preferred_models JSONB,
                auto_fallback BOOLEAN DEFAULT TRUE,
                notifications JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        # 5. Tabela ai_usage_alerts
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ai_usage_alerts (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
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
        
        # Índices para performance
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ai_models_model_id ON ai_models(model_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ai_models_provider ON ai_models(provider);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ai_subscriptions_plan_id ON ai_subscriptions(plan_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_subscriptions_user_id ON user_subscriptions(user_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_subscriptions_status ON user_subscriptions(status);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_ai_settings_user_id ON user_ai_settings(user_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ai_usage_alerts_user_id ON ai_usage_alerts(user_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ai_usage_alerts_type ON ai_usage_alerts(alert_type);"))
        
        # Dados iniciais - Modelos de IA
        conn.execute(text("""
            INSERT INTO ai_models (model_id, name, provider, is_paid, cost_per_1k_tokens, max_tokens_per_request, description, features, rate_limits) 
            VALUES 
            ('ollama', 'Ollama Local', 'Ollama', false, 0, 8192, 'Modelo local gratuito', '["chat", "analysis"]', '{"requestsPerMinute": 60, "requestsPerHour": 1000}'),
            ('deepseek', 'DeepSeek', 'DeepSeek', true, 0.0001, 4096, 'Modelo econômico para análise', '["chat", "analysis", "coding"]', '{"requestsPerMinute": 30, "requestsPerHour": 500}'),
            ('gpt-4o-mini', 'GPT-4o Mini', 'OpenAI', true, 0.00015, 4096, 'Modelo rápido e eficiente', '["chat", "analysis", "coding"]', '{"requestsPerMinute": 50, "requestsPerHour": 800}'),
            ('gpt-5-mini', 'GPT-5 Mini', 'OpenAI', true, 0.0003, 8192, 'Modelo avançado', '["chat", "analysis", "coding", "reasoning"]', '{"requestsPerMinute": 20, "requestsPerHour": 300}')
            ON CONFLICT (model_id) DO NOTHING;
        """))
        
        # Dados iniciais - Planos de assinatura
        conn.execute(text("""
            INSERT INTO ai_subscriptions (plan_id, name, price, features, limits) 
            VALUES 
            ('free', 'Plano Gratuito', 0, '["chat", "basic_analysis"]', '{"maxRequestsPerMonth": 100, "maxTokensPerMonth": 50000, "maxCostPerMonth": 0}'),
            ('basic', 'Plano Básico', 29.90, '["chat", "analysis", "coding"]', '{"maxRequestsPerMonth": 1000, "maxTokensPerMonth": 500000, "maxCostPerMonth": 50}'),
            ('premium', 'Plano Premium', 99.90, '["chat", "analysis", "coding", "advanced_features"]', '{"maxRequestsPerMonth": 5000, "maxTokensPerMonth": 2000000, "maxCostPerMonth": 200}'),
            ('enterprise', 'Plano Enterprise', 299.90, '["all_features", "priority_support"]', '{"maxRequestsPerMonth": 50000, "maxTokensPerMonth": 10000000, "maxCostPerMonth": 1000}')
            ON CONFLICT (plan_id) DO NOTHING;
        """))
        
        conn.commit()
        logger.info("Tabelas de gerenciamento de IA criadas com sucesso!")

if __name__ == "__main__":
    create_ai_management_tables()
