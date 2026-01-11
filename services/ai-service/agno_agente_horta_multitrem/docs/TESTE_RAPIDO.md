# 🧪 Teste Rápido do Agente Único

## Como Testar o Agente Atualizado

### 1️⃣ Teste Rápido via Python

Crie um arquivo `teste.py`:

```python
from horta_organica_agent import agente_sitio_multitrem

# Teste 1: Consulta de produtos
print("=== TESTE 1: CONSULTA DE PRODUTOS ===")
agente_sitio_multitrem.print_response(
    "Quais produtos vocês têm disponíveis?",
    stream=True
)

print("\n" + "="*50 + "\n")

# Teste 2: Fazer um pedido completo
print("=== TESTE 2: PEDIDO COMPLETO ===")
agente_sitio_multitrem.print_response(
    "Quero fazer um pedido de 4 alfaces, 2 rúculas e 12 ovos. Meu nome é João Silva, telefone (11) 98765-4321, endereço Rua das Flores, 123",
    stream=True
)
```

Execute:
```powershell
uv run python teste.py
```

---

### 2️⃣ Teste Interativo com Exemplos

Execute o script de exemplos:

```powershell
uv run python exemplos_uso.py
```

Escolha uma das opções:
- **1**: Pergunta sobre produtos
- **2**: Fazer um pedido simples
- **3**: Pedido com agendamento
- **4**: Pedido completo (venda + pagamento + agendamento)
- **5**: Dúvida sobre produtos orgânicos
- **6**: Consultar estatísticas

---

### 3️⃣ Testes Específicos por Funcionalidade

#### Teste de Vendas
```python
from horta_organica_agent import agente_sitio_multitrem

agente_sitio_multitrem.print_response(
    "Quanto custa a alface e a rúcula? Quero comprar 4 alfaces e 2 rúculas",
    stream=True
)
```

**O que esperar:**
- Lista de produtos com preços
- Cálculo do total
- Aplicação de desconto (se aplicável)
- Informação sobre taxa de entrega
- Tom amigável e entusiasmado

---

#### Teste de Agendamento
```python
from horta_organica_agent import agente_sitio_multitrem

agente_sitio_multitrem.print_response(
    "Quero agendar a entrega do meu pedido para segunda-feira de manhã",
    stream=True
)
```

**O que esperar:**
- Verificação de disponibilidade
- Opções de horários
- Confirmação de endereço
- Tom organizado e objetivo

---

#### Teste de Pagamento
```python
from horta_organica_agent import agente_sitio_multitrem

agente_sitio_multitrem.print_response(
    "Como posso pagar? Aceita PIX?",
    stream=True
)
```

**O que esperar:**
- Lista de métodos de pagamento
- Instruções para PIX
- Informação sobre métodos disponíveis
- Tom claro e confiável

---

#### Teste de Suporte
```python
from horta_organica_agent import agente_sitio_multitrem

agente_sitio_multitrem.print_response(
    "Quais são os benefícios dos produtos orgânicos comparados aos convencionais?",
    stream=True
)
```

**O que esperar:**
- Informações nutricionais
- Comparação detalhada
- Dicas de armazenamento
- Tom educativo e didático

---

### 4️⃣ Teste do Fluxo Completo

Este teste simula um cliente fazendo um pedido completo:

```python
from horta_organica_agent import agente_sitio_multitrem

# Passo 1: Cliente pergunta sobre produtos
agente_sitio_multitrem.print_response(
    "Olá! Quero comprar produtos orgânicos. O que vocês têm?",
    session_id="cliente_teste_001",
    stream=True
)

print("\n" + "="*50 + "\n")

# Passo 2: Cliente faz o pedido
agente_sitio_multitrem.print_response(
    "Quero 4 alfaces, 2 rúculas e 12 ovos. Meu nome é Maria Santos, telefone (11) 91234-5678",
    session_id="cliente_teste_001",
    stream=True
)

print("\n" + "="*50 + "\n")

# Passo 3: Cliente agenda entrega
agente_sitio_multitrem.print_response(
    "Quero entregar na segunda-feira. Endereço: Rua das Palmeiras, 456, Bairro Centro, Cidade São Paulo",
    session_id="cliente_teste_001",
    stream=True
)

print("\n" + "="*50 + "\n")

# Passo 4: Cliente quer pagar
agente_sitio_multitrem.print_response(
    "Vou pagar por PIX. Como faço?",
    session_id="cliente_teste_001",
    stream=True
)
```

