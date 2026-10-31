# WhatsApp Gateway (porta 8020)

Gateway fino entre **Evolution API** e o **Chatbot Users** (`8010`).

Não classifica intenção, não grava pedido e não é CRM. Só autentica o webhook, responde 200 e encaminha mensagens **IN** para o chatbot.

```
WhatsApp Oficial → Evolution (Contabo) → Cloudflare Tunnel → este serviço (:8020) → Chatbot (:8010) → outros serviços
```

## Endpoints

| Método | Path | Descrição |
|--------|------|-----------|
| POST | `/api/webhooks/evolution?token=SEGREDO` | Webhook Evolution |
| GET | `/api/webhooks/evolution/recent?token=SEGREDO` | Últimos eventos (ops) |
| GET | `/health` | Health check |
| GET | `/docs` | OpenAPI |

Header alternativo: `X-Webhook-Secret: SEGREDO`.

## Setup local

```powershell
cd services-python\4_messages_apps\whatsapp
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy env.example .env
# edite EVOLUTION_WEBHOOK_SECRET no .env
python main.py
```

Ou:

```powershell
.\start-python-services.ps1 -Only whatsapp -Action restart -EnsureVenv
```

Detalhes do túnel Cloudflare: [EVOLUTION_WEBHOOK_LOCAL.md](./EVOLUTION_WEBHOOK_LOCAL.md).
