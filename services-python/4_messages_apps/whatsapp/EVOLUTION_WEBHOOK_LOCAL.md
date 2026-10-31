# Teste local — Evolution API + Cloudflare Tunnel

Fluxo:

```
WhatsApp → Evolution (Contabo) → Cloudflare Tunnel → localhost:8020 → Chatbot :8010
```

## 1. Subir o gateway

```powershell
cd F:\repositorios\sitio-multitrem-ecommerce\services-python
.\start-python-services.ps1 -Only whatsapp -Action restart -EnsureVenv
```

Confirme `EVOLUTION_WEBHOOK_SECRET` no `.env` do serviço (`4_messages_apps\whatsapp\.env`).

Opcional (para ver o forward):

```powershell
.\start-python-services.ps1 -Only bot_users -Action restart
```

Health: http://localhost:8020/health

## 2. Cloudflare Tunnel (Windows)

```powershell
winget install --id Cloudflare.cloudflared
```

Novo terminal:

```powershell
cloudflared tunnel --url http://localhost:8020
```

Anote a URL `https://….trycloudflare.com` (muda a cada reinício do túnel rápido).

## 3. Evolution Manager

Instância `sitio-multitrem` → Events → Webhook:

| Campo | Valor |
|-------|--------|
| Enabled | On |
| URL | `https://SEU-TUNEL.trycloudflare.com/api/webhooks/evolution?token=SEU_SEGREDO` |
| Webhook by Events | Off |
| Webhook Base64 | Off |

Eventos:

- `MESSAGES_UPSERT`
- `MESSAGES_UPDATE`
- `MESSAGES_DELETE`
- `CHATS_UPSERT`
- `CHATS_UPDATE`
- `CONTACTS_UPSERT`
- `CONNECTION_UPDATE`

## 4. Validar

1. Envie uma mensagem de **outro** WhatsApp para o número da instância.
2. Confira logs do gateway e/ou:

```powershell
curl "http://localhost:8020/api/webhooks/evolution/recent?token=SEU_SEGREDO"
```

3. Se `bot_users` estiver no ar, deve aparecer request em `:8010`.

O gateway **não** responde no WhatsApp nesta fase.

## Segurança

- O túnel é público: use segredo forte e não exponha outros serviços no mesmo túnel.
- Não registre o token em logs.
- PC/túnel desligado = webhooks perdidos. Para produção contínua, receptor permanente na Contabo.

## Teste local sem Evolution

```powershell
curl -X POST "http://localhost:8020/api/webhooks/evolution?token=SEU_SEGREDO" `
  -H "Content-Type: application/json" `
  -d '{
    "event": "MESSAGES_UPSERT",
    "instance": "sitio-multitrem",
    "data": {
      "key": { "remoteJid": "5511999999999@s.whatsapp.net", "fromMe": false, "id": "TESTE123" },
      "pushName": "Teste",
      "message": { "conversation": "ola do curl" }
    }
  }'
```
