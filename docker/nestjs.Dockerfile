FROM node:22-alpine AS builder

WORKDIR /app

# Install curl for health checks
RUN apk add --no-cache curl

# Copy and build shared package
COPY shared/ ./shared/
WORKDIR /app/shared
RUN npm ci && npm run build

# Copy service files
WORKDIR /app/service
ARG SERVICE_PATH
ARG SERVICE_PORT=3001
COPY ${SERVICE_PATH}/package*.json ./
COPY ${SERVICE_PATH}/tsconfig.json ./

# Install dependencies
RUN npm ci --silent

# Copy source code
COPY ${SERVICE_PATH}/src ./src

# Build the service
RUN npm run build

# Production stage
FROM node:22-alpine AS runner

WORKDIR /app

RUN addgroup --system --gid 1001 nestjs
RUN adduser --system --uid 1001 nestjs

# Install curl for health checks
RUN apk add --no-cache curl

COPY --from=builder /app/service/dist ./dist
COPY --from=builder /app/service/node_modules ./node_modules
COPY --from=builder /app/service/package*.json ./

USER nestjs

ARG SERVICE_PORT=3001
EXPOSE ${SERVICE_PORT}

CMD ["node", "dist/main.js"]