# Problema: Token do Telegram nao configurado

## Diagnostico

O servico esta rodando, mas o **token do Telegram nao esta configurado** no arquivo `.env`.

O arquivo `.env` existe, mas o token esta como placeholder:
```
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
```

## Solucao

### 1. Obter o Token do Bot

1. Abra o Telegram e procure por **@BotFather**
2. Envie o comando `/newbot`
3. Siga as instrucoes:
   - Escolha um nome para o bot (ex: "Meu E-commerce Bot")
   - Escolha um username (deve terminar com `bot`, ex: `meu_ecommerce_bot`)
4. Ao final, o BotFather enviara uma mensagem com o **token**:
   ```
   1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
   ```
5. **Copie esse token**

### 2. Configurar o Token no .env

Edite o arquivo `.env` na pasta `4_messages_apps_services/telegram_service/`:

```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=SEU_TOKEN_AQUI
```

**Exemplo:**
```env
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

### 3. Reiniciar o Servico

Apos configurar o token, **reinicie o servico**:

```bash
# Parar o servico atual (Ctrl+C)
# Depois iniciar novamente:
cd 4_messages_apps_services/telegram_service
python main.py
```

### 4. Verificar se Funcionou

1. Execute o script de verificacao:
   ```bash
   python verificar_servico.py
   ```

2. Envie uma mensagem "oi" para o bot no Telegram

3. Verifique os logs do servico - deve aparecer:
   ```
   INFO: Recebidas 1 atualizacao(oes)
   INFO: Mensagem recebida do Telegram...
   ```

## Validacao do Token

O servico agora valida o token ao iniciar. Se o token nao estiver configurado ou for invalido, o servico nao iniciara e mostrara um erro claro.

## Importante

- **NUNCA compartilhe seu token** publicamente
- **NAO faca commit** do arquivo `.env` no Git (ja esta no .gitignore)
- Se o token for exposto, revogue-o no BotFather com `/revoke` e crie um novo
