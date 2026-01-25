FROM node:22-alpine AS builder

WORKDIR /app

# Install curl for health checks
RUN apk add --no-cache curl

# Build shared package first and create a tarball
COPY shared/ ./shared/
WORKDIR /app/shared
RUN npm ci && npm run build && npm pack

# Move the generated tarball to a predictable location
RUN mv *.tgz /tmp/shared-package.tgz

# Setup service
WORKDIR /app/service
ARG SERVICE_PATH
ARG SERVICE_PORT=3001

# Copy service files
COPY ${SERVICE_PATH}/package*.json ./
COPY ${SERVICE_PATH}/tsconfig.json ./

# Remove the file: dependency from package.json and add tarball dependency
RUN sed -i 's|"@sitio/shared": "file:../../shared"|"@sitio/shared": "file:/tmp/shared-package.tgz"|g' package.json

# Remove package-lock.json since we modified package.json
RUN rm -f package-lock.json

# Install dependencies with npm install (ignore peer dependency conflicts)
RUN npm install --legacy-peer-deps

# Copy and build source code
COPY ${SERVICE_PATH}/src ./src
RUN npm run build

# Production stage
FROM node:22-alpine AS runner

WORKDIR /app

RUN addgroup --system --gid 1001 nestjs
RUN adduser --system --uid 1001 nestjs

# Install curl for health checks
RUN apk add --no-cache curl

# Copy built service
COPY --from=builder /app/service/dist ./dist
COPY --from=builder /app/service/node_modules ./node_modules
COPY --from=builder /app/service/package*.json ./

USER nestjs

ARG SERVICE_PORT=3001
EXPOSE ${SERVICE_PORT}

CMD ["node", "dist/main.js"]