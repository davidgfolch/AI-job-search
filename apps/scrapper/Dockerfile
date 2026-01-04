# Development Dockerfile for Scrapper with Selenium/Chrome
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including Chrome and ChromeDriver
RUN apt-get update && apt-get install -y \
    gcc \
    wget \
    gnupg \
    unzip \
    curl \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome
RUN wget -q -O /tmp/google-chrome-key.pub https://dl-ssl.google.com/linux/linux_signing_key.pub \
    && gpg --dearmor -o /usr/share/keyrings/google-chrome-keyring.gpg /tmp/google-chrome-key.pub \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/* /tmp/google-chrome-key.pub

# Install Poetry
RUN pip install --no-cache-dir poetry==1.8.0

# Copy commonlib first and install it
COPY apps/commonlib /app/apps/commonlib
WORKDIR /app/apps/commonlib
RUN pip install -e .

# Copy dependency files
COPY apps/scrapper/pyproject.toml apps/scrapper/poetry.lock* /app/apps/scrapper/

# Install dependencies
WORKDIR /app/apps/scrapper
RUN poetry config virtualenvs.create false \
    && poetry lock --no-update \
    && poetry install --no-interaction --no-ansi --only main

# Copy application code
COPY apps/scrapper /app/apps/scrapper

# Copy environment file
COPY .env* /app/

# Note: Scrapper typically runs as a scheduled/manual job, not a long-running service
# For dev mode, you can run specific scrapers manually
CMD ["poetry", "run", "python", "-m", "scrapper.main"]
