# 🚀 Guia de Deploy no Netlify - Sítio Multitrem

Este guia explica como fazer o deploy do frontend Next.js no Netlify.

## 📋 Pré-requisitos

1. Conta no GitHub com o repositório do projeto
2. Conta no Netlify (gratuita)
3. Node.js 20 instalado localmente (para testes)

---

## 🔧 Passo 1: Preparação Local

### 1.1 Testar o Build Localmente

```bash
cd frontend
npm install
npm run build
npm start
```

Se o build funcionar localmente, está pronto para o deploy!

### 1.2 Verificar Variáveis de Ambiente

Crie um arquivo `.env.local` no diretório `frontend/` com as variáveis necessárias:

```env
NEXT_PUBLIC_API_URL=https://sua-api.com/api
NEXT_PUBLIC_APP_URL=https://seu-site.netlify.app
NEXT_PUBLIC_KEYCLOAK_CLIENT_ID=sitio-multitrem-app
```

---

## 🌐 Passo 2: Deploy no Netlify

### 2.1 Conectar Repositório

1. Acesse [https://app.netlify.com](https://app.netlify.com)
2. Faça login com sua conta GitHub
3. Clique em **"Add new site"** > **"Import an existing project"**
4. Selecione **"Deploy with GitHub"**
5. Autorize o Netlify a acessar seus repositórios
6. Selecione o repositório: `seu-usuario/sitio-multitrem-ecommerce`

### 2.2 Configurações do Build

O Netlify detectará automaticamente o arquivo `netlify.toml` na raiz do projeto.

**Configurações automáticas:**
- **Base directory:** `frontend`
- **Build command:** `npm install && npm run build`
- **Publish directory:** `frontend/.next`

**Se precisar configurar manualmente:**
- **Base directory:** `frontend`
- **Build command:** `npm install && npm run build`
- **Publish directory:** `frontend/.next`

### 2.3 Variáveis de Ambiente

No painel do Netlify, vá em **Site settings** > **Environment variables** e adicione:

| Variável | Valor | Descrição |
|----------|-------|-----------|
| `NEXT_PUBLIC_API_URL` | `https://sua-api.com/api` | URL da API backend |
| `NEXT_PUBLIC_APP_URL` | `https://seu-site.netlify.app` | URL do site no Netlify |
| `NEXT_PUBLIC_KEYCLOAK_CLIENT_ID` | `sitio-multitrem-app` | Client ID do Keycloak |

**⚠️ IMPORTANTE:** 
- Use `https://` nas URLs de produção
- Não use `localhost` em produção
- As variáveis `NEXT_PUBLIC_*` são expostas no cliente

### 2.4 Deploy

1. Clique em **"Deploy site"**
2. Aguarde o build (2-5 minutos)
3. Seu site estará online em: `https://random-name-123.netlify.app`

---

## 🔄 Passo 3: Deploy Automático

O Netlify faz deploy automático a cada push na branch `main` (ou `master`).

### 3.1 Configurar Branch de Deploy

1. Vá em **Site settings** > **Build & deploy** > **Continuous Deployment**
2. Configure a branch principal (geralmente `main` ou `master`)
3. Ative **"Deploy only the production branch"** se desejar

### 3.2 Preview Deploys

- Cada Pull Request gera um preview deploy automaticamente
- Útil para testar mudanças antes de mergear

---

## 🌍 Passo 4: Domínio Personalizado (Opcional)

### 4.1 Adicionar Domínio

1. Vá em **Site settings** > **Domain management**
2. Clique em **"Add custom domain"**
3. Digite seu domínio: `sitio-multitrem.com`
4. Siga as instruções para configurar DNS

### 4.2 Configurar DNS

Adicione um registro CNAME no seu provedor de DNS:

```
Tipo: CNAME
Nome: www (ou @)
Valor: seu-site.netlify.app
```

Ou use um registro A (para domínio raiz):

```
Tipo: A
Nome: @
Valor: 75.2.60.5 (IP do Netlify)
```

### 4.3 SSL Automático

O Netlify fornece SSL gratuito automaticamente via Let's Encrypt.

---

## 🔍 Passo 5: Verificação Pós-Deploy

### 5.1 Checklist

- [ ] Site carrega corretamente
- [ ] Imagens aparecem (`/images/products/*`)
- [ ] Navegação funciona
- [ ] Carrinho funciona (localStorage)
- [ ] Chat widget aparece
- [ ] Links do WhatsApp funcionam
- [ ] Formulários funcionam (se houver)

### 5.2 Testar Funcionalidades

1. **Produtos:** Verifique se os cards aparecem
2. **Carrinho:** Adicione produtos e verifique
3. **Chat:** Clique no botão do WhatsApp
4. **Navegação:** Teste todos os links

---

## 🐛 Solução de Problemas

### Erro: "Build failed"

**Causa:** Erro no build do Next.js

**Solução:**
1. Verifique os logs de build no Netlify
2. Teste o build localmente: `npm run build`
3. Verifique se todas as dependências estão no `package.json`

### Erro: "Module not found"

**Causa:** Dependência faltando

**Solução:**
```bash
cd frontend
npm install
# Verifique se todas as dependências estão instaladas
```

### Imagens não aparecem

**Causa:** Caminho incorreto ou imagem não encontrada

**Solução:**
1. Verifique se as imagens estão em `frontend/public/images/products/`
2. Use caminhos relativos: `/images/products/nome.jpg`
3. Verifique o console do navegador para erros 404

### API não funciona

**Causa:** Variável de ambiente incorreta ou CORS

**Solução:**
1. Verifique `NEXT_PUBLIC_API_URL` no Netlify
2. Configure CORS no backend para aceitar o domínio do Netlify
3. Use HTTPS nas URLs de produção

### Erro de hidratação do React

**Causa:** Diferença entre servidor e cliente

**Solução:**
1. Verifique se não está usando `Math.random()` ou `Date.now()` no render
2. Use `useId()` do React para IDs únicos
3. Verifique o console do navegador para detalhes

---

## 📊 Monitoramento

### 5.1 Analytics (Opcional)

1. Vá em **Site settings** > **Analytics**
2. Ative **"Netlify Analytics"** (plano pago) ou use Google Analytics

### 5.2 Logs

- Acesse **Site overview** > **Deploys** para ver logs
- Clique em um deploy para ver logs detalhados

---

## 🔐 Segurança

### Headers de Segurança

O `netlify.toml` já inclui headers de segurança:
- X-Frame-Options
- X-XSS-Protection
- X-Content-Type-Options
- Referrer-Policy

### Variáveis de Ambiente

- **Nunca** commite arquivos `.env` no Git
- Use variáveis de ambiente do Netlify para dados sensíveis
- Variáveis `NEXT_PUBLIC_*` são expostas no cliente

---

## 📚 Recursos Úteis

- [Documentação Netlify](https://docs.netlify.com/)
- [Next.js no Netlify](https://docs.netlify.com/integrations/frameworks/next-js/)
- [Netlify Status](https://www.netlifystatus.com/)

---

## ✅ Checklist Final

Antes de fazer deploy:

- [ ] Build local funciona: `npm run build`
- [ ] Teste local funciona: `npm start`
- [ ] Variáveis de ambiente configuradas
- [ ] Imagens na pasta correta
- [ ] Sem erros no console
- [ ] Código commitado no GitHub

---

**Boa sorte com o deploy! 🚀**

Se tiver problemas, verifique os logs de build no Netlify ou abra uma issue no repositório.