**O que esperar:**
1. **Vendas**: Apresenta produtos, calcula total com desconto e taxa
2. **Agendamento**: Confirma horário e endereço
3. **Pagamento**: Fornece chave PIX e instruções
4. **Contexto mantido**: O agente mantém o contexto do pedido completo

---

### 5️⃣ Verificar Dados no Banco

Após os testes, verifique os dados salvos:

```powershell
uv run python consultas.py
```

Escolha:
- **1**: Listar todos os clientes
- **2**: Listar todos os pedidos
- **3**: Listar agendamentos
- **4**: Ver estatísticas

---

## ✅ Checklist de Validação

Após os testes, verifique se:

### Funcionalidade de Vendas
- [ ] Apresenta lista completa de produtos
- [ ] Informa preços corretos
- [ ] Calcula descontos (20% para >3 hortaliças)
- [ ] Informa taxa de entrega (grátis acima de R$ 30)
- [ ] Menciona frete grátis acima de R$ 30
- [ ] Tom amigável e entusiasmado

### Funcionalidade de Agendamento
- [ ] Informa horários corretos (Seg, Qua, Sex, Sáb - manhã)
- [ ] Oferece apenas os dias disponíveis
- [ ] Confirma endereço completo
- [ ] Tom organizado e objetivo

### Funcionalidade de Pagamento
- [ ] Lista 4 métodos de pagamento (PIX, Crédito, Débito, Dinheiro)
- [ ] Fornece chave PIX correta
- [ ] Explica parcelamento (3x sem juros acima de R$ 100)
- [ ] Tom claro e confiável

### Funcionalidade de Suporte
- [ ] Responde dúvidas sobre produtos orgânicos
- [ ] Fornece informações nutricionais
- [ ] Dá dicas de armazenamento
- [ ] Tom educativo e didático

### Agente Único
- [ ] Mantém contexto da conversa
- [ ] Coordena fluxo completo de pedido (Vendas -> Agendamento -> Pagamento)
- [ ] Tom acolhedor e profissional

---

## 🐛 Problemas Comuns

### Erro: "OPENAI_API_KEY not found"
**Solução**: Configure o arquivo `.env`:
```bash
copy env.example .env
# Edite .env e adicione sua chave
```

### Erro: "No module named 'agno'"
**Solução**: Instale as dependências:
```bash
uv sync
```

### Erro: "Database not found"
**Solução**: Inicialize o banco:
```bash
uv run python init_db.py
```

---

## 📊 Exemplos de Saída Esperada

### Exemplo 1: Consulta de Produtos
```
🛒 Agente Vendas:
Olá! Que bom ter você aqui! 😊

Temos produtos fresquinhos colhidos hoje! Veja nossas opções:

**Verduras e Folhas:**
- Alface (maço) - R$ 4,00
- Rúcula (maço) - R$ 5,00
- Couve (maço) - R$ 3,50
...

Todos 100% orgânicos, sem agrotóxicos! O que te interessa?
```

### Exemplo 2: Cálculo de Pedido
```
🛒 Agente Vendas:
Perfeito! Vou calcular seu pedido:

- 2kg de Tomate: R$ 16,00
- 1 maço de Rúcula: R$ 5,00
- 1kg de Cenoura: R$ 6,00

Subtotal: R$ 27,00
Desconto (0%): R$ 0,00
Taxa de entrega (3km): R$ 5,00

**Total: R$ 32,00**

Posso confirmar seu pedido?
```

---

## 🎯 Próximos Passos

Após validar os prompts:
1. Teste com casos extremos (pedidos muito grandes, distâncias longas)
2. Verifique persistência no banco de dados
3. Teste o AgentOS via interface web
4. Ajuste prompts conforme necessário

---

**Última Atualização**: 10 de Janeiro de 2026
