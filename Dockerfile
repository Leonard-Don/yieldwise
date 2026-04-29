# Yieldwise app image — FastAPI + uvicorn + bundled frontend.
# The image is self-contained: code, frontend assets, and Python deps.
# Runtime config (DSN, session secret, admin seed, AMAP key) comes via env.

FROM python:3.13-slim

# Build deps for psycopg + bcrypt; runtime stays minimal.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (cached layer; deps change less than source).
COPY api/requirements.txt /app/api/requirements.txt
RUN pip install --no-cache-dir -r api/requirements.txt

# Copy the rest of the project. tmp/ is gitignored so it won't bloat the image.
COPY . /app

# Default port; override with -p host:8000 if you need a different host port.
EXPOSE 8000

# Healthcheck the public endpoint that doesn't require auth.
HEALTHCHECK --interval=10s --timeout=5s --start-period=20s --retries=5 \
    CMD curl -fsS http://localhost:8000/api/health >/dev/null || exit 1

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
