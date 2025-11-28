# Product Service

Microserviço de produtos do Sítio Multitrem, responsável por gerenciar o catálogo de produtos.

## Tecnologias

- NestJS
- TypeORM
- PostgreSQL
- TypeScript

## Instalação

```bash
npm install
```

## Configuração

1. Copie o arquivo `.env.example` para `.env`:
```bash
cp .env.example .env
```

2. Configure as variáveis de ambiente no `.env`:
```env
DB_HOST=localhost
DB_PORT=5432
DB_USERNAME=postgres
DB_PASSWORD=postgres
DB_NAME=sitio_multitrem
PORT=3001
NODE_ENV=development
```

## Executar

### Desenvolvimento
```bash
npm run start:dev
```

### Produção
```bash
npm run build
npm start
```

## Endpoints

- `GET /products` - Listar todos os produtos
  - Query params: `?category=hortalica` (filtro por categoria)
  - Query params: `?active=true` (filtro por status ativo/inativo, padrão: true)
- `GET /products/:id` - Buscar produto por ID
- `GET /products/slug/:slug` - Buscar produto por slug
- `POST /products` - Criar produto
- `PUT /products/:id` - Atualizar produto
- `DELETE /products/:id` - Soft delete (desativa produto)

## Seed Automático

O seed de produtos é executado automaticamente ao iniciar o serviço se o banco estiver vazio. Inclui:

- **6 Hortaliças** (R$ 5,00 cada): Alface Americana, Alface Crespa, Coentro, Cebolinha, Salsa, Rúcula
- **3 Ovos Caipiras**: 12 ovos (R$ 15,00), 20 ovos (R$ 24,00), 30 ovos (R$ 35,00)
- **5 Kits**: Kit 1 Pessoa (3 hortaliças - R$ 12,00) até Kit 5 Pessoas (12 hortaliças - R$ 45,00)
- **1 Combo**: Combo Família 2 (5 hortaliças + 20 ovos - R$ 49,50)

## Porta

O serviço roda na porta **3001** por padrão.

