# 🔧 Correção de Erros - Google Calendar

## 📋 Problemas Identificados nos Logs

### 1. ❌ Erro: Parâmetro `time_zone` não aceito

**Erro nos logs:**
```
WARNING  Could not run function create_event(...)        
ERROR    1 validation error for GoogleCalendarTools.create_event
         time_zone
           Unexpected keyword argument
         [type=unexpected_keyword_argument,
         input_value='America/Sao_Paulo', input_type=str]
```

**Causa:**
O método `create_event` do `GoogleCalendarTools` **não aceita** o parâmetro `time_zone`. A biblioteca detecta automaticamente o timezone baseado nas credenciais ou usa o padrão do sistema.

**Correção aplicada:**
- ✅ Removido o parâmetro `time_zone='America/Sao_Paulo'` de todas as instruções
- ✅ Atualizado o formato de chamada do `create_event` para:
  ```python
  create_event(
      title=title,
      start_date=start_date,
      end_date=end_date,
      location=endereco_entrega,
      description=descricao
  )
  ```

**Arquivos corrigidos:**
- `horta_organica_agent.py` (linhas 357-364, 436-444, 454)

---

### 2. ❌ Erro: Serviço não inicializado (`NoneType`)

**Erro nos logs:**
```
WARNING  Could not run function create_event(...)        
ERROR    'NoneType' object has no attribute 'events'     
         Traceback (most recent call last):
           ...
           File "...\agno\tools\googlecalendar.py", line 254, in create_event
             service.events()
             ^^^^^^^^^^^^^^
         AttributeError: 'NoneType' object has no        
         attribute 'events'
```

**Causa:**
O serviço do Google Calendar (`service`) não foi inicializado corretamente. Isso pode acontecer quando:
1. O token OAuth não foi gerado ou expirou
2. A autenticação falhou silenciosamente
3. O arquivo `token.json` está corrompido ou inválido

**Solução:**
1. **Verificar se o token existe:**
   ```bash
   ls -la token.json
   ```

2. **Se o token não existir ou estiver inválido:**
   - Delete o arquivo `token.json` se existir
   - Execute o agente novamente
   - O navegador deve abrir automaticamente para autorização OAuth
   - Faça login e autorize o acesso ao Google Calendar

3. **Verificar se as credenciais estão corretas:**
   - Verifique se o arquivo de credenciais JSON existe
   - Verifique se o formato está correto (deve ser tipo "installed")
   - Verifique se o escopo está correto: `https://www.googleapis.com/auth/calendar`

4. **Verificar logs de inicialização:**
   - Deve aparecer: `✅ Google Calendar Tools inicializado com sucesso!`
   - Se aparecer erro, verifique a mensagem específica

---

### 3. ⚠️ Erro: Porta já em uso

**Erro nos logs:**
```
ERROR    An error occurred: [WinError 10048] Normalmente 
         é permitida apenas uma utilização de cada       
         endereço de soquete (protocolo/endereço de      
         rede/porta)
```

**Causa:**
Outro processo já está usando a porta 7777 (porta padrão do AgentOS).

**Solução:**
1. **Encontrar o processo que está usando a porta:**
   ```bash
   # Windows PowerShell
   netstat -ano | findstr :7777
   ```

2. **Encerrar o processo:**
   ```bash
   # Substitua <PID> pelo número do processo encontrado
   taskkill /PID <PID> /F
   ```

3. **Ou alterar a porta no código:**
   - Edite `horta_organica_agent.py`
   - Procure por `AgentOS(port=7777)`
   - Altere para outra porta (ex: `port=7778`)

---

## ✅ Correções Aplicadas

### 1. Remoção do parâmetro `time_zone`

**Antes:**
```python
create_event(
    title=title,
    start_date=start_date,
    end_date=end_date,
    location=endereco_entrega,
    description=descricao,
    time_zone='America/Sao_Paulo'  # ❌ Este parâmetro não existe
)
```

**Depois:**
```python
create_event(
    title=title,
    start_date=start_date,
    end_date=end_date,
    location=endereco_entrega,
    description=descricao  # ✅ Sem time_zone
)
```

### 2. Atualização das instruções do agente

- ✅ Removido `time_zone` de todas as instruções
- ✅ Atualizado o texto para indicar que o timezone é detectado automaticamente
- ✅ Mantidas todas as outras instruções sobre formatação de data/hora

---

## 🧪 Como Testar

1. **Reinicie o agente:**
   ```bash
   cd services/ai-service/agno_agente_horta_multitrem
   uv run python horta_organica_agent.py
   ```

2. **Verifique a inicialização:**
   - Deve aparecer: `✅ Google Calendar Tools inicializado com sucesso!`
   - Se aparecer erro, siga as soluções acima

3. **Teste criando um agendamento:**
   - Crie um pedido
   - Agende uma entrega
   - Verifique se o evento é criado no Google Calendar

4. **Verifique os logs:**
   - Não deve aparecer mais o erro sobre `time_zone`
   - Se aparecer erro sobre `NoneType`, siga a solução do item 2 acima

---

## 📝 Parâmetros Corretos do `create_event`

Baseado na documentação e testes do Agno Framework, os parâmetros aceitos são:

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `title` | string | ✅ Sim | Título do evento |
| `start_date` | string | ✅ Sim | Data/hora de início (ISO 8601: `YYYY-MM-DDTHH:MM:SS`) |
| `end_date` | string | ✅ Sim | Data/hora de término (ISO 8601: `YYYY-MM-DDTHH:MM:SS`) |
| `description` | string | ❌ Não | Descrição do evento |
| `location` | string | ❌ Não | Localização do evento |
| `attendees` | list | ❌ Não | Lista de emails dos participantes |
| `add_google_meet_link` | boolean | ❌ Não | Adicionar link do Google Meet |

**Parâmetros que NÃO existem:**
- ❌ `time_zone` - O timezone é detectado automaticamente

---

## 🔍 Verificação Pós-Correção

Após aplicar as correções, verifique:

1. ✅ O agente inicia sem erros
2. ✅ A mensagem `✅ Google Calendar Tools inicializado com sucesso!` aparece
3. ✅ Ao criar um agendamento, o evento é criado no Google Calendar
4. ✅ Não aparecem mais erros sobre `time_zone` nos logs
5. ✅ Não aparecem mais erros sobre `NoneType` nos logs

---

## 📚 Referências

- [Documentação do Agno Framework - GoogleCalendarTools](https://docs.agno.com)
- [Troubleshooting Google Calendar](./TROUBLESHOOTING_GOOGLE_CALENDAR.md)
- [Configuração do Google Calendar](./GOOGLE_CALENDAR_CONFIG.md)
