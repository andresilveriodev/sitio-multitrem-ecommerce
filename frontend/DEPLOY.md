# 🚀 Guia de Deploy - Sítio Multitrem

Este guia explica como fazer o deploy do projeto Next.js em diferentes plataformas.

## 📋 Pré-requisitos

1. Conta no GitHub (já temos o repositório)
2. Conta na plataforma de deploy escolhida
3. Projeto funcionando localmente

---

## 🌟 Opção 1: Vercel (Recomendado - Oficial do Next.js)

A Vercel é a plataforma oficial do Next.js e oferece deploy automático e gratuito.

### Passo a Passo:

1. **Acesse o site da Vercel:**
   - Vá para: https://vercel.com
   - Faça login com sua conta GitHub

2. **Importe o projeto:**
   - Clique em "Add New Project"
   - Selecione o repositório: `andresilveriodev/sitio-multitrem-ecommerce`
   - A Vercel detectará automaticamente que é um projeto Next.js

3. **Configurações do projeto:**
   - **Root Directory:** `frontend` (importante!)
   - **Framework Preset:** Next.js (já detectado)
   - **Build Command:** `npm run build` (padrão)
   - **Output Directory:** `.next` (padrão)
   - **Install Command:** `npm install` (padrão)

4. **Variáveis de Ambiente (se necessário):**
   - Por enquanto não precisamos, mas se adicionar APIs futuramente, configure aqui

5. **Deploy:**
   - Clique em "Deploy"
   - Aguarde o build (2-3 minutos)
   - Seu site estará online em: `https://sitio-multitrem-ecommerce.vercel.app`

6. **Domínio personalizado (opcional):**
   - Vá em Settings > Domains
   - Adicione seu domínio personalizado

### Vantagens:
- ✅ Deploy automático a cada push no GitHub
- ✅ Preview de cada PR
- ✅ CDN global (site rápido no mundo todo)
- ✅ SSL gratuito
- ✅ Gratuito para projetos pessoais

---

## 🌐 Opção 2: Netlify

### Passo a Passo:

1. **Acesse o site:**
   - Vá para: https://netlify.com
   - Faça login com GitHub

2. **Importe o projeto:**
   - Clique em "Add new site" > "Import an existing project"
   - Conecte com GitHub e selecione o repositório

3. **Configurações:**
   - **Base directory:** `frontend`
   - **Build command:** `npm run build`
   - **Publish directory:** `frontend/.next`

4. **Deploy:**
   - Clique em "Deploy site"
   - Aguarde o build

### Vantagens:
- ✅ Deploy automático
- ✅ Formulários gratuitos
- ✅ Funções serverless

---

## 🚂 Opção 3: Railway

### Passo a Passo:

1. **Acesse:** https://railway.app
2. **Crie novo projeto** e conecte com GitHub
3. **Adicione serviço** > "GitHub Repo"
4. **Configure:**
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Start Command: `npm start`

---

## 🐳 Opção 4: Docker + VPS (Avançado)

Para deploy em servidor próprio (DigitalOcean, AWS, etc.)

### Criar Dockerfile:

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine AS base

# Install dependencies only when needed
FROM base AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# Production image
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000

CMD ["node", "server.js"]
```

### Configurar next.config.ts:

```typescript
const nextConfig: NextConfig = {
  output: 'standalone', // Adicionar esta linha
  // ... resto da configuração
}
```

---

## 📝 Checklist Antes do Deploy

- [ ] Testar build local: `npm run build`
- [ ] Verificar se não há erros: `npm run lint`
- [ ] Testar em produção local: `npm start`
- [ ] Verificar variáveis de ambiente (se houver)
- [ ] Atualizar URLs de API (se houver)
- [ ] Verificar imagens e assets

---

## 🔧 Comandos Úteis

```bash
# Build de produção local
cd frontend
npm run build

# Testar build de produção
npm start

# Verificar tamanho do bundle
npm run build
# Verá o tamanho de cada página no terminal
```

---

## 🎯 Recomendação

**Para este projeto, recomendo Vercel** porque:
1. É a plataforma oficial do Next.js
2. Deploy automático a cada commit
3. Gratuito e fácil de usar
4. Performance excelente
5. Integração perfeita com GitHub

---

## 📚 Links Úteis

- [Documentação Vercel](https://vercel.com/docs)
- [Documentação Next.js Deploy](https://nextjs.org/docs/deployment)
- [Guia Netlify Next.js](https://docs.netlify.com/integrations/frameworks/next-js/)

---

## 🆘 Problemas Comuns

### Erro: "Cannot find module"
- Verifique se todas as dependências estão no `package.json`
- Execute `npm install` novamente

### Erro: "Build failed"
- Verifique os logs de build na plataforma
- Teste o build local primeiro: `npm run build`

### Imagens não aparecem
- Verifique se as URLs estão corretas
- Use `next/image` para otimização

---

**Boa sorte com o deploy! 🚀**

