# ─── Build stage ──────────────────────────────────────────────────────────────
FROM python:3.13-slim AS builder

WORKDIR /app

# Install system deps needed for psycopg2, Pillow, and Node.js (for Tailwind CSS build)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libjpeg-dev \
    libwebp-dev \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ─── CSS build stage ──────────────────────────────────────────────────────────
FROM node:20-slim AS css-builder

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci --include=dev

COPY tailwind.config.js postcss.config.js ./
COPY yoga_app/templates ./yoga_app/templates
COPY yoga_app/static/css/input.css ./yoga_app/static/css/input.css

RUN npm run build

# ─── Runtime stage ────────────────────────────────────────────────────────────
FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Runtime system deps only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libjpeg62-turbo \
    libwebp7 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy project
COPY . .

# Copy compiled CSS from css-builder stage
COPY --from=css-builder /app/yoga_app/static/css/output.css ./yoga_app/static/css/output.css

# Collect static files at build time
RUN python manage.py collectstatic --noinput

# Non-root user for security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
RUN chown -R appuser:appgroup /app
USER appuser

EXPOSE $PORT

CMD ["gunicorn", "yoga_kailasa.wsgi:application", "--config", "gunicorn.conf.py"]
