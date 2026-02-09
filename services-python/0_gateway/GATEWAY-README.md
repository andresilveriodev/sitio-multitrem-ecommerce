# Gateway Service - BFF/API Gateway

## Visão Geral

O Gateway Service é o ponto de entrada principal para todas as aplicações frontend (Web/Mobile) que precisam se comunicar com os microserviços do E-commerce. Ele atua como um **Backend for Frontend (BFF)** e **API Gateway**, fornecendo uma interface unificada e segura para todos os microserviços.

## Arquitetura

```
[Web/Mobile] 
    └──> [Gateway Service - Porta 8000]
            ├──> user_service (Porta 8001)
            ├──> import_service (Porta 8002)
            ├──> chatbot_service (Porta 8008)
            └──> ai_service (Porta 8012)
```

## Funcionalidades

### 🔐 Autenticação e Autorização
- **JWT Token Validation**: Validação de tokens JWT
- **Keycloak Integration**: Integração com Keycloak para autenticação
- **Permission-based Access**: Controle de acesso baseado em permissões
- **Session Management**: Gerenciamento de sessões

### 🚦 Rate Limiting
- **Per-minute limits**: Limite por minuto configurável
- **Per-hour limits**: Limite por hora configurável
- **IP-based tracking**: Rastreamento por IP
- **User-based tracking**: Rastreamento por usuário

### 💾 Cache
- **Redis Integration**: Cache distribuído com Redis
- **Response Caching**: Cache de respostas
- **TTL Configuration**: Tempo de vida configurável por endpoint
- **Cache Invalidation**: Invalidação inteligente de cache

### 📊 Logging e Monitoramento
- **Request/Response Logging**: Log de todas as requisições e respostas
- **Performance Metrics**: Métricas de performance
- **Error Tracking**: Rastreamento de erros
- **Health Checks**: Verificação de saúde dos microserviços

### 🔄 Circuit Breaker
- **Failure Detection**: Detecção de falhas
- **Automatic Recovery**: Recuperação automática
- **Configurable Thresholds**: Limites configuráveis
- **Service Isolation**: Isolamento de serviços

### ⚖️ Load Balancing
- **Round Robin**: Distribuição round-robin
- **Health-based Routing**: Roteamento baseado em saúde
- **Multiple Instances**: Suporte a múltiplas instâncias

## Endpoints

### Autenticação
- `POST /api/v1/auth/login` - Login do usuário
- `POST /api/v1/auth/register` - Registro de usuário
- `POST /api/v1/auth/refresh` - Refresh de token
- `POST /api/v1/auth/logout` - Logout
- `GET /api/v1/auth/profile` - Perfil do usuário

### Usuários
- `GET /api/v1/users/*` - Todas as operações de usuário
- `POST /api/v1/users/*` - Criação de usuários
- `PUT /api/v1/users/*` - Atualização de usuários
- `DELETE /api/v1/users/*` - Remoção de usuários

### Produtos
- `GET /api/v1/products` - Lista de produtos
- `GET /api/v1/products/{id}` - Detalhes do produto
- `GET /api/v1/products/search` - Busca de produtos

### Carrinho
- `GET /api/v1/cart` - Carrinho do usuário
- `POST /api/v1/cart/items` - Adicionar item ao carrinho
- `PUT /api/v1/cart/items/{id}` - Atualizar item do carrinho
- `DELETE /api/v1/cart/items/{id}` - Remover item do carrinho

### Pedidos
- `GET /api/v1/orders` - Lista de pedidos
- `POST /api/v1/orders` - Criar pedido
- `GET /api/v1/orders/{id}` - Detalhes do pedido
- `PUT /api/v1/orders/{id}` - Atualizar pedido

### Chatbot e IA
- `POST /api/v1/chatbot/message` - Envio de mensagem
- `GET /api/v1/ai/analysis` - Análise de IA
- `POST /api/v1/ai/prediction` - Predições

