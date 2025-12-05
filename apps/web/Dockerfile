# Development Dockerfile for React/Vite Web App
FROM node:20-slim

WORKDIR /app

# Copy package files
COPY apps/web/package.json apps/web/package-lock.json* /app/

# Install dependencies
RUN npm ci

# Copy application code
COPY apps/web /app/

# Expose Vite dev server port
EXPOSE 5173

# Run Vite dev server with host binding for Docker
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
