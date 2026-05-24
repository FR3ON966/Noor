"""
UST Smart Chatbot — Analytics API
Provides statistics and performance metrics for the chatbot system.
"""

import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, cast, Date, asc
from datetime import datetime, timedelta

from models.database import get_db, Conversation, Message, Feedback, Document
from models.schemas import AnalyticsOverview, AnalyticsDetailResponse
from services.conversation_service import ConversationService
from core.vector_store import get_vector_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/analytics", tags=["Analytics"])


@router.get("/overview")
async def get_overview(db: Session = Depends(get_db)):
    """Get overall system analytics."""
    conv_service = ConversationService(db)
    analytics = conv_service.get_analytics()

    # Add document count
    total_docs = db.query(func.count(Document.id)).scalar() or 0
    vector_store = get_vector_store()

    return {
        **analytics,
        "total_documents": total_docs,
        "total_chunks_in_index": vector_store.get_document_count(),
    }


@router.get("/questions")
async def get_top_questions(limit: int = 20, db: Session = Depends(get_db)):
    """Get most frequently asked questions."""
    # Get user messages grouped by content similarity
    user_messages = (
        db.query(Message.content, func.count(Message.id).label("count"))
        .filter(Message.role == "user")
        .group_by(Message.content)
        .order_by(func.count(Message.id).desc())
        .limit(limit)
        .all()
    )

    return {
        "top_questions": [
            {"question": m.content, "count": m.count}
            for m in user_messages
        ],
    }


@router.get("/accuracy")
async def get_accuracy_metrics(db: Session = Depends(get_db)):
    """Get accuracy and performance metrics."""
    # Confidence score distribution
    assistant_msgs = (
        db.query(Message)
        .filter(Message.role == "assistant")
        .filter(Message.confidence_score.isnot(None))
        .all()
    )

    if not assistant_msgs:
        return {
            "total_responses": 0,
            "avg_confidence": 0,
            "high_confidence_rate": 0,
            "low_confidence_rate": 0,
            "avg_response_time_ms": 0,
        }

    total = len(assistant_msgs)
    high_conf = sum(1 for m in assistant_msgs if m.confidence_score >= 0.7)
    low_conf = sum(1 for m in assistant_msgs if m.confidence_score < 0.3)

    avg_conf = sum(m.confidence_score for m in assistant_msgs) / total
    avg_time = sum(
        m.response_time_ms for m in assistant_msgs if m.response_time_ms
    ) / max(sum(1 for m in assistant_msgs if m.response_time_ms), 1)

    # Feedback metrics
    feedbacks = db.query(Feedback).all()
    avg_rating = sum(f.rating for f in feedbacks) / len(feedbacks) if feedbacks else 0

    return {
        "total_responses": total,
        "avg_confidence": round(avg_conf, 4),
        "high_confidence_rate": round((high_conf / total) * 100, 2),
        "low_confidence_rate": round((low_conf / total) * 100, 2),
        "avg_response_time_ms": round(avg_time, 2),
        "total_feedbacks": len(feedbacks),
        "avg_rating": round(avg_rating, 2),
    }


@router.get("/response-times")
async def get_response_times(db: Session = Depends(get_db)):
    """Get response time statistics."""
    times = (
        db.query(Message.response_time_ms)
        .filter(Message.role == "assistant")
        .filter(Message.response_time_ms.isnot(None))
        .all()
    )

    if not times:
        return {"avg_ms": 0, "min_ms": 0, "max_ms": 0, "count": 0}

    values = [t[0] for t in times]
    return {
        "avg_ms": round(sum(values) / len(values), 2),
        "min_ms": min(values),
        "max_ms": max(values),
        "count": len(values),
    }


@router.get("/charts")
async def get_charts_data(db: Session = Depends(get_db)):
    """Get time-series data for charts."""
    # Last 7 days conversations
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    
    # Conversations per day
    daily_convs = (
        db.query(
            func.date(Conversation.started_at).label('date'),
            func.count(Conversation.id).label('count')
        )
        .filter(Conversation.started_at >= seven_days_ago)
        .group_by(func.date(Conversation.started_at))
        .order_by(asc('date'))
        .all()
    )

    conv_dates = [str(r.date) for r in daily_convs]
    conv_counts = [r.count for r in daily_convs]

    # Feedback distribution
    feedbacks = db.query(Feedback.rating, func.count(Feedback.id).label('count')).group_by(Feedback.rating).all()
    feedback_dist = {r.rating: r.count for r in feedbacks}
    
    positive = feedback_dist.get(4, 0) + feedback_dist.get(5, 0) + feedback_dist.get(3, 0)
    negative = feedback_dist.get(1, 0) + feedback_dist.get(2, 0)

    return {
        "conversations_chart": {
            "labels": conv_dates,
            "data": conv_counts
        },
        "feedback_chart": {
            "positive": positive,
            "negative": negative
        }
    }


@router.get("/feedback-review")
async def get_feedback_review(limit: int = 50, db: Session = Depends(get_db)):
    """Get negative feedback with the associated conversation context for review."""
    bad_feedbacks = (
        db.query(Feedback)
        .options(joinedload(Feedback.message).joinedload(Message.conversation))
        .filter(Feedback.rating <= 2)
        .order_by(Feedback.timestamp.desc())
        .limit(limit)
        .all()
    )

    result = []
    for fb in bad_feedbacks:
        # Get the preceding user message to show context
        user_msg = (
            db.query(Message)
            .filter(Message.conversation_id == fb.message.conversation_id)
            .filter(Message.role == "user")
            .filter(Message.timestamp < fb.message.timestamp)
            .order_by(Message.timestamp.desc())
            .first()
        )
        
        result.append({
            "feedback_id": fb.id,
            "rating": fb.rating,
            "comment": fb.comment,
            "timestamp": fb.timestamp.isoformat(),
            "bot_response": fb.message.content,
            "user_question": user_msg.content if user_msg else "N/A",
            "conversation_id": fb.message.conversation_id
        })
        
    return {"reviews": result}
