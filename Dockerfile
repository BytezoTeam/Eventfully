FROM python:3.11-alpine AS build

WORKDIR /app

COPY eventfully/ eventfully/
COPY tailwind.config.js ./

# Build CSS Styles
RUN pip install --no-cache-dir pytailwindcss-extra==0.2.* && \
    tailwindcss-extra && \
    tailwindcss-extra -i ./eventfully/static/input.css -o ./eventfully/static/output.css --minify


FROM python:3.11-alpine AS run

WORKDIR /app

# Add Tini
RUN apk add --no-cache tini && \
    # Running eventfully without root with gosu
    addgroup nonroot && \
    adduser --system -G nonroot --disabled-password nonroot && \
    apk add --no-cache gosu --repository https://dl-cdn.alpinelinux.org/alpine/edge/testing/

# Install and setup dependencies
COPY requirements.lock ./
RUN PYTHONDONTWRITEBYTECODE=1 pip install --no-cache-dir -r requirements.lock

# Copy project files
COPY --from=build /app/eventfully/ eventfully/
COPY tests/ tests/
COPY locales/ locales/
COPY tailwind.config.js docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh

# The server runs on port 8000
EXPOSE 8000

VOLUME [ "/app/database/sqlite" ]

# Run your program under Tini
ENTRYPOINT ["/sbin/tini", "--"]
CMD ["./docker-entrypoint.sh"]

HEALTHCHECK CMD wget --spider -q http://127.0.0.1:8000 || exit 1
