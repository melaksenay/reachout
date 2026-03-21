# ---- Build stage: compile TypeScript + bundle with Vite ----
FROM node:20-alpine AS builder

WORKDIR /app

# Supabase vars are inlined by Vite at build time
ARG VITE_SUPABASE_URL
ARG VITE_SUPABASE_PUBLISHABLE_KEY

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

# ---- Production stage: serve static files with nginx ----
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
