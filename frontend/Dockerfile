# Stage 1: Build optimized Vue 3 static bundle
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Stage 2: Serve static assets with unprivileged Nginx
FROM nginxinc/nginx-unprivileged:1.27-alpine

COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