### Sistema
- `GET /` - Status do gateway
- `GET /health` - Health check
- `GET /api/v1/status` - Status detalhado

## Configuração

### Variáveis de Ambiente

```bash
# Configurações básicas
DEBUG=false
HOST=0.0.0.0
PORT=8000

# Redis
REDIS_URL=redis://redis:6379/0

# Microserviços
USER_SERVICE_URL=http://user_service:8001
IMPORT_SERVICE_URL=http://import_service:8002
CHATBOT_SERVICE_URL=http://chatbot_service:8008
AI_SERVICE_URL=http://artificial_intelligence_service:8012

# Keycloak
KEYCLOAK_URL=http://localhost:8080
KEYCLOAK_REALM=ecommerce
KEYCLOAK_CLIENT_ID=ecommerce-gateway
KEYCLOAK_CLIENT_SECRET=your-secret

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_PER_HOUR=1000

# Cache
CACHE_TTL=300

# Circuit Breaker
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_RECOVERY_TIMEOUT=60
```

## Execução

### Com Docker Compose

```bash
# Executar todos os serviços
docker-compose up -d

# Executar apenas o gateway
docker-compose up gateway_service
```

### Desenvolvimento Local

```bash
# Instalar dependências
pip install -r requirements.txt

# Executar
python main.py
```

### Testes

```bash
# Testar health check
curl http://localhost:8000/health

# Testar status
curl http://localhost:8000/api/v1/status

# Testar autenticação (sem token)
curl http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "test"}'
```

## Monitoramento

### Health Checks
- **Gateway**: `GET /health`
- **Microserviços**: Verificação automática de todos os serviços
- **Redis**: Verificação de conectividade
- **Circuit Breakers**: Status dos circuit breakers

### Métricas
- **Request Rate**: Requisições por segundo
- **Response Time**: Tempo de resposta médio
- **Error Rate**: Taxa de erro
- **Cache Hit Rate**: Taxa de acerto do cache

### Logs
- **Request Logs**: Todas as requisições com detalhes
- **Error Logs**: Erros e exceções
- **Performance Logs**: Métricas de performance
- **Security Logs**: Tentativas de acesso não autorizado

## Segurança

### Autenticação
- **JWT Tokens**: Tokens JWT para autenticação
- **Keycloak Integration**: Integração com Keycloak
- **Token Refresh**: Renovação automática de tokens
- **Session Management**: Gerenciamento de sessões

### Autorização
- **Permission-based**: Controle baseado em permissões
- **Role-based**: Controle baseado em roles
- **Resource-based**: Controle por recurso
- **API-level**: Controle no nível da API

### Rate Limiting
- **IP-based**: Limitação por IP
- **User-based**: Limitação por usuário
- **Endpoint-based**: Limitação por endpoint
- **Configurable**: Limites configuráveis

### CORS
- **Origin Control**: Controle de origens permitidas
- **Method Control**: Controle de métodos HTTP
- **Header Control**: Controle de headers
- **Credential Support**: Suporte a credenciais

## Troubleshooting

### Problemas Comuns

1. **Serviço não responde**
   - Verificar se o microserviço está rodando
   - Verificar conectividade de rede
   - Verificar circuit breaker

2. **Erro de autenticação**
   - Verificar token JWT
   - Verificar configuração do Keycloak
   - Verificar permissões do usuário

3. **Rate limit excedido**
   - Aguardar reset do limite
   - Verificar configuração de rate limiting
   - Considerar aumentar limites

4. **Cache não funcionando**
   - Verificar conectividade com Redis
   - Verificar configuração de TTL
   - Verificar chaves de cache

### Logs Úteis

```bash
# Ver logs do gateway
docker logs ecommerce_gateway_service

# Ver logs em tempo real
docker logs -f ecommerce_gateway_service

# Ver logs de erro
docker logs ecommerce_gateway_service 2>&1 | grep ERROR
```

## Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Implemente as mudanças
4. Adicione testes
5. Faça commit das mudanças
6. Abra um Pull Request

## Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.
