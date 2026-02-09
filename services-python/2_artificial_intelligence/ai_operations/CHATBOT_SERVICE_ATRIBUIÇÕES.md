# 🤖 ATRIBUIÇÕES DO CHATBOT SERVICE

Este documento descreve as atribuições principais do Chatbot Service e a separação clara de responsabilidades com o AI Service.

---

## 📋 **10 ATRIBUIÇÕES PRINCIPAIS DO CHATBOT SERVICE**

### **1. Gateway de Segurança e Validação de Entrada**
- **Valida e sanitiza** todas as mensagens antes de enviar ao AI Service
- **Validação de formato**: Verifica estrutura e formato das mensagens
- **Detecção de spam**: Identifica e bloqueia conteúdo spam
- **Proteção contra prompt injection**: Previne ataques de injeção de prompt
- **Sanitização de PII**: Remove ou mascara dados sensíveis como CPF/CNPJ
- **Validação de limites**: Verifica limites de caracteres e tamanho

### **2. Filtros Inteligentes e Respostas Automáticas**
- **Responde diretamente** a perguntas frequentes e óbvias **SEM chamar a IA**:
  - Saudações: "Oi", "Olá", "Como você está?"
  - Perguntas sobre o sistema: "Qual é o seu nome?", "Que horas são?"
  - Agradecimentos: "Obrigado", "Valeu"
  - Despedidas: "Tchau", "Adeus", "Até logo"
  - Perguntas sobre funcionalidades básicas do sistema
- **Economiza custos** evitando chamadas desnecessárias à IA

### **3. Sistema de Cache**
- **Cache em memória**: Respostas rápidas para consultas similares
- **Cache em Redis**: Persistência de cache entre reinicializações
- **Cache inteligente**: Identifica mensagens similares e reutiliza respostas
- **Reduz chamadas** ao AI Service em até 40-60%

### **4. Gestão de Contexto de Conversas**
- **Mantém histórico contextual** de cada conversa por usuário
- **Detecta mudanças de tópico** e cria novos contextos quando necessário
- **Gera resumos de contexto** para otimizar tokens enviados à IA
- **Enriquece prompts** com informações relevantes do histórico
- **Persiste contexto** entre interações (via Redis)

### **5. Sistema de Comandos do E-commerce**
- **Detecta intenções** de comandos do e-commerce na mensagem do usuário
- **Valida comandos** antes de executar
- **Executa ações** como:
  - Mostrar carrinho atual
  - Adicionar produtos ao carrinho
  - Preparar pedidos de compra
  - Consultar histórico de pedidos
- **Confirmação para ações críticas**: Solicita confirmação antes de executar operações importantes
- **Formata respostas** de forma amigável para o usuário

### **6. Otimização de Custos**
- **Reduz 40-60%** das chamadas à IA através de:
  - Cache inteligente
  - Respostas automáticas para perguntas simples
  - Agrupamento de mensagens quando apropriado
- **Classifica urgência** das mensagens (baixa, média, alta)
- **Seleciona modelos mais baratos** para tarefas simples
- **Monitora custos** por usuário e conversa (consultando AI Service)

### **7. Integração com AI Service**
- **Atua como proxy** entre frontend e AI Service
- **Valida limites** de assinatura antes de chamar IA (consultando AI Service)
- **Consulta configurações** do usuário (user_ai_settings) no AI Service
- **Repassa requisições** ao AI Service quando necessário
- **Envia metadados** corretos para rastreamento (conversation_id, user_id)
- **Implementa fallbacks** quando um provider falha
- **Gerencia timeouts** e retry logic

### **8. Analytics e Métricas**
- **Coleta estatísticas** de performance do próprio serviço:
  - Taxa de cache hit
  - Taxa de respostas diretas (sem IA)
  - Tempo médio de resposta
  - Uso de memória
  - Número de sessões ativas
- **Monitora custos** e economia gerada pelo cache e filtros
- **Rastreia saúde** do sistema (uptime, erros, latência)
- **Gera relatórios** de uso do chatbot service

### **9. Streaming de Respostas**
- **Suporta Server-Sent Events (SSE)** para respostas em tempo real
- **Processa chunks** da IA e repassa ao frontend em streaming
- **Gerencia conexões** de streaming ativas
- **Implementa timeouts** e reconexão automática

### **10. Gestão de Sessões e Rate Limiting**
- **Controla sessões ativas** por usuário
- **Aplica rate limiting**: 30 requisições por minuto por usuário (configurável)
- **Gerencia timeouts** de sessão
- **Sincroniza estado** entre frontend e backend
- **Armazena preferências** temporárias do usuário (em Redis)
- **Persiste estado** entre reinicializações quando necessário

---

## ❌ **ATRIBUIÇÕES DO AI SERVICE QUE O CHATBOT SERVICE NÃO FAZ**

O Chatbot Service **NÃO gerencia** as seguintes responsabilidades (são do AI Service):

### **1. Tabelas de Banco de Dados de IA**
- ❌ **NÃO gerencia** `conversations` (o Chatbot apenas consulta)
- ❌ **NÃO gerencia** `messages` (o Chatbot apenas consulta)
- ❌ **NÃO gerencia** `transactions` (o Chatbot apenas consulta)
- ❌ **NÃO gerencia** `user_subscriptions` (o Chatbot apenas consulta)
- ❌ **NÃO gerencia** `usage` (o Chatbot apenas consulta)
- ❌ **NÃO gerencia** `ai_models` (o Chatbot apenas consulta)
- ❌ **NÃO gerencia** `ai_subscriptions` (o Chatbot apenas consulta)
- ❌ **NÃO gerencia** `user_ai_settings` (o Chatbot apenas consulta)
- ❌ **NÃO gerencia** `ai_usage_alerts` (o Chatbot apenas consulta)

