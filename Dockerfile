# Використовуємо офіційний легкий образ Python 3.12
FROM python:3.12-slim

# Встановлюємо робочу директорію
WORKDIR /app

# Встановлюємо системні залежності для psycopg2
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копіюємо requirements.txt та встановлюємо залежності
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо весь код проекту в контейнер
COPY . .

# Відкриваємо порт 8000(Render 10000)
EXPOSE 10000

# Run uvicorn dynamically bound to 0.0.0.0 and the port provided by Render
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}"]