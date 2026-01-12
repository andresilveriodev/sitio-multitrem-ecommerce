# 🔧 Correção de Submodules no Netlify

## ✅ O que foi feito:

1. **Removidas referências de submodules** do Git:
   - `services/ai-service/agno-agent/agent-ui`
   - `services/evolution-api`

2. **Criado arquivo `.gitmodules`** vazio

3. **Atualizado `netlify.toml`** com configuração para ignorar submodules

4. **Commit e push realizados**

## 🎯 Próximos Passos no Netlify:

### Opção 1: Configurar no Painel do Netlify (Recomendado)

1. Acesse o painel do seu site no Netlify
2. Vá em **Site settings** > **Build & deploy** > **Environment**
3. Adicione a variável de ambiente:
   - **Key:** `NETLIFY_SKIP_SUBMODULES`
   - **Value:** `true`

### Opção 2: Redeploy Automático

O Netlify deve fazer um novo deploy automaticamente após o push. Se não fizer:

1. Vá em **Deploys**
2. Clique em **Trigger deploy** > **Deploy site**

### Opção 3: Verificar Configuração de Build

No painel do Netlify, verifique se as configurações estão assim:

- **Base directory:** `frontend`
- **Build command:** `npm install && npm run build`
- **Publish directory:** `frontend/.next`

## 🔍 Se ainda der erro:

Se o erro persistir, você pode configurar no painel do Netlify para **não fazer checkout de submodules**:

1. Vá em **Site settings** > **Build & deploy** > **Build settings**
2. Procure por **"Submodules"** ou **"Git submodules"**
3. Desmarque a opção de fazer checkout de submodules

## ✅ Verificação:

Após o deploy, verifique:
- ✅ Build completa sem erros
- ✅ Site carrega corretamente
- ✅ Imagens aparecem
- ✅ Funcionalidades funcionam

---

**As mudanças já foram commitadas e enviadas para o GitHub!**

O próximo deploy no Netlify deve funcionar. Se ainda houver problemas, configure no painel conforme as instruções acima.
