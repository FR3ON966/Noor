"""
UST Smart Chatbot — Conversation Service
Manages conversation sessions, message storage, and history retrieval.
"""

import uuid
import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from models.database import Conversation, Message, Feedback

logger = logging.getLogger(__name__)


class ConversationService:
    """Handles conversation lifecycle and message persistence."""

    def __init__(self, db: Session):
        self.db = db

    def create_conversation(self, language: str = "ar") -> Conversation:
        """Create a new conversation session."""
        conv = Conversation(
            id=str(uuid.uuid4()),
            started_at=datetime.utcnow(),
            language=language,
            message_count=0,
        )
        self.db.add(conv)
        self.db.commit()
        self.db.refresh(conv)
        logger.info(f"Created conversation: {conv.id}")
        return conv

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation by ID."""
        return self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        retrieved_chunks: list = None,
        confidence_score: float = None,
        response_time_ms: int = None,
    ) -> Message:
        """Add a message to a conversation."""
        msg = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            timestamp=datetime.utcnow(),
            retrieved_chunks=retrieved_chunks,
            confidence_score=confidence_score,
            response_time_ms=response_time_ms,
        )
        self.db.add(msg)

        # Update conversation message count
        conv = self.get_conversation(conversation_id)
        if conv:
            conv.message_count = (conv.message_count or 0) + 1

        self.db.commit()
        self.db.refresh(msg)
        return msg

    def get_history(
        self,
        conversation_id: str,
        limit: int = 10
    ) -> List[dict]:
        """Get conversation history as a list of {role, content} dicts."""
        messages = (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.timestamp.asc())
            .limit(limit)
            .all()
        )
        return [{"role": m.role, "content": m.content} for m in messages]

    def get_messages(self, conversation_id: str) -> List[Message]:
        """Get all messages for a conversation."""
        return (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.timestamp.asc())
            .all()
        )

    def add_feedback(
        self,
        message_id: int,
        rating: int,
        comment: str = None,
    ) -> Feedback:
        """Add or update feedback for a message."""
        fb = self.db.query(Feedback).filter(Feedback.message_id == message_id).first()
        if fb:
            fb.rating = rating
            fb.comment = comment
            fb.timestamp = datetime.utcnow()
        else:
            fb = Feedback(
                message_id=message_id,
                rating=rating,
                comment=comment,
                timestamp=datetime.utcnow(),
            )
            self.db.add(fb)
        self.db.commit()
        self.db.refresh(fb)
        return fb

    def get_all_conversations(
        self,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Conversation]:
        """Get all conversations, newest first."""
        return (
            self.db.query(Conversation)
            .order_by(Conversation.started_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_analytics(self) -> dict:
        """Calculate analytics overview."""
        from sqlalchemy import func

        total_convs = self.db.query(func.count(Conversation.id)).scalar() or 0
        total_msgs = self.db.query(func.count(Message.id)).scalar() or 0

        # Average confidence for assistant messages
        avg_conf = (
            self.db.query(func.avg(Message.confidence_score))
            .filter(Message.role == "assistant")
            .filter(Message.confidence_score.isnot(None))
            .scalar()
        ) or 0.0

        # Average response time
        avg_time = (
            self.db.query(func.avg(Message.response_time_ms))
            .filter(Message.role == "assistant")
            .filter(Message.response_time_ms.isnot(None))
            .scalar()
        ) or 0.0

        # Feedback stats
        total_fb = self.db.query(func.count(Feedback.id)).scalar() or 0
        avg_rating = self.db.query(func.avg(Feedback.rating)).scalar() or 0.0

        # Coverage: messages with confidence > 0 / total assistant messages
        total_assistant = (
            self.db.query(func.count(Message.id))
            .filter(Message.role == "assistant")
            .scalar()
        ) or 1
        answered = (
            self.db.query(func.count(Message.id))
            .filter(Message.role == "assistant")
            .filter(Message.confidence_score > CONFIDENCE_THRESHOLD)
            .scalar()
        ) or 0

        coverage = (answered / total_assistant) * 100 if total_assistant > 0 else 0

        return {
            "total_conversations": total_convs,
            "total_messages": total_msgs,
            "avg_confidence_score": round(float(avg_conf), 4),
            "avg_response_time_ms": round(float(avg_time), 2),
            "total_feedback": total_fb,
            "avg_rating": round(float(avg_rating), 2),
            "coverage_rate": round(coverage, 2),
        }


# Import at bottom to avoid circular
from config import CONFIDENCE_THRESHOLD
