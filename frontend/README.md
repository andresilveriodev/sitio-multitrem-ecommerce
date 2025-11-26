# Sítio Multitrem - Frontend

E-commerce single-page para o Sítio Multitrem (Terezópolis de Goiás) que vende hortaliças frescas e ovos caipiras.

## 🚀 Como Rodar o Projeto

### Desenvolvimento

```bash
cd frontend
npm run dev
```

O servidor será iniciado em `http://localhost:3000`

### Build de Produção

```bash
cd frontend
npm run build
npm start
```

### Lint

```bash
cd frontend
npm run lint
```

## 📦 Dependências Instaladas

- **next**: Framework React
- **react** e **react-dom**: Biblioteca React
- **typescript**: Tipagem estática
- **tailwindcss**: Framework CSS
- **lucide-react**: Ícones
- **clsx** e **tailwind-merge**: Utilitários para classes CSS
- **react-hot-toast**: Notificações toast

## 📁 Estrutura de Pastas

```
src/
├── app/              # Rotas e layouts (App Router)
├── components/       # Componentes React
│   ├── ui/         # Componentes reutilizáveis
│   ├── layout/      # Header, Footer
│   └── sections/    # Seções da landing page
├── hooks/           # Custom hooks
├── contexts/        # Context API
├── lib/             # Utilitários
├── types/           # Tipos TypeScript
└── services/        # Chamadas API
```

## 🎨 Tema

- **Cores primárias**: Verde (#22c55e, #16a34a, #15803d)
- **Cores secundárias**: Marrom (#78350f, #92400e, #a16207)
- **Cores de destaque**: Laranja (#f97316)
- **Fontes**: Inter (corpo) e Poppins (títulos)
