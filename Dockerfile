FROM oven/bun:1.1-alpine AS build

WORKDIR /build

COPY package.json tailwind.config.js ./
COPY eventfully/ eventfully/

RUN bun install
RUN bun run build

FROM python:3.11-alpine AS run

# Install dependencies
WORKDIR /tmp

COPY requirements.lock ./
RUN sed '/-e/d' requirements.lock > requirements.txt && \
    pip install -r requirements.txt

# Add non root user
RUN addgroup eventfully && \
    adduser --system -G eventfully --disabled-password eventfully
USER eventfully

# Run eventfully
WORKDIR /home/eventfully
COPY --from=build /build/eventfully/ eventfully/

EXPOSE 8000

ENTRYPOINT ["gunicorn", "eventfully.main:app", "-w", "4", "-b", "0.0.0.0:8000"]
