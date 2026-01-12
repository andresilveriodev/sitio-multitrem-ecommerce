# 🚀 Deploy no Netlify - Guia Rápido

## Variáveis de Ambiente Necessárias

Configure estas variáveis no painel do Netlify (Site settings > Environment variables):

```
NEXT_PUBLIC_API_URL=https://sua-api.com/api
NEXT_PUBLIC_APP_URL=https://seu-site.netlify.app
NEXT_PUBLIC_KEYCLOAK_CLIENT_ID=sitio-multitrem-app
```

## Comandos de Build

O Netlify executará automaticamente:
```bash
cd frontend
npm install
npm run build
```

## Estrutura

- **Base directory:** `frontend`
- **Build command:** `npm install && npm run build`
- **Publish directory:** `frontend/.next`

## Documentação Completa

Veja `NETLIFY_DEPLOY.md` para o guia completo.
