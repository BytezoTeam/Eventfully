FROM python:3.11-alpine AS run

WORKDIR /app

COPY requirements.lock ./
RUN sed '/-e/d' requirements.lock > requirements.txt && \
    pip install -r requirements.txt
COPY eventfully/ eventfully/

EXPOSE 8000

ENTRYPOINT ["gunicorn", "eventfully.main:app", "-w", "4", "-b", "0.0.0.0:8000"]
