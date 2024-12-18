# Stage 1: Builder
FROM python:3.10-slim AS builder

# Установка переменных окружения
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем зависимости с кешированием
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код приложения
COPY . .

# Stage 2: Final image
FROM python:3.10-slim

# Установка переменных окружения
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем только необходимые файлы из builder
COPY --from=builder /usr/local/lib/python3.10/site-packages/ /usr/local/lib/python3.10/site-packages/
COPY --from=builder /app /app

# Убедимся, что start.sh существует и имеет права на выполнение
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Создаем non-root пользователя для безопасности
RUN adduser --disabled-password --no-create-home appuser && \
    chown -R appuser:appuser /app

# Переходим на non-root пользователя
USER appuser

# Открываем порт приложения
EXPOSE 9000

# Проверка здоровья контейнера
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:9000/health || exit 1

