from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
import uuid

from pydantic import BaseModel


class FileProcessingResponse(BaseModel):
    context_id:str
    task_ids: List[str]
    status: str
    created_at: datetime

@dataclass
class ProcessingContext:
    context_id: str
    task_ids: List[str]
    status: str
    created_at: float

    @classmethod
    def create_new(cls, context_id: Optional[str] = None) -> 'ProcessingContext':
        return cls(
            context_id=context_id or str(uuid.uuid4()),
            task_ids=[],
            status="processing",
            created_at=datetime.now().timestamp()
        )