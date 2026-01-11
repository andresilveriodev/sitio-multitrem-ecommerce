# 📚 Exemplos de Uso - Agente Horta Multitrem

Este documento contém exemplos práticos de como usar o sistema.

## 🚀 Executando Exemplos

### Exemplo 1: Script Interativo

Execute o script de exemplos:

```bash
uv run python exemplos_uso.py
```

Este script oferece um menu interativo com vários exemplos.

### Exemplo 2: Consultas ao Banco de Dados

Execute o script de consultas:

```bash
uv run python consultas.py
```

Este script permite consultar dados diretamente do banco.

## 💡 Exemplos de Conversas

### Exemplo 1: Dúvida sobre Produto

**Usuário:**
```
Quais são os benefícios do tomate orgânico?
```

**Sistema:**
O agente principal responde com informações detalhadas sobre os benefícios nutricionais e ambientais.

### Exemplo 2: Consulta de Produtos

**Usuário:**
```
Quais produtos vocês têm disponíveis?
```

**Sistema:**
O agente lista todos os produtos disponíveis organizados por categoria.

### Exemplo 3: Pedido Completo

**Passo 1 - Cadastro:**
```
Usuário: Quero me cadastrar. Meu nome é Maria Santos, email maria@email.com, telefone (11) 98888-8888, endereço Av. Principal, 456
```

**Passo 2 - Pedido:**
```
Usuário: Quero comprar 2kg de tomate orgânico, 1 maço de rúcula e 1 bandeja de morango
```

**Passo 3 - Pagamento:**
```
Usuário: Quero pagar com PIX
```

**Passo 4 - Agendamento:**
```
Usuário: Pode entregar amanhã às 15h?
```

**Sistema:**
O agente coordena todo o fluxo completo de atendimento.

### Exemplo 4: Suporte Técnico

**Usuário:**
```
Como devo armazenar os produtos orgânicos para manter a frescura?
```

**Sistema:**
O agente de suporte fornece dicas detalhadas sobre armazenamento.

### Exemplo 5: Receita

**Usuário:**
```
Você tem alguma receita com espinafre orgânico?
```

**Sistema:**
O agente de suporte pode buscar receitas e fornecer instruções.

## 🔧 Uso Programático

### Exemplo: Usar o Agente Único

```python
from horta_organica_agent import agente_sitio_multitrem

# Para dúvidas gerais
resposta = agente_sitio_multitrem.run(
    "Quais são os benefícios da agricultura orgânica?"
)
print(resposta.content)

# Para fazer pedidos
resposta = agente_sitio_multitrem.run(
    "Quero comprar 4 alfaces e 12 ovos",
    session_id="sessao_001",
    user_id="usuario_001"
)
print(resposta.content)
```

### Exemplo: Consultar Estatísticas

```python
from utils import obter_estatisticas

stats = obter_estatisticas()
print(f"Total de clientes: {stats['total_clientes']}")
print(f"Total de pedidos: {stats['total_pedidos']}")
print(f"Valor total: R$ {stats['valor_total_confirmado']:.2f}")
```

### Exemplo: Listar Dados

```python
from utils import listar_clientes, listar_pedidos

# Listar clientes
clientes = listar_clientes()
for cliente in clientes:
    print(f"{cliente['nome']} - {cliente['email']}")

# Listar pedidos pendentes
pedidos = listar_pedidos(status="pendente")
for pedido in pedidos:
    print(f"Pedido #{pedido['id']}: R$ {pedido['valor_total']:.2f}")
```

### Exemplo: Relatório de Vendas

```python
from utils import obter_relatorio_vendas

# Relatório do último mês
from datetime import datetime, timedelta
hoje = datetime.now()
um_mes_atras = hoje - timedelta(days=30)

relatorio = obter_relatorio_vendas(
    data_inicio=um_mes_atras.strftime("%Y-%m-%d"),
    data_fim=hoje.strftime("%Y-%m-%d")
)

print(f"Total de vendas: {relatorio['total_vendas']}")
print(f"Valor total: R$ {relatorio['valor_total']:.2f}")
print(f"Ticket médio: R$ {relatorio['ticket_medio']:.2f}")
```

## 🎯 Casos de Uso Comuns

### 1. Atendimento ao Cliente

O sistema pode ser usado para:
- Responder dúvidas sobre produtos
- Fornecer informações nutricionais
- Dar dicas de preparo e armazenamento
- Explicar diferenças entre orgânicos e convencionais

### 2. Processamento de Pedidos

O sistema pode:
- Cadastrar novos clientes
- Criar pedidos
- Processar pagamentos
- Agendar entregas

### 3. Relatórios e Análises

O sistema permite:
- Consultar estatísticas gerais
- Gerar relatórios de vendas
- Analisar produtos mais vendidos
- Acompanhar status de pedidos

## 📝 Notas Importantes

1. **Sessões**: Use `session_id` e `user_id` consistentes para manter o contexto da conversa.

2. **IDs**: Os IDs de clientes, pedidos, etc. são números inteiros. O sistema converte strings automaticamente.

3. **Status**: Os status válidos são:
   - Pedidos: `pendente`, `confirmado`, `cancelado`, `entregue`
   - Agendamentos: `agendado`, `confirmado`, `entregue`, `cancelado`
   - Pagamentos: `processado`, `confirmado`, `cancelado`, `reembolsado`

4. **Datas**: Use formato `YYYY-MM-DD` para datas.

5. **Horários**: Use formato `HH:MM` (24 horas) para horários.

## 🐛 Troubleshooting

Se encontrar erros:

1. Verifique se o banco de dados está inicializado
2. Verifique se a API key está configurada
3. Verifique os logs de erro
4. Consulte a documentação completa em `docs/DOCUMENTACAO_HORTA_ORGANICA.md`
