# src/helpers.py
import uuid
import os

def generate_file_key(session_id: str, original_filename: str) -> str:
    """
    Генерирует уникальный file key для хранения файла в MinIO по структуре:
    hr_task/sessions/{session_id}/{unique_id}_{original_filename}

    :param session_id: Идентификатор сессии пользователя.
    :param original_filename: Оригинальное имя файла.
    :return: Уникальный file key.
    """
    # Извлекаем расширение файла
    _, ext = os.path.splitext(original_filename)
    # Генерируем UUID
    unique_id = str(uuid.uuid4())
    # Формируем file key
    file_key = f"hr_task/sessions/{session_id}/{unique_id}{ext}"
    return file_key
