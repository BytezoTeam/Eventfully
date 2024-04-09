FROM oven/bun:1.1-alpine AS build

WORKDIR /build

COPY package.json tailwind.config.js ./
COPY eventfully/ eventfully/

RUN bun install
RUN bun run build

FROM python:3.11-alpine AS run

# Install dependencies
WORKDIR /app

COPY requirements.lock ./
RUN sed '/-e/d' requirements.lock > requirements.txt && \
    pip install -r requirements.txt

# Run eventfully
COPY --from=build /build/eventfully/ eventfully/
COPY tests/ tests/

EXPOSE 8000

ENTRYPOINT ["gunicorn", "eventfully.main:app", "-w", "4", "-b", "0.0.0.0:8000"]
