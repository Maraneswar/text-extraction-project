"""
Pydantic models for request/response schemas.
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from enum import Enum
import time
import uuid


class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


class FileType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    IMAGE = "image"


class UploadResponse(BaseModel):
    file_id: str
    filename: str
    file_type: str
    size_bytes: int
    size_human: str
    message: str


class DocumentMetadata(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    creation_date: Optional[str] = None
    modification_date: Optional[str] = None
    page_count: Optional[int] = None
    word_count: int = 0
    character_count: int = 0
    file_type: str = ""
    extra: Dict[str, Any] = {}


class ExtractionResult(BaseModel):
    raw_text: str
    metadata: DocumentMetadata
    success: bool = True
    error_message: Optional[str] = None
    extraction_time_ms: float = 0


class SummaryResult(BaseModel):
    summary: str
    original_length: int
    summary_length: int
    compression_ratio: float
    sentence_count: int
    algorithm: str


class Entity(BaseModel):
    text: str
    label: str
    label_description: str
    count: int = 1
    positions: List[int] = []


class EntityResult(BaseModel):
    entities: List[Entity]
    entity_counts: Dict[str, int]
    total_entities: int


class SentimentBreakdown(BaseModel):
    text: str
    compound: float
    positive: float
    negative: float
    neutral: float
    label: str


class SentimentResult(BaseModel):
    overall_compound: float
    overall_positive: float
    overall_negative: float
    overall_neutral: float
    overall_label: str
    sentence_breakdown: List[SentimentBreakdown]
    confidence: float


class ProcessingResult(BaseModel):
    file_id: str
    filename: str
    file_type: str
    status: TaskStatus
    extraction: Optional[ExtractionResult] = None
    summary: Optional[SummaryResult] = None
    entities: Optional[EntityResult] = None
    sentiment: Optional[SentimentResult] = None
    processing_time_ms: float = 0
    error_message: Optional[str] = None
    timestamp: float = 0

    @staticmethod
    def create_pending(file_id: str, filename: str, file_type: str) -> "ProcessingResult":
        return ProcessingResult(
            file_id=file_id,
            filename=filename,
            file_type=file_type,
            status=TaskStatus.PENDING,
            timestamp=time.time(),
        )
