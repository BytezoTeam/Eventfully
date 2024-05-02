FROM python:3.11-alpine

WORKDIR /app

# Actions for running eventfully without root with gosu
RUN addgroup nonroot && \
    adduser --system -G nonroot --disabled-password nonroot && \
    apk add --no-cache gosu --repository https://dl-cdn.alpinelinux.org/alpine/edge/testing/

# Install and setup dependencies
COPY requirements.lock ./
RUN PYTHONDONTWRITEBYTECODE=1 pip install --no-cache-dir -r requirements.lock

# Copy project files
COPY tests/ tests/
COPY eventfully/ eventfully/
COPY tailwind.config.js docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh

# Build CSS Styles
RUN tailwindcss-extra -i ./eventfully/static/input.css -o ./eventfully/static/output.css

# The server runs on port 8000
EXPOSE 8000

ENTRYPOINT ./docker-entrypoint.sh
