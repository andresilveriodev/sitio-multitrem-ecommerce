# Comando /menu - Menu Principal com Botões

## Descrição

O comando `/menu` exibe um menu principal com botões interativos no Telegram, permitindo navegação rápida pelas principais funcionalidades do sistema.

## Uso

### Comando
```
/menu
```

### Aliases
- `menu`
- `m`
- `início`
- `inicio`
- `home`

## Botões do Menu

O menu exibe 6 botões organizados em 3 linhas com 2 colunas:

| Botão | Callback Data | Descrição |
|-------|--------------|-----------|
| 📦 Pedidos | `menu_pedidos` | Acessa funcionalidades de pedidos |
| 🚚 Entregas | `menu_entregas` | Acessa funcionalidades de entregas |
| 🥬 Estoque | `menu_estoque` | Acessa funcionalidades de estoque |
| 💰 Financeiro | `menu_financeiro` | Acessa funcionalidades financeiras |
| 👤 Clientes | `menu_clientes` | Acessa funcionalidades de clientes |
| ⚙️ Admin | `menu_admin` | Acessa funcionalidades administrativas |

## Formato de Resposta

Quando o comando `/menu` é executado, a resposta inclui:

```json
{
  "success": true,
  "response": "Menu Principal - Selecione uma opção:",
  "telegram_keyboard": {
    "inline_keyboard": [
      [
        {"text": "📦 Pedidos", "callback_data": "menu_pedidos"},
        {"text": "🚚 Entregas", "callback_data": "menu_entregas"}
      ],
      [
        {"text": "🥬 Estoque", "callback_data": "menu_estoque"},
        {"text": "💰 Financeiro", "callback_data": "menu_financeiro"}
      ],
      [
        {"text": "👤 Clientes", "callback_data": "menu_clientes"},
        {"text": "⚙️ Admin", "callback_data": "menu_admin"}
      ]
    ]
  },
  "metadata": {
    "user_id": "123",
    "username": "usuario",
    "command_id": "show_menu",
    "is_command": true
  }
}
```

## Implementação

### Arquivos Modificados

1. **`services/commands/definitions.py`**
   - Adicionada função `show_menu_action()`
   - Adicionado comando `show_menu` em `VIEW_COMMANDS`

2. **`services/commands/analyzer.py`**
   - Ajustada função `_normalize_message()` para preservar "/" em comandos
   - Ajustada função `_build_command_patterns()` para detectar comandos com "/"
   - Ajustada função `_check_permissions()` para permitir comandos sem permissões

3. **`routes/telegram_router.py`**
   - Adicionado suporte para retornar `telegram_keyboard` na resposta

## Próximos Passos

Para completar a funcionalidade, é necessário:

1. **Implementar handlers para callback_data**
   - Criar handlers para processar `menu_pedidos`, `menu_entregas`, etc.
   - Cada handler deve executar a ação correspondente

2. **Integrar com o webhook do Telegram**
   - O webhook do Telegram deve processar `callback_query` quando um botão for clicado
   - Enviar a resposta apropriada baseada no `callback_data`

3. **Adicionar navegação**
   - Implementar submenus para cada seção
   - Adicionar botão "Voltar" nos submenus

## Exemplo de Uso no Telegram

```
Usuário: /menu

Bot: Menu Principal - Selecione uma opção:
     [📦 Pedidos] [🚚 Entregas]
     [🥬 Estoque] [💰 Financeiro]
     [👤 Clientes] [⚙️ Admin]
```

Quando o usuário clicar em um botão, o Telegram enviará um `callback_query` com o `callback_data` correspondente, que deve ser processado pelo sistema.
