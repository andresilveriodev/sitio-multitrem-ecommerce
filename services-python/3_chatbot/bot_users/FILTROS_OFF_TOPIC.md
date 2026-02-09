# 🚫 Filtros de Assuntos Fora do Contexto (Off-Topic)

## 📋 Visão Geral

O Chatbot Service agora possui filtros inteligentes para detectar assuntos que **não são relacionados ao e-commerce** e responder de forma simpática sem chamar a IA, **economizando custos** para a empresa.

## 🎯 Objetivo

Evitar que conversas sobre assuntos não relacionados ao e-commerce (clima, notícias, entretenimento, etc.) gerem custos desnecessários com chamadas à IA.

## 🔍 Como Funciona

### 1. **Detecção de Assuntos Off-Topic**

O sistema verifica se a mensagem contém palavras-chave relacionadas a:
- ❌ **Clima e tempo** (clima, chuva, sol, temperatura)
- ❌ **Notícias gerais** (notícias, política, eleição)
- ❌ **Entretenimento** (filmes, séries, música, futebol)
- ❌ **Educação geral** (história, geografia, matemática)
- ❌ **Saúde e medicina** (medicina, médico, remédio)
- ❌ **Tecnologia geral** (programação, código, desenvolvimento)
- ❌ **Conversas casuais** (como você está, onde você mora)
- ❌ **Assuntos pessoais** (família, relacionamento, filhos)

### 2. **Palavras-Chave de E-Commerce (Contexto Válido)**

O sistema também identifica palavras-chave relacionadas ao e-commerce:
- ✅ **Produtos e compras** (produto, comprar, carrinho, pedido)
- ✅ **Preços e ofertas** (preço, desconto, promoção, cupom)
- ✅ **Pedidos e entregas** (rastrear, status, entrega, frete)
- ✅ **Conta e perfil** (minha conta, endereço, cadastro)
- ✅ **Suporte** (dúvida, ajuda, garantia, especificação)

### 3. **Respostas de Escape Simpáticas**

Quando detecta assunto off-topic, o sistema retorna uma resposta simpática **SEM chamar a IA**:

```
"Olá! Sou especializado em ajudar com produtos, pedidos e dúvidas sobre compras 
no nosso e-commerce. Como posso ajudá-lo com isso hoje?"
```

## 🔄 Fluxo de Processamento

```
Mensagem do Usuário
    ↓
Validação de Segurança
    ↓
Verificação de Filtros
    ↓
É Off-Topic? → SIM → Resposta de Escape (SEM IA) → FIM
    ↓ NÃO
Tem Resposta Automática? → SIM → Resposta Automática (SEM IA) → FIM
    ↓ NÃO
É Comando? → SIM → Executa Comando → FIM
    ↓ NÃO
Precisa de IA? → SIM → Chama IA Service → FIM
```

## 💰 Economia de Custos

### Antes da Implementação:
- ❌ Todas as mensagens chamavam a IA
- ❌ Conversas sobre clima, notícias, etc. geravam custos
- ❌ Sem controle sobre assuntos off-topic

### Depois da Implementação:
- ✅ Assuntos off-topic recebem resposta automática (SEM IA)
- ✅ Apenas mensagens relacionadas ao e-commerce chamam a IA
- ✅ Redução estimada de **30-50%** nas chamadas à IA
- ✅ Respostas instantâneas para assuntos off-topic

## 📊 Exemplos

### ❌ Assunto Off-Topic (NÃO chama IA):
```
Usuário: "Como está o clima hoje?"
Bot: "Olá! Sou especializado em ajudar com produtos, pedidos e dúvidas sobre 
     compras no nosso e-commerce. Como posso ajudá-lo com isso hoje?"
```

### ✅ Assunto Relacionado ao E-Commerce (chama IA):
```
Usuário: "Quero comprar um produto"
Bot: [Resposta da IA sobre produtos disponíveis]
```

### ✅ Assunto Relacionado ao E-Commerce (chama IA):
```
Usuário: "Qual o status do meu pedido?"
Bot: [Resposta da IA sobre status do pedido]
```

## ⚙️ Configuração

Os filtros estão configurados em `services/filters/message_filters.py`:

- `ecommerce_keywords`: Palavras-chave relacionadas ao e-commerce
- `off_topic_keywords`: Palavras-chave de assuntos fora do contexto
- `off_topic_responses`: Respostas simpáticas de escape

## 🔧 Personalização

Para adicionar novos assuntos off-topic, edite `off_topic_keywords`:

```python
self.off_topic_keywords = [
    # ... palavras-chave existentes ...
    "novo_assunto", "outro_tema"
]
```

Para adicionar novas respostas de escape, edite `off_topic_responses`:

```python
self.off_topic_responses = [
    # ... respostas existentes ...
    "Nova resposta simpática de escape"
]
```

## 📈 Métricas

O sistema registra quando uma resposta de escape é enviada:

```python
logger.info(
    "Resposta de escape enviada (assunto fora do contexto do e-commerce)",
    user_id=user_id,
    message_preview=message[:50]
)
```

## 🎯 Benefícios

1. **Redução de Custos**: Menos chamadas à IA = menos gastos
2. **Respostas Rápidas**: Respostas instantâneas para assuntos off-topic
3. **Foco no E-Commerce**: Mantém o bot focado no objetivo principal
4. **Experiência do Usuário**: Respostas simpáticas que redirecionam para o contexto correto
