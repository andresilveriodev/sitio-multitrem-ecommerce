# 📋 PLANEJAMENTO DE REFATORAÇÃO VISUAL - FRONTEND
## Sítio Multitrem E-commerce

**Baseado em:** [Orgânico do Chico](https://www.organicodochico.com.br/)  
**Data:** Janeiro 2026  
**Objetivo:** Reformular completamente o design, UX/UI e identidade visual

---

## ⚠️ IMPORTANTE - ESCOPO DA REFATORAÇÃO

> **Esta refatoração é exclusivamente VISUAL e de LAYOUT.**
> 
> - ✅ **Será alterado:** Design, cores, tipografia, espaçamentos, componentes visuais, animações, layout e organização visual
> - ❌ **NÃO será alterado:** Conteúdo textual, informações dos produtos, funcionalidades, lógica de negócio, integrações
> 
> **Todas as informações, textos, descrições e conteúdos permanecerão inalterados.**  
> **Apenas a apresentação visual (aparência) será reformulada.**

---

## 📌 O QUE MUDA E O QUE NÃO MUDA

### ✅ O QUE SERÁ REFATORADO (Visual/Layout):
- Design system (cores, tipografia, espaçamentos)
- Componentes UI (botões, cards, inputs, modais)
- Layout de páginas (estrutura, grid, organização)
- Header e Footer (aparência visual)
- Responsividade e breakpoints
- Animações e transições
- Estilos CSS/Tailwind
- Hierarquia visual de informações

### ❌ O QUE PERMANECE INALTERADO (Conteúdo/Funcionalidades):
- Textos e descrições dos produtos
- Nomes de produtos e categorias
- Preços e informações de valor
- Funcionalidades (adicionar ao carrinho, checkout, etc)
- Integrações (payment, API, backend)
- Lógica de negócio
- Dados e informações do banco
- Fluxos de navegação existentes
- Contextos e estados (CartContext, ChatContext, etc)

### 🎨 Resumo:
**Mesma casa, nova pintura e móveis!**  
A estrutura funcional permanece, apenas a "cara" do site muda para ficar mais bonita e alinhada com a identidade visual do Orgânico do Chico.

---

## 🎨 ANÁLISE DE REFERÊNCIA (Orgânico do Chico)

### Identidade Visual Identificada

#### Paleta de Cores
```css
/* Cores Principais */
--primary-green: #4CAF50        /* Verde orgânico/fresco */
--primary-dark: #2E7D32         /* Verde escuro */
--accent-orange: #FF9800        /* Laranja ofertas */
--accent-red: #F44336           /* Vermelho promoções */

/* Cores Neutras */
--white: #FFFFFF
--gray-50: #FAFAFA
--gray-100: #F5F5F5
--gray-200: #EEEEEE
--gray-600: #757575
--gray-900: #212121

/* Cores de Status */
--success: #66BB6A
--warning: #FFA726
--error: #EF5350
--info: #42A5F5
```

#### Tipografia
```css
/* Fontes Base */
font-family-primary: 'Inter', 'Roboto', -apple-system, sans-serif
font-family-heading: 'Inter', sans-serif

/* Tamanhos */
--text-xs: 0.75rem      /* 12px - Labels pequenos */
--text-sm: 0.875rem     /* 14px - Descrições */
--text-base: 1rem       /* 16px - Corpo */
--text-lg: 1.125rem     /* 18px - Subtítulos */
--text-xl: 1.25rem      /* 20px - Títulos pequenos */
--text-2xl: 1.5rem      /* 24px - Títulos médios */
--text-3xl: 1.875rem    /* 30px - Títulos grandes */
--text-4xl: 2.25rem     /* 36px - Hero titles */

/* Pesos */
--font-normal: 400
--font-medium: 500
--font-semibold: 600
--font-bold: 700
```

#### Espaçamentos
```css
/* Sistema de Grid */
--spacing-1: 0.25rem    /* 4px */
--spacing-2: 0.5rem     /* 8px */
--spacing-3: 0.75rem    /* 12px */
--spacing-4: 1rem       /* 16px */
--spacing-5: 1.25rem    /* 20px */
--spacing-6: 1.5rem     /* 24px */
--spacing-8: 2rem       /* 32px */
--spacing-10: 2.5rem    /* 40px */
--spacing-12: 3rem      /* 48px */
--spacing-16: 4rem      /* 64px */
--spacing-20: 5rem      /* 80px */

/* Container */
--container-max-width: 1200px
--container-padding: 1rem (mobile) | 2rem (desktop)
```

#### Border Radius
```css
--radius-sm: 4px        /* Badges, tags */
--radius-md: 8px        /* Cards, buttons */
--radius-lg: 12px       /* Modais, drawers */
--radius-xl: 16px       /* Hero sections */
--radius-full: 9999px   /* Pills, avatars */
```

#### Sombras
```css
--shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05)
--shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1)
--shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1)
--shadow-xl: 0 20px 25px rgba(0, 0, 0, 0.15)
```

---

## 🏗️ ESTRUTURA DE REFATORAÇÃO

### FASE 1: Design System & Tokens
**Duração:** 2-3 dias

#### 1.1 Criar Design Tokens
```
frontend/src/styles/
├── tokens/
│   ├── colors.css          # Paleta completa
│   ├── typography.css      # Fontes e tamanhos
│   ├── spacing.css         # Espaçamentos
│   ├── shadows.css         # Sombras
│   └── animations.css      # Transições
└── themes/
    ├── light.css          # Tema claro (padrão)
    └── dark.css           # Tema escuro (futuro)
```

#### 1.2 Atualizar globals.css
```css
/* Importar tokens */
@import './tokens/colors.css';
@import './tokens/typography.css';
@import './tokens/spacing.css';
@import './tokens/shadows.css';
@import './tokens/animations.css';

/* Reset customizado */
/* Estilos base */
/* Utilities */
```

---

### FASE 2: Componentes Base (UI Library)
**Duração:** 3-4 dias

#### 2.1 Atualizar Componentes Existentes

**Button.tsx**
```tsx
// Variantes a implementar:
- primary (verde)
- secondary (branco com borda)
- outline (apenas borda)
- ghost (transparente)
- danger (vermelho)
- success (verde claro)

// Tamanhos:
- xs (pequeno - 28px)
- sm (pequeno - 32px)
- md (médio - 40px - padrão)
- lg (grande - 48px)
- xl (extra grande - 56px)

// Estados:
- default
- hover
- active
- disabled
- loading
```

**Card.tsx**
```tsx
// Variantes:
- elevated (com sombra)
- outlined (com borda)
- filled (com background)
- interactive (hover effect)

// Especializações:
<ProductCard />      // Card de produto
<CategoryCard />     // Card de categoria
<BlogCard />         // Card de blog post
<OfferCard />        // Card de oferta especial
```

**Badge.tsx**
```tsx
// Variantes:
- success (verde)
- warning (laranja)
- error (vermelho)
- info (azul)
- neutral (cinza)
- organic (verde claro - "Orgânico")
- discount (vermelho - "30% OFF")
- new (amarelo - "Novo")
```

#### 2.2 Criar Novos Componentes Base

**Carousel.tsx**
```tsx
// Banner carousel (hero)
- Autoplay
- Dots navigation
- Arrow navigation
- Touch/swipe support
- Lazy loading de imagens
```

**Chip.tsx**
```tsx
// Filtros e tags
- Clickable/selectable
- Removable (com X)
- Icon support
```

**Skeleton.tsx** (melhorar)
```tsx
// Loading states
- Card skeleton
- Text skeleton
- Image skeleton
- List skeleton
```

**Tabs.tsx**
```tsx
// Navegação por categorias
- Horizontal scroll
- Active indicator
- Icon + text
```

**Breadcrumb.tsx**
```tsx
// Navegação hierárquica
- Home > Categoria > Produto
```

---

### FASE 3: Layout Principal
**Duração:** 2-3 dias

#### 3.1 Header (Refatoração Completa)

**Desktop Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│  [Logo]          [Busca]          [Login] [Cart] [Chat]     │
│  Horta do Chico  Ovos e Carnes   Mercearia   Bebidas   etc  │
└─────────────────────────────────────────────────────────────┘
```

**Características:**
- Sticky header (fixo no scroll)
- Busca com autocomplete
- Menu de categorias com hover
- Badge de contador no carrinho
- Indicador de chat não lido

**Mobile Layout:**
```
┌────────────────────────────┐
│ [☰]  [Logo]  [🔍] [Cart]   │
└────────────────────────────┘
```

**Drawer Menu Mobile:**
- Slide-in da esquerda
- Categorias expansíveis
- Login/perfil
- Links úteis

#### 3.2 Footer (Refatoração Completa)

**Layout 4 Colunas (Desktop):**
```
┌──────────────────────────────────────────────────────────────┐
│  Institucional  |  SAC  |  Termos  |  Redes Sociais         │
│  - Início       | Tel   | Termos   | [F] [I] [W]            │
│  - Sobre Nós    | Email | Política |                         │
│  - Blog         |       | Entrega  | Métodos de Pagamento    │
│  - Contato      |       |          | [💳 💳 💳 💳 💳]        │
│                 |       |          |                         │
│  Desenvolvido por Instabuy  |  © 2026 Sítio Multitrem       │
└──────────────────────────────────────────────────────────────┘
```

**Mobile:**
- Accordion/collapse sections
- Stack vertical

---

### FASE 4: Página Principal (Home)
**Duração:** 4-5 dias

#### 4.1 Hero Section (Banner Carrossel)

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│                                                          │
│    [← Imagem de Banner com Texto Overlay →]            │
│                                                          │
│    ○ ○ ● ○ ○  (Indicadores)                           │
└─────────────────────────────────────────────────────────┘
```

**Características:**
- 3-5 slides
- Autoplay (5s)
- Pause on hover
- CTA buttons nos banners
- Responsivo (imagens diferentes mobile/desktop)

**Exemplos de Banners:**
1. "Arroz Agulhinha Integral, Biodinâmico e Orgânico 1kg - Volkmann"
2. "Hortaliças Frescas Colhidas no Dia"
3. "Ovos Caipiras do Sítio"

#### 4.2 Categorias Rápidas

**Layout Desktop:**
```
┌─────────────────────────────────────────────────────────┐
│  Categorias                                       ver tudo→│
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐     │
│  │ 🌱   │  │ 🥕   │  │ 🍎   │  │ 🥚   │  │ 🛍️  │     │
│  │Horta │  │Legum.│  │Frutas│  │ Ovos │  │Cestas│     │
│  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘     │
└─────────────────────────────────────────────────────────┘
```

**Características:**
- Scroll horizontal (mobile)
- Ícones coloridos
- Hover effect
- Link para página da categoria

#### 4.3 Ofertas / Destaques

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│  Ofertas                                          ver tudo→│
│  ┌───────┐  ┌───────┐  ┌───────┐  ┌───────┐            │
│  │[IMG]  │  │[IMG]  │  │[IMG]  │  │[IMG]  │            │
│  │Produto│  │Produto│  │Produto│  │Produto│            │
│  │R$29,99│  │R$42,99│  │R$19,99│  │R$34,99│            │
│  │[-30%] │  │[-20%] │  │[-15%] │  │[-25%] │            │
│  │  [+]  │  │  [+]  │  │  [+]  │  │  [+]  │            │
│  └───────┘  └───────┘  └───────┘  └───────┘            │
└─────────────────────────────────────────────────────────┘
```

**Product Card Anatomy:**
```
┌──────────────────┐
│   [Badge Oferta] │ <- "Oferta" em vermelho/laranja
│                  │
│   [Imagem]       │ <- 1:1 ratio, lazy load
│                  │
│ Nome do Produto  │ <- 2 linhas max, ellipsis
│ (Descrição)      │ <- Peso/unidade
│                  │
│ ~~R$ 42,99~~     │ <- Preço original riscado
│ R$ 29,99         │ <- Preço com desconto (destaque)
│ -30%             │ <- Badge de desconto
│                  │
│   [Adicionar]    │ <- Botão primário verde
└──────────────────┘
```

#### 4.4 Mais Vendidos

- Layout idêntico às ofertas
- Sem badge de desconto
- Ordenado por vendas

#### 4.5 Categorias de Produtos

**Seções:**
1. **Horta do Chico** (verduras, legumes)
2. **Ovos, Peixes e Carnes**
3. **Mercearia** (arroz, feijão, grãos)
4. **Bebidas e Laticínios**
5. **Cestas Prontas**

**Layout de cada seção:**
- Título + "ver tudo"
- Grid de produtos (4 colunas desktop, 2 mobile)
- Scroll horizontal como alternativa

#### 4.6 Nosso Blog

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│  Nosso Blog                                     ver post→│
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │[IMG]         │  │[IMG]         │  │[IMG]         │  │
│  │Título        │  │Título        │  │Título        │  │
│  │Resumo...     │  │Resumo...     │  │Resumo...     │  │
│  │ver post →    │  │ver post →    │  │ver post →    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

**Posts Sugeridos (baseado no site):**
- "De onde vem seus orgânicos?"
- "Como conservar hortaliças"
- "Por que os ovos caipira têm cores diferentes?"

#### 4.7 Diferenciais (Badges)

**Layout:**
```
┌──────────────────────────────────────────────────────┐
│  [⚡ Agilidade]  [🚚 Entrega Grátis]  [💳 Segurança] │
│  Pediu meio-dia   Compras + R$ 200    Pagamento      │
│  recebe hoje                           online seguro  │
└──────────────────────────────────────────────────────┘
```

---

### FASE 5: Página de Produto
**Duração:** 2-3 dias

#### 5.1 Layout Desktop

```
┌──────────────────────────────────────────────────────────┐
│ Home > Categoria > Produto                                │
│                                                            │
│ ┌──────────────┐  ┌────────────────────────────────────┐ │
│ │              │  │  Nome do Produto                    │ │
│ │   [Imagem]   │  │  R$ 29,99                          │ │
│ │              │  │  ~~R$ 42,99~~ -30%                 │ │
│ │              │  │                                     │ │
│ │ [Thumb]      │  │  Descrição do produto lorem ipsum  │ │
│ │ [Thumb]      │  │  dolor sit amet...                 │ │
│ │ [Thumb]      │  │                                     │ │
│ │              │  │  Informações Nutricionais:         │ │
│ │              │  │  - Orgânico certificado            │ │
│ │              │  │  - Peso: 500g                      │ │
│ │              │  │                                     │ │
│ │              │  │  [- 1 +]  [Adicionar ao Carrinho] │ │
│ └──────────────┘  └────────────────────────────────────┘ │
│                                                            │
│ Produtos Relacionados                              ver tudo│
│ [Card] [Card] [Card] [Card]                               │
└──────────────────────────────────────────────────────────┘
```

---

### FASE 6: Carrinho & Checkout
**Duração:** 2-3 dias

#### 6.1 Cart Drawer (Lateral Direita)

**Layout:**
```
┌────────────────────────────┐
│ Seu Carrinho        [X]    │
│────────────────────────────│
│ ┌──────────────────────┐   │
│ │[IMG] Produto         │   │
│ │R$ 29,99              │   │
│ │[- 2 +]        [🗑️]   │   │
│ └──────────────────────┘   │
│                            │
│ ┌──────────────────────┐   │
│ │[IMG] Produto         │   │
│ │R$ 19,99              │   │
│ │[- 1 +]        [🗑️]   │   │
│ └──────────────────────┘   │
│                            │
│────────────────────────────│
│ Subtotal      R$ 79,97     │
│ Entrega       R$ 0,00      │
│ Total         R$ 79,97     │
│                            │
│ [Finalizar Compra]         │
│ [Continuar Comprando]      │
└────────────────────────────┘
```

#### 6.2 Página de Checkout

**Stepper:**
```
1. Dados ● ────── 2. Entrega ○ ────── 3. Pagamento ○ ────── 4. Confirmação ○
```

**Layout de cada step:**
- Formulário no centro
- Resumo do pedido à direita (sticky)
- Breadcrumb no topo

---

### FASE 7: Responsividade
**Duração:** 2 dias

#### Breakpoints
```css
/* Mobile First */
--mobile: 0px        /* Default */
--sm: 640px          /* Small tablets */
--md: 768px          /* Tablets */
--lg: 1024px         /* Laptops */
--xl: 1280px         /* Desktops */
--2xl: 1536px        /* Large screens */
```

#### Ajustes por Dispositivo

**Mobile (< 768px):**
- Hamburger menu
- Cards 1-2 colunas
- Botões full-width
- Font-sizes reduzidos
- Espaçamentos menores

**Tablet (768px - 1024px):**
- Cards 2-3 colunas
- Menu adaptativo

**Desktop (> 1024px):**
- Cards 4-5 colunas
- Hover effects
- Mega menu

---

### FASE 8: Animações & Transições
**Duração:** 1-2 dias

#### Transições Padrão
```css
--transition-fast: 150ms ease-in-out
--transition-base: 200ms ease-in-out
--transition-slow: 300ms ease-in-out
```

#### Animações a Implementar

**Entrada de Elementos:**
```css
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from { 
    opacity: 0; 
    transform: translateY(20px);
  }
  to { 
    opacity: 1; 
    transform: translateY(0);
  }
}
```

**Hover Effects:**
- Card lift (translateY + shadow)
- Button scale
- Image zoom

**Loading States:**
- Skeleton shimmer
- Spinner
- Progress bar

---

### FASE 9: Acessibilidade (A11Y)
**Duração:** 1-2 dias

#### Checklist

- [ ] Contraste de cores (WCAG AA)
- [ ] Navegação por teclado
- [ ] Focus visible
- [ ] ARIA labels
- [ ] Alt text em imagens
- [ ] Landmarks (header, main, footer, nav)
- [ ] Screen reader friendly
- [ ] Form validation messages

---

### FASE 10: Performance
**Duração:** 1-2 dias

#### Otimizações

**Imagens:**
- Next.js Image component
- WebP format
- Lazy loading
- Blur placeholder
- Responsive images

**Código:**
- Code splitting
- Tree shaking
- Dynamic imports
- Bundle analysis

**Cache:**
- Static generation
- ISR (Incremental Static Regeneration)
- CDN

---

## 📝 PRIORIZAÇÃO

### Alta Prioridade (Semana 1)
1. ✅ Design System & Tokens
2. ✅ Componentes Base
3. ✅ Header & Footer
4. ✅ Home Page (Hero + Ofertas)

### Média Prioridade (Semana 2)
5. ✅ Product Cards
6. ✅ Product Page
7. ✅ Cart & Checkout
8. ✅ Responsividade

### Baixa Prioridade (Semana 3)
9. ✅ Animações
10. ✅ Acessibilidade
11. ✅ Performance
12. ✅ Testes

---

## 🎯 MÉTRICAS DE SUCESSO

- **Performance:** Lighthouse Score > 90
- **Acessibilidade:** WCAG AA compliant
- **SEO:** Score > 95
- **Conversão:** Taxa de abandono de carrinho < 30%
- **Mobile:** Tempo de carregamento < 3s

---

## 📦 ENTREGÁVEIS

### Documentação
- [ ] Style Guide completo
- [ ] Component Library (Storybook)
- [ ] Design Tokens documentados
- [ ] Guia de uso dos componentes

### Código
- [ ] Todos componentes refatorados
- [ ] Testes unitários > 80%
- [ ] Testes E2E principais fluxos
- [ ] Performance otimizada

### Design
- [ ] Mockups Figma (todas páginas)
- [ ] Protótipos interativos
- [ ] Assets exportados (ícones, logos)

---

## 🚀 PRÓXIMOS PASSOS

1. ✅ Aprovação do Planejamento
2. **Criação de Mockups no Figma** (opcional)
3. **Início da Implementação - FASE 1**
4. **Reviews a cada fase completada**
5. **Deploy em ambiente de staging**
6. **Testes com usuários**
7. **Deploy em produção**

---

## 📚 REFERÊNCIAS

- Site de referência: https://www.organicodochico.com.br/
- Material Design: https://material.io/
- TailwindCSS: https://tailwindcss.com/
- Next.js: https://nextjs.org/
- WCAG Guidelines: https://www.w3.org/WAI/WCAG21/quickref/

---

## 🔐 GARANTIAS

### Durante toda a refatoração:

✅ **Garantimos que:**
- Nenhum texto ou conteúdo será alterado
- Todas as funcionalidades continuarão funcionando
- Dados e informações permanecerão intactos
- Integrações com backend não serão afetadas
- Experiência do usuário será melhorada (não degradada)

### Metodologia:
- Cada componente será refatorado mantendo suas props e interfaces
- Testes serão executados após cada fase
- Versionamento com git para fácil rollback se necessário
- Deploy gradual (staging → produção)

---

**Status:** Planejamento aprovado e pronto para implementação  
**Última atualização:** Janeiro 2026  
**Tipo de refatoração:** Visual/Layout apenas (conteúdo inalterado)

