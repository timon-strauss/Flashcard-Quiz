# Stage 1: build frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci
COPY frontend/index.html frontend/vite.config.js ./
COPY frontend/src/ ./src/
RUN npm run build

# Stage 2: final image
FROM python:3.12-slim

# Install nginx
RUN apt-get update && apt-get install -y nginx && rm -rf /var/lib/apt/lists/*

# Install backend deps
WORKDIR /app/backend
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/app/ ./app/

# Install MCP server
WORKDIR /app/mcp-server
COPY mcp-server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY mcp-server/server.py .
WORKDIR /app/backend

# Copy built frontend
COPY --from=frontend-builder /app/dist /usr/share/nginx/html

# nginx config: proxy /api/ to localhost:8000
RUN printf 'server {\n\
    listen 80;\n\
    client_max_body_size 50M;\n\
    root /usr/share/nginx/html;\n\
    index index.html;\n\
    location / {\n\
        try_files $uri $uri/ /index.html;\n\
    }\n\
    location /api/ {\n\
        proxy_pass http://127.0.0.1:8000/;\n\
        proxy_set_header Host $host;\n\
        proxy_set_header X-Real-IP $remote_addr;\n\
    }\n\
    location /uploads/ {\n\
        proxy_pass http://127.0.0.1:8000/uploads/;\n\
        proxy_set_header Host $host;\n\
        proxy_set_header X-Real-IP $remote_addr;\n\
    }\n\
    location /mcp {\n\
        proxy_pass http://127.0.0.1:8001;\n\
        proxy_http_version 1.1;\n\
        proxy_set_header Connection \"\";\n\
        proxy_buffering off;\n\
        proxy_cache off;\n\
        proxy_read_timeout 1h;\n\
    }\n\
}\n' > /etc/nginx/sites-enabled/default

# Startup script: nginx + MCP server in background, backend in foreground
RUN printf '#!/bin/sh\nnginx\nBACKEND_URL=http://127.0.0.1:8000 MCP_HOST=127.0.0.1 MCP_PORT=8001 python /app/mcp-server/server.py &\nuvicorn app.main:app --host 127.0.0.1 --port 8000\n' > /start.sh && chmod +x /start.sh

ENV DATA_DIR=/app/data \
    UPLOAD_DIR=/app/uploads

VOLUME ["/app/data", "/app/uploads"]

EXPOSE 80

CMD ["/start.sh"]
