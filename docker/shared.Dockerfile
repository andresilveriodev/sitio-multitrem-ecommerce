FROM node:22-alpine

WORKDIR /app/shared

COPY shared/package*.json ./
COPY shared/tsconfig.json ./

RUN npm ci --silent

COPY shared/src ./src

RUN npm run build

VOLUME ["/app/shared/dist"]