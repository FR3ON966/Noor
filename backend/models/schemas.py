"""
UST Smart Chatbot — Pydantic Schemas
API request/response models for type validation and serialization.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ──────────── Chat Schemas ────────────

class ChatRequest(BaseModel):
    """Request body for the chat endpoint."""
    message: str = Field(..., min_length=1, max_length=2000, description="Student's question")
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID")
    language: Optional[str] = Field("auto", description="Language: 'ar', 'en', or 'auto'")


class SourceChunk(BaseModel):
    """A retrieved knowledge base chunk used in the response."""
    content: str
    source: str
    relevance_score: float


class ChatResponse(BaseModel):
    """Response body from the chat endpoint."""
    answer: str
    conversation_id: str
    message_id: int
    sources: List[SourceChunk] = []
    confidence_score: float
    response_time_ms: int
    language: str


# ──────────── Conversation Schemas ────────────

class MessageOut(BaseModel):
    """Serialized message for conversation history."""
    id: int
    role: str
    content: str
    timestamp: datetime
    confidence_score: Optional[float] = None
    sources: Optional[List[SourceChunk]] = None

    class Config:
        from_attributes = True


class ConversationOut(BaseModel):
    """Serialized conversation with messages."""
    id: str
    started_at: datetime
    message_count: int
    language: str
    messages: List[MessageOut] = []

    class Config:
        from_attributes = True


# ──────────── Feedback Schemas ────────────

class FeedbackRequest(BaseModel):
    """Request body for submitting feedback."""
    message_id: int
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    comment: Optional[str] = Field(None, max_length=500)


class FeedbackResponse(BaseModel):
    """Response after submitting feedback."""
    success: bool
    message: str


# ──────────── Document Schemas ────────────

class DocumentOut(BaseModel):
    """Serialized document info."""
    id: int
    filename: str
    doc_type: str
    chunk_count: int
    added_at: datetime
    status: str

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """List of documents."""
    documents: List[DocumentOut]
    total: int


# ──────────── Analytics Schemas ────────────

class AnalyticsOverview(BaseModel):
    """Overview statistics."""
    total_conversations: int
    total_messages: int
    total_documents: int
    avg_confidence_score: float
    avg_response_time_ms: float
    total_feedback: int
    avg_rating: float
    coverage_rate: float  # % of questions answered (not "I don't know")


class TopQuestion(BaseModel):
    """A frequently asked question."""
    question: str
    count: int
    avg_confidence: float


class AnalyticsDetailResponse(BaseModel):
    """Detailed analytics response."""
    overview: AnalyticsOverview
    top_questions: List[TopQuestion] = []
    daily_stats: List[dict] = []