### **2. Chamadas Diretas aos Providers de IA**
- ❌ **NÃO chama** OpenAI diretamente
- ❌ **NÃO chama** DeepSeek diretamente
- ❌ **NÃO chama** Ollama diretamente
- ✅ **Apenas repassa** requisições ao AI Service, que faz as chamadas

### **3. Cálculo de Custos e Tokens**
- ❌ **NÃO calcula** tokens usados por transação
- ❌ **NÃO calcula** custos por transação
- ❌ **NÃO calcula** métricas agregadas de uso
- ✅ **Apenas consulta** essas informações no AI Service quando necessário

### **4. Controle de Assinaturas e Limites**
- ❌ **NÃO gerencia** planos de assinatura
- ❌ **NÃO controla** limites de uso por assinatura
- ❌ **NÃO verifica** se usuário pode usar IA (o AI Service faz isso)
- ✅ **Apenas consulta** limites antes de chamar IA, mas a verificação final é do AI Service

### **5. Persistência de Conversas**
- ❌ **NÃO salva** conversas no banco de dados
- ❌ **NÃO salva** mensagens no banco de dados
- ❌ **NÃO atualiza** métricas de conversas no banco
- ✅ **Mantém apenas** contexto temporário em Redis (cache)
- ✅ **Consulta** conversas e mensagens do AI Service quando necessário

### **6. Gestão de Modelos e Providers**
- ❌ **NÃO gerencia** configurações de modelos
- ❌ **NÃO gerencia** configurações de providers
- ❌ **NÃO gerencia** APIs dos providers
- ✅ **Apenas consulta** modelos disponíveis no AI Service
- ✅ **Apenas seleciona** qual modelo/provider usar, mas o AI Service faz a chamada

---

## 🔄 **FLUXO DE COMUNICAÇÃO**

```
Frontend 
  ↓
Chatbot Service (Porta 8008/8013)
  ↓ [Filtros/Cache/Validações/Comandos]
  ↓
AI Service (Porta 8012)
  ↓ [Chamadas para Providers]
  ↓
OpenAI / DeepSeek / Ollama
  ↓
AI Service (salva transações, calcula custos)
  ↓
Chatbot Service (formata resposta)
  ↓
Frontend
```

---

## 📊 **RESUMO DA SEPARAÇÃO DE RESPONSABILIDADES**

| Responsabilidade | Chatbot Service | AI Service |
|-----------------|-----------------|------------|
| **Filtros e validações** | ✅ Faz | ❌ Não faz |
| **Cache de respostas** | ✅ Faz | ❌ Não faz |
| **Respostas automáticas** | ✅ Faz | ❌ Não faz |
| **Comandos do e-commerce** | ✅ Faz | ❌ Não faz |
| **Gestão de contexto** | ✅ Faz (em Redis) | ❌ Não faz |
| **Rate limiting** | ✅ Faz | ❌ Não faz |
| **Chamadas aos providers** | ❌ Não faz | ✅ Faz |
| **Persistência no banco** | ❌ Não faz | ✅ Faz |
| **Cálculo de custos** | ❌ Não faz | ✅ Faz |
| **Gestão de assinaturas** | ❌ Não faz | ✅ Faz |
| **Configurações de modelos** | ❌ Não faz | ✅ Faz |

---

## 🎯 **OBJETIVOS DO CHATBOT SERVICE**

1. **Reduzir custos de IA em 40-60%** através de filtros inteligentes e cache
2. **Melhorar tempo de resposta** para perguntas simples em 80%
3. **Manter contexto** em 95% das conversas
4. **Alta disponibilidade** (99.9% uptime)
5. **Experiência fluida** para o usuário final
6. **Segurança** através de validações e sanitização

---

## 🚨 **REGRAS CRÍTICAS**

### **❌ PROIBIÇÕES ABSOLUTAS:**
- ❌ **NENHUM comando DELETE** em qualquer tabela
- ❌ **NENHUMA exclusão direta** de dados no banco
- ❌ **NENHUMA modificação** de dados históricos de transações
- ❌ **NÃO duplicar** tabelas que o AI Service já gerencia
- ❌ **NÃO chamar** providers de IA diretamente

### **✅ O QUE FAZER:**
- ✅ **Consultar** dados no AI Service via endpoints HTTP
- ✅ **Gerenciar apenas** contexto temporário em Redis
- ✅ **Implementar** filtros e cache para otimização
- ✅ **Validar** mensagens antes de enviar ao AI Service
- ✅ **Detectar e executar** comandos do e-commerce

---

## 📝 **NOTAS IMPORTANTES**

- O Chatbot Service é um **middleware de otimização e segurança**
- O AI Service é responsável pela **persistência, chamadas aos providers e gestão de dados de IA**
- O Chatbot Service **NÃO duplica dados**, apenas consulta o AI Service quando necessário
- O Chatbot Service mantém **apenas contexto temporário** em Redis para otimização
- Todas as tabelas de IA são gerenciadas **exclusivamente pelo AI Service**

---

**Última atualização**: 2025-01-XX

