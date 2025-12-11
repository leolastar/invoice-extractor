FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for Pillow, PostgreSQL client, and Redis client
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    libtiff-dev \
    libfreetype6-dev \
    postgresql-client \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p uploads
RUN chmod +x wait-for-db.sh wait-for-redis.sh || true

EXPOSE 5000

CMD ["python", "app.py"]

