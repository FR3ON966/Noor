"""
UST Smart Chatbot — Chat API
Handles student chat interactions with the RAG pipeline.
"""

import json
import logging
import time
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from models.database import get_db
from models.schemas import (
    ChatRequest, ChatResponse, SourceChunk,
    FeedbackRequest, FeedbackResponse,
    ConversationOut, MessageOut,
)
from core.rag_pipeline import get_rag_pipeline
from services.conversation_service import ConversationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post("/", response_model=ChatResponse)
async def send_message(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Send a message to the chatbot and get a response.
    Creates a new conversation if conversation_id is not provided.
    """
    conv_service = ConversationService(db)
    rag = get_rag_pipeline()

    # Get or create conversation
    if request.conversation_id:
        conversation = conv_service.get_conversation(request.conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        lang = request.language if request.language != "auto" else "ar"
        conversation = conv_service.create_conversation(language=lang)

    # Save user message
    conv_service.add_message(
        conversation_id=conversation.id,
        role="user",
        content=request.message,
    )

    # Get conversation history for context
    history = conv_service.get_history(conversation.id, limit=8)

    # Run RAG pipeline
    result = await rag.answer(
        question=request.message,
        conversation_history=history[:-1],  # Exclude current message
        language=request.language or "auto",
    )

    # Save assistant message
    sources_data = [
        {"source": s["source"], "score": s["relevance_score"]}
        for s in result["sources"]
    ]
    assistant_msg = conv_service.add_message(
        conversation_id=conversation.id,
        role="assistant",
        content=result["answer"],
        retrieved_chunks=sources_data,
        confidence_score=result["confidence_score"],
        response_time_ms=result["response_time_ms"],
    )

    # Build response
    return ChatResponse(
        answer=result["answer"],
        conversation_id=conversation.id,
        message_id=assistant_msg.id,
        sources=[
            SourceChunk(
                content=s["content"],
                source=s["source"],
                relevance_score=s["relevance_score"],
            )
            for s in result["sources"]
        ],
        confidence_score=result["confidence_score"],
        response_time_ms=result["response_time_ms"],
        language=result["language"],
    )


@router.get("/new")
async def new_conversation(db: Session = Depends(get_db)):
    """Create a new empty conversation."""
    conv_service = ConversationService(db)
    conversation = conv_service.create_conversation()
    return {"conversation_id": conversation.id}


@router.get("/history/{conversation_id}")
async def get_history(conversation_id: str, db: Session = Depends(get_db)):
    """Get full conversation history."""
    conv_service = ConversationService(db)
    conversation = conv_service.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = conv_service.get_messages(conversation_id)

    return {
        "conversation_id": conversation.id,
        "started_at": conversation.started_at.isoformat(),
        "language": conversation.language,
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "timestamp": m.timestamp.isoformat(),
                "confidence_score": m.confidence_score,
            }
            for m in messages
        ],
    }


@router.post("/stream")
async def stream_message(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Stream a chat response using Server-Sent Events (SSE).
    Sends metadata first, then text chunks, then a done signal.
    """
    conv_service = ConversationService(db)
    rag = get_rag_pipeline()

    # Get or create conversation
    if request.conversation_id:
        conversation = conv_service.get_conversation(request.conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        lang = request.language if request.language != "auto" else "ar"
        conversation = conv_service.create_conversation(language=lang)

    # Save user message
    conv_service.add_message(
        conversation_id=conversation.id,
        role="user",
        content=request.message,
    )

    # Get conversation history
    history = conv_service.get_history(conversation.id, limit=8)

    # Get metadata + stream
    metadata, text_gen, start_time = await rag.answer_stream(
        question=request.message,
        conversation_history=history[:-1],
        language=request.language or "auto",
    )

    async def event_stream():
        full_answer = []

        # Send metadata first
        meta_event = {
            "type": "metadata",
            "conversation_id": conversation.id,
            "sources": [
                {"content": s["content"], "source": s["source"], "relevance_score": s["relevance_score"]}
                for s in metadata["sources"]
            ],
            "confidence_score": metadata["confidence_score"],
            "language": metadata["language"],
        }
        yield f"data: {json.dumps(meta_event, ensure_ascii=False)}\n\n"

        # Stream text chunks
        async for chunk in text_gen:
            full_answer.append(chunk)
            chunk_event = {"type": "chunk", "content": chunk}
            yield f"data: {json.dumps(chunk_event, ensure_ascii=False)}\n\n"

        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)

        # Save complete response to DB
        complete_text = "".join(full_answer)
        sources_data = [
            {"source": s["source"], "score": s["relevance_score"]}
            for s in metadata["sources"]
        ]
        assistant_msg = conv_service.add_message(
            conversation_id=conversation.id,
            role="assistant",
            content=complete_text,
            retrieved_chunks=sources_data,
            confidence_score=metadata["confidence_score"],
            response_time_ms=response_time_ms,
        )

        # Send done signal
        done_event = {
            "type": "done",
            "message_id": assistant_msg.id,
            "response_time_ms": response_time_ms,
        }
        yield f"data: {json.dumps(done_event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest, db: Session = Depends(get_db)):
    """Submit feedback on a chatbot response."""
    conv_service = ConversationService(db)
    try:
        conv_service.add_feedback(
            message_id=request.message_id,
            rating=request.rating,
            comment=request.comment,
        )
        return FeedbackResponse(success=True, message="شكراً لتقييمك! | Thank you for your feedback!")
    except Exception as e:
        logger.error(f"Feedback error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
