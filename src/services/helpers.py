# src/helpers.py
import uuid
import os

def generate_file_key(session_id: str, original_filename: str) -> str:
    # Извлекаем расширение файла
    _, ext = os.path.splitext(original_filename)
    # Генерируем UUID
    unique_id = str(uuid.uuid4())
    # Формируем file key
    file_key = f"hr_task/sessions/{session_id}/{unique_id}{ext}"
    return file_key


def generate_clone_filekey(session_id: str, original_filename: str) -> str:
    # Извлекаем расширение файла
    _, ext = os.path.splitext(original_filename)
    # Генерируем UUID
    unique_id = str(uuid.uuid4())
    # Формируем file key
    file_key = f"clone/sessions/{session_id}/{unique_id}{ext}"
    return file_key
