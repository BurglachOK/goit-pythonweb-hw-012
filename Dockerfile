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

# Відкриваємо порт 8000
EXPOSE 8000

# Команда для запуску (використовуємо 0.0.0.0, щоб порт був доступний ззовні контейнера)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]