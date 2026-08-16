FROM node:20-alpine AS deps
WORKDIR /app
COPY package*.json tsconfig*.json ./
RUN npm install

FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY package*.json tsconfig*.json ./
COPY src ./src
COPY contracts ./contracts
RUN npx tsc

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY package*.json ./
RUN npm install --only=production
COPY --from=builder /app/dist ./dist
USER node
EXPOSE 3001
CMD ["node", "dist/server.js"]
