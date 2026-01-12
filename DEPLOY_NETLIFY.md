# 🚀 Deploy no Netlify - Configuração Completa

## ✅ Arquivos Criados/Atualizados

1. **`netlify.toml`** - Configuração principal do Netlify
2. **`frontend/.nvmrc`** - Versão do Node.js (20)
3. **`frontend/env.example`** - Exemplo de variáveis de ambiente
4. **`frontend/NETLIFY_DEPLOY.md`** - Guia completo de deploy
5. **`frontend/README_NETLIFY.md`** - Guia rápido

## 📋 Checklist Pré-Deploy

### 1. Testar Build Local

```bash
cd frontend
npm install
npm run build
npm start
```

Se funcionar localmente, está pronto!

### 2. Configurar Variáveis de Ambiente no Netlify

No painel do Netlify (Site settings > Environment variables), adicione:

| Variável | Valor Exemplo | Obrigatório |
|----------|---------------|-------------|
| `NEXT_PUBLIC_API_URL` | `https://api.sitio-multitrem.com/api` | ✅ Sim |
| `NEXT_PUBLIC_APP_URL` | `https://seu-site.netlify.app` | ✅ Sim |
| `NEXT_PUBLIC_KEYCLOAK_CLIENT_ID` | `sitio-multitrem-app` | ⚠️ Opcional |

### 3. Conectar Repositório

1. Acesse [app.netlify.com](https://app.netlify.com)
2. **Add new site** > **Import an existing project**
3. Conecte com GitHub
4. Selecione o repositório
5. O Netlify detectará automaticamente o `netlify.toml`

### 4. Configurações Automáticas

O `netlify.toml` já está configurado com:
- ✅ Base directory: `frontend`
- ✅ Build command: `npm install && npm run build`
- ✅ Publish directory: `frontend/.next`
- ✅ Node.js 20
- ✅ Plugin Next.js oficial
- ✅ Headers de segurança
- ✅ Cache otimizado

## 🎯 Passos para Deploy

1. **Commit e Push:**
   ```bash
   git add .
   git commit -m "Configuração para deploy no Netlify"
   git push origin main
   ```

2. **No Netlify:**
   - O deploy iniciará automaticamente
   - Aguarde 2-5 minutos
   - Verifique os logs se houver erros

3. **Verificar:**
   - Site carrega: `https://seu-site.netlify.app`
   - Imagens aparecem
   - Funcionalidades funcionam

## 🔧 Configurações do netlify.toml

### Build
- Base: `frontend`
- Command: `npm install && npm run build`
- Publish: `frontend/.next`
- Node: 20

### Segurança
- Headers de segurança configurados
- XSS Protection
- Content-Type Options
- Frame Options

### Performance
- Cache para imagens (1 ano)
- Cache para assets estáticos (1 ano)
- Minificação ativada

## 🐛 Solução de Problemas

### Build Falha
1. Verifique logs no Netlify
2. Teste build local: `npm run build`
3. Verifique dependências

### Imagens Não Aparecem
1. Verifique se estão em `frontend/public/images/`
2. Use caminhos: `/images/products/nome.jpg`
3. Verifique console do navegador

### API Não Funciona
1. Verifique `NEXT_PUBLIC_API_URL`
2. Configure CORS no backend
3. Use HTTPS em produção

## 📚 Documentação

- **Guia Completo:** `frontend/NETLIFY_DEPLOY.md`
- **Guia Rápido:** `frontend/README_NETLIFY.md`
- **Variáveis:** `frontend/env.example`

## ✨ Próximos Passos

1. ✅ Fazer deploy inicial
2. ✅ Configurar domínio personalizado (opcional)
3. ✅ Configurar SSL (automático)
4. ✅ Monitorar performance
5. ✅ Configurar analytics (opcional)

---

**Tudo pronto para deploy! 🚀**
