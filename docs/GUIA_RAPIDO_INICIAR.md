# 🚀 GUIA RÁPIDO - Como Iniciar o Sistema

## ⚡ Início Rápido (3 Terminais)

### Terminal 1: Evolution API (Docker)
```powershell
cd "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02\services\evolution-api"
docker-compose up -d
```

### Terminal 2: Agno AgentOS (Python)
```powershell
cd "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02\services\ai-service\agno-agent"
.\.venv\Scripts\Activate.ps1
python my_os.py
```

### Terminal 3: WhatsApp Service (NestJS)
```powershell
cd "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02\services\whatsapp-service"
npm run start:dev
```

---

## ✅ Verificar Status

### Evolution API
```powershell
# Verificar se está rodando
docker ps | Select-String "evolution"

# Ver logs
docker logs evolution_api --tail 50
```

### Agno AgentOS
**Deve aparecer:**
```
============================================================
SITIO MULTITREM - AGENTOS
============================================================
Porta: 7777 (padrao AgentOS)
App Interface: http://localhost:7777
API Docs: http://localhost:7777/docs
```

### WhatsApp Service
**Deve aparecer:**
```
✅ Redis conectado com sucesso
🚀 Redis pronto para uso
📱 WhatsApp Service running on port 3006
```

---

## 🧪 Testar Sistema

```powershell
cd "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02\services\evolution-api"
node test-webhook-direct.js
```

**Resultado esperado:**
```json
{
  "processed": true,
  "aiResponse": "Olá! 😊 Que bom que você está interessado..."
}
```

---

## 🛑 Parar Tudo

```powershell
# Parar Evolution API
cd "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02\services\evolution-api"
docker-compose down

# Parar Agno (Ctrl+C no terminal)
# Parar WhatsApp Service (Ctrl+C no terminal)
```

---

## 🔧 Problemas Comuns

### Docker não inicia
```powershell
# Iniciar Docker Desktop manualmente
# Aguardar até estar "running"
# Tentar novamente: docker-compose up -d
```

### Agno não encontra chave OpenAI
```powershell
# Verificar arquivo .env
cat "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02\services\ai-service\agno-agent\.env"
# Deve conter: OPENAI_API_KEY=sk-...
```

### WhatsApp Service erro Redis
```powershell
# Verificar se Redis está rodando no Docker
docker ps | Select-String "redis"
# Verificar .env não tem REDIS_PASSWORD
```

---

## 📦 Portas Usadas

- **7777** - Agno AgentOS
- **3006** - WhatsApp Service
- **8080** - Evolution API
- **6379** - Redis (Docker)
- **5432** - PostgreSQL (Docker)

**Nota:** O Evolution Frontend (UI web) foi desabilitado para evitar conflitos de porta. Se precisar, edite `docker-compose.yaml` e escolha uma porta livre.

---

## 🎯 URLs Importantes

- **Agno Docs:** http://localhost:7777/docs
- **Agno Config:** http://localhost:7777/config
- **WhatsApp Service:** http://localhost:3006/api/docs
- **Evolution API:** http://localhost:8080 (use Postman/Insomnia)

---

## 📞 Conectar WhatsApp (Primeira Vez)

```powershell
cd "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02\services\evolution-api"
node connect-whatsapp.js
# Escanear QR Code com WhatsApp Web
```

---

**✅ Sistema pronto para uso!**


