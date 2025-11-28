# @sitio/shared

Pacote compartilhado com tipos, DTOs e constantes para os microserviços do Sítio Multitrem.

## Estrutura

```
shared/
├── src/
│   ├── types/          # Tipos TypeScript compartilhados
│   ├── dto/            # Data Transfer Objects para validação
│   ├── constants/      # Constantes do sistema
│   └── index.ts        # Exportações principais
├── dist/               # Build compilado (gerado)
├── package.json
└── tsconfig.json
```

## Uso

### Instalação

```bash
npm install @sitio/shared
```

### Importação

```typescript
// Tipos
import { Product, Cart, Order, PaymentMethod } from '@sitio/shared'

// DTOs
import { CreateProductDto, AddToCartDto } from '@sitio/shared'

// Constantes
import { PRODUCT_CATEGORIES, ORDER_STATUS } from '@sitio/shared'
```

## Build

```bash
npm run build
```

## Watch Mode

```bash
npm run watch
```

