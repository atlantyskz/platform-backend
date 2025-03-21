# Используем slim-образ Python для минимального размера
FROM python:3.10-slim AS builder

# Устанавливаем переменные окружения для Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем requirements.txt для установки зависимостей
COPY requirements.txt requirements.txt

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все файлы проекта в контейнер
COPY . .

# Создаем папку static внутри контейнера (опционально, но рекомендуется для порядка)
RUN mkdir -p /app/static
# Копируем собранные статические файлы в контейнер
COPY collected_static /app/static 
# Открываем порт, на котором будет работать приложение
EXPOSE 9000

# Задаем команду по умолчанию для выполнения (например, Alembic миграции и запуск приложения)
#CMD ["sh", "-c", "python -m alembic upgrade head && python -u main.py"]
CMD ["python", "telegram_bot.py"]