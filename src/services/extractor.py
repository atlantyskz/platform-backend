import io
import docx
import asyncio
import logging
import pdfplumber
from functools import partial
from abc import ABC, abstractmethod
from fastapi import Depends, UploadFile
from concurrent.futures import ThreadPoolExecutor

# Логирование
logger = logging.getLogger(__name__)

class ITextExtractor(ABC):
    """Протокол для интерфейса извлечения текста"""
    
    @abstractmethod
    async def extract_text(self, file: UploadFile) -> str:
        pass

class FileFormatError(Exception):
    """Ошибка при несоответствии формата файла"""
    pass

class TextExtractionError(Exception):
    """Ошибка извлечения текста"""
    pass

class AsyncTextExtractor:
    def __init__(self, thread_pool: ThreadPoolExecutor):
        self.thread_pool = thread_pool
        self.supported_formats = {
            'application/pdf': self._extract_from_pdf,
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': self._extract_from_docx,
            'text/plain': self._extract_from_txt,
        }

    async def extract_text(self, file: UploadFile) -> str:
        try:
            if file.content_type not in self.supported_formats:
                raise FileFormatError(f"Unsupported file format: {file.content_type}")
            content = await self._read_file(file)
            extractor = self.supported_formats[file.content_type]
            loop = asyncio.get_event_loop()
            text = await loop.run_in_executor(
                self.thread_pool,
                partial(extractor, content)
            )
            return text.strip()
        except FileFormatError:
            raise
        except Exception as e:
            logger.error(f"Failed to extract text from {file.filename}: {str(e)}")
            raise TextExtractionError(f"Failed to extract text from {file.filename}")

    async def _read_file(self, file: UploadFile) -> bytes:
        try:
            return await file.read()
        except Exception as e:
            logger.error(f"Failed to read file {file.filename}: {str(e)}")
            raise TextExtractionError(f"Failed to read file {file.filename}")

    def _extract_from_pdf(self, content: bytes) -> str:
        try:
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text()
                return text
        except Exception as e:
            logger.error(f"PDF extraction failed: {str(e)}")
            raise TextExtractionError("Failed to extract text from PDF")

    def _extract_from_docx(self, content: bytes) -> str:
        try:
            docx_file = io.BytesIO(content)
            doc = docx.Document(docx_file)
            return "\n".join([paragraph.text for paragraph in doc.paragraphs])
        except Exception as e:
            logger.error(f"DOCX extraction failed: {str(e)}")
            raise TextExtractionError("Failed to extract text from DOCX")

    def _extract_from_txt(self, content: bytes) -> str:
        try:
            return content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                return content.decode('cp1251')
            except Exception as e:
                logger.error(f"Text file decoding failed: {str(e)}")
                raise TextExtractionError("Failed to decode text file")

async def get_thread_pool() -> ThreadPoolExecutor:
    """Создать пул потоков для операций, которые могут быть сериализованы"""
    return ThreadPoolExecutor()

async def get_text_extractor(
    thread_pool: ThreadPoolExecutor = Depends(get_thread_pool)
) -> ITextExtractor:
    return AsyncTextExtractor(thread_pool)
