# ==========================================
# STAGE 1: Build the React static assets
# ==========================================
FROM node:20-alpine AS build

WORKDIR /app

# Install dependencies using package-lock.json caching
COPY package.json package-lock.json* ./
RUN npm ci

# Copy codebase and compile
COPY . .
RUN npm run build

# ==========================================
# STAGE 2: Spin up Nginx web server
# ==========================================
FROM nginx:alpine

# Copy compiled bundles from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
