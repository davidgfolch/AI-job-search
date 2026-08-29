# Development Dockerfile for React/Vite Web App
FROM node:24-slim

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy package files
COPY apps/web/package.json apps/web/package-lock.json* /app/

# Install dependencies
RUN npm ci

# Store lockfile hash so the entrypoint can detect stale node_modules in the
# persistent volume on later starts (see docker-entrypoint.sh).
RUN sha256sum package-lock.json | awk '{print $1}' > node_modules/.package-lock.sha256

# Copy application code
COPY apps/web /app/

# Entrypoint reinstalls node_modules when package-lock.json changes
COPY apps/web/docker-entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh

# Expose Vite dev server port
EXPOSE 5173

# Run Vite dev server with host binding for Docker
ENTRYPOINT ["/entrypoint.sh"]
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
