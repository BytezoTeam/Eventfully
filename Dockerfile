FROM python:3.11-alpine

WORKDIR /app

# Install dependencies
COPY requirements.lock ./
RUN PYTHONDONTWRITEBYTECODE=1 pip install --no-cache-dir -r requirements.lock

COPY tests/ tests/
COPY eventfully/ eventfully/
COPY tailwind.config.js ./

# Build CSS Styles
RUN tailwindcss-extra -i ./eventfully/static/input.css -o ./eventfully/static/output.css

EXPOSE 8000

ENTRYPOINT ["gunicorn", "eventfully.main:app", "-w", "4", "-b", "0.0.0.0:8000"]
