# Prompts Atualizados - Sítio Multitrem

## 📋 Resumo das Atualizações

Todos os prompts dos agentes foram atualizados com informações detalhadas do **Sítio Multitrem**, incluindo produtos, preços, regras de negócio e diretrizes de comunicação.

---

## 🛒 AGENTE VENDAS

### Produtos e Preços Cadastrados:

#### Verduras e Folhas:
- Alface (maço) - R$ 4,00
- Rúcula (maço) - R$ 5,00
- Couve (maço) - R$ 3,50
- Espinafre (maço) - R$ 4,50
- Agrião (maço) - R$ 4,00

#### Legumes:
- Tomate (kg) - R$ 8,00
- Cenoura (kg) - R$ 6,00
- Beterraba (kg) - R$ 5,50
- Abobrinha (kg) - R$ 7,00
- Pepino (kg) - R$ 6,50
- Pimentão (kg) - R$ 9,00

#### Temperos:
- Cebolinha (maço) - R$ 2,50
- Salsinha (maço) - R$ 2,50
- Coentro (maço) - R$ 3,00
- Manjericão (maço) - R$ 4,00

#### Raízes:
- Batata-doce (kg) - R$ 5,00
- Mandioca (kg) - R$ 4,50
- Inhame (kg) - R$ 6,00

### Regras de Desconto:
- Compras acima de R$ 50,00: **5% de desconto**
- Compras acima de R$ 100,00: **10% de desconto**
- Compras acima de R$ 200,00: **15% de desconto**

### Taxa de Entrega:
- Até 5 km: R$ 5,00
- De 5 a 10 km: R$ 10,00
- Acima de 10 km: R$ 15,00
- **Compras acima de R$ 150,00: FRETE GRÁTIS**

### Características:
- Tom amigável e acolhedor
- Processo de venda estruturado em 9 passos
- Raciocínio passo a passo antes de cada ação
- Proativo em sugerir produtos complementares

---

## 📅 AGENTE AGENDAMENTO

### Horários de Entrega:
- **Segunda a Sexta**: 08:00 às 18:00
- **Sábado**: 08:00 às 12:00
- **Domingo**: NÃO fazemos entregas

### Períodos Disponíveis:
- **Manhã**: 08:00 às 12:00
- **Tarde**: 13:00 às 18:00 (segunda a sexta)
- **Sábado**: apenas período da manhã

### Prazo de Entrega:
- Pedidos até 12:00: entrega no mesmo dia (se houver disponibilidade)
- Pedidos após 12:00: entrega no próximo dia útil

### Características:
- Tom organizado e objetivo
- Confirma sempre todos os detalhes
- Processo de agendamento em 9 passos
- Verifica se alguém estará em casa

---

## 💳 AGENTE PAGAMENTO

### Métodos de Pagamento:

1. **PIX (preferencial)**
   - Chave: sitio.multitrem@email.com
   - Confirmação imediata
   - Desconto adicional de 2%

2. **Cartão de Crédito**
   - Todas as bandeiras
   - Até 3x sem juros (compras acima de R$ 100)
   - Confirmação em até 2 horas

3. **Cartão de Débito**
   - Todas as bandeiras
   - Confirmação imediata

4. **Dinheiro**
   - Pagamento na entrega
   - Cliente deve ter troco

### Descontos Totais:
- Descontos por valor de compra (5%, 10%, 15%)
- **+2% adicional para pagamento via PIX**

### Política de Reembolso:
- Produtos com defeito: reembolso integral em até 7 dias
- Cancelamento antes da entrega: reembolso integral
- Cancelamento após entrega: apenas com produto lacrado

### Características:
- Tom claro e transparente
- Transmite confiança e segurança
- Processo de pagamento em 11 passos
- Foco em segurança dos dados

---

## 🆘 AGENTE SUPORTE

### Áreas de Conhecimento:
- Benefícios nutricionais dos produtos orgânicos
- Diferenças entre orgânicos e convencionais
- Armazenamento e conservação
- Dicas de preparo e receitas
- Cultivo orgânico
- Sustentabilidade e impacto ambiental
- Certificações orgânicas
- Sazonalidade dos produtos

### Características:
- Tom educado, paciente e empático
- Linguagem acessível e didática
- Demonstra paixão pelos produtos orgânicos
- Usa DuckDuckGoTools para informações científicas
- Sempre cita fontes confiáveis

---

## 🤖 AGENTE ÚNICO - ASSISTENTE SÍTIO MULTITREM

### Função:
Assistente completo responsável por todo o atendimento ao cliente:
- **Vendas**: Apresentação de produtos, criação de pedidos
- **Suporte**: Dúvidas sobre produtos orgânicos, benefícios, receitas
- **Agendamento**: Coletar endereço e agendar entregas
- **Pagamento**: Processar pagamentos em todos os métodos disponíveis

### Fluxo Completo de Pedido:
1. **Vendas**: Apresenta produtos e cria o pedido
2. **Agendamento**: Coleta endereço completo e agenda a entrega
3. **Pagamento**: Processa o pagamento
4. **Suporte**: Tira dúvidas a qualquer momento durante o processo

### Tópicos que Domina:
- Benefícios dos produtos orgânicos
- Impacto ambiental da agricultura orgânica
- Certificações e regulamentações
- Sazonalidade de produtos
- Técnicas de cultivo sustentável
- Conservação de alimentos
- Receitas e preparos saudáveis
- Processamento de pedidos
- Métodos de pagamento
- Agendamento de entregas

### Valores do Sítio Multitrem:
- Qualidade acima de tudo
- Transparência total com o cliente
- Sustentabilidade em cada ação
- Saúde e bem-estar das famílias
- Respeito à natureza e às pessoas

---

## ✅ Verificação

O agente único foi testado e está funcionando corretamente:
- ✅ Agente Único: `assistente_sitio_multitrem`

---

## 🚀 Como Testar

Execute os exemplos de uso:

```powershell
cd agente_horta_multitrem
uv run python exemplos_uso.py
```

Ou teste diretamente no código:

```python
from horta_organica_agent import agente_sitio_multitrem

agente_sitio_multitrem.print_response(
    "Quero comprar 4 alfaces e 12 ovos",
    stream=True
)
```

---

## 📝 Observações Importantes

1. **Raciocínio Passo a Passo**: Todos os agentes foram instruídos a pensar antes de agir, seguindo uma lista de verificação específica para cada função.

2. **Tom de Comunicação**: Cada agente tem um tom específico adequado à sua função:
   - Vendas: Amigável e entusiasmado
   - Suporte: Educado e didático
   - Agendamento: Organizado e objetivo
   - Pagamento: Claro e confiável

3. **Integração**: Os agentes trabalham de forma coordenada através do Team, proporcionando uma experiência fluida ao cliente.

4. **Persistência**: Todas as operações são salvas no banco de dados SQLite (`tmp/data.db`).

---

**Data da Atualização**: 10 de Janeiro de 2026
**Versão**: 2.0 - Prompts Completos Sítio Multitrem
