"""
UST Smart Chatbot — RAG Pipeline
The core retrieval-augmented generation pipeline.
Orchestrates: Query → Embed → Search → Context → LLM → Response
"""

import logging
import re
import time
from typing import List, Optional, Tuple

from config import (
    SYSTEM_PROMPT_AR, SYSTEM_PROMPT_EN,
    TOP_K_RESULTS, CONFIDENCE_THRESHOLD
)
from core.vector_store import get_vector_store
from core.llm_handler import get_llm_handler

logger = logging.getLogger(__name__)


def detect_language(text: str) -> str:
    """Detect if text is primarily Arabic or English."""
    arabic_pattern = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+')
    arabic_chars = len(arabic_pattern.findall(text))
    latin_chars = len(re.findall(r'[a-zA-Z]+', text))

    if arabic_chars > latin_chars:
        return "ar"
    elif latin_chars > arabic_chars:
        return "en"
    else:
        return "ar"  # Default to Arabic


# ──────── Smart Casual Detection ────────

GREETINGS_AR = [
    "السلام عليكم", "سلام عليكم", "مرحبا", "مرحبأ", "هلا", "اهلا", "أهلا",
    "هاي", "هاى", "صباح الخير", "مساء الخير", "سلام", "الو", "ألو",
    "يا هلا", "اهلين", "هلو", "hello", "hi", "hey", "مرحب",
]

FAREWELLS_AR = [
    "مع السلامة", "باي", "باى", "سلام", "الله معاك", "في أمان الله",
    "مع السلامه", "بالسلامة", "bye", "goodbye", "شكرا باي", "يلا باي",
    "تصبح على خير", "الله يوفقك",
]

THANKS_AR = [
    "شكرا", "شكراً", "تسلم", "تسلمي", "مشكور", "مشكورة", "جزاك الله",
    "جزاكي", "الله يعطيك العافية", "يعطيك العافية", "thanks", "thank you",
    "ممتنة", "ممتن", "تشكرات",
]

IDENTITY_AR = [
    "اسمك شنو", "انتي منو", "انت منو", "من انت", "من انتي", "مين انت",
    "عرف نفسك", "عرفي نفسك", "who are you", "what is your name",
    "شنو اسمك", "اسمك ايه", "اسمك إيه",
]

HOWRU_AR = [
    "كيف حالك", "كيفك", "كيف الحال", "عامل كيف", "عاملة كيف",
    "ازيك", "إزيك", "كيف اخبارك", "شلونك", "how are you",
    "تمام", "اخبارك شنو", "اخبارك ايه",
]

# Patterns for messages that are NOT real questions (gibberish, too short, etc.)
UNCLEAR_PATTERNS = [
    r'^\.+$',           # Just dots
    r'^[!؟?]+$',        # Just punctuation
    r'^\W+$',           # Only non-word chars
    r'^.{1,2}$',        # 1-2 chars only
]


def is_unclear_message(text: str) -> bool:
    """Check if a message is too unclear/short to be a real question."""
    clean = text.strip()
    if not clean:
        return True
    # Check regex patterns
    for pattern in UNCLEAR_PATTERNS:
        if re.match(pattern, clean):
            return True
    return False


def detect_casual(text: str) -> dict | None:
    """
    Detect if a message is casual (greeting, farewell, thanks, etc.)
    or unclear/gibberish.
    Returns an instant response dict or None if it's a real question.
    """
    clean = text.strip().lower()
    # Remove punctuation for matching
    clean_no_punct = re.sub(r'[؟?!.,،؛\s]+', ' ', clean).strip()

    # Check for unclear/gibberish messages first
    if is_unclear_message(clean):
        return {
            "answer": "ما فهمت سؤالك تماماً 😅\nممكن توضح أكتر؟ مثلاً اسألني عن:\n• شروط القبول والتسجيل\n• الكليات والأقسام\n• الرسوم الدراسية\n• خدمات الطلاب\n\nأو أي شيء يخص جامعة العلوم والتقانة! 🎓",
            "is_casual": True,
            "confidence_score": 1.0,
        }

    # Check greetings
    for g in GREETINGS_AR:
        if g in clean or clean_no_punct.startswith(g):
            return {
                "answer": "وعليكم السلام ورحمة الله! 😊\nأهلاً بيك! أنا نور، المساعدة الذكية لجامعة العلوم والتقانة.\nكيف أقدر أساعدك اليوم؟ 🎓",
                "is_casual": True,
                "confidence_score": 1.0,
            }

    # Check farewells
    for f in FAREWELLS_AR:
        if f in clean or clean_no_punct.startswith(f):
            return {
                "answer": "مع السلامة! 👋\nربنا يوفقك في دراستك. لو احتجت أي مساعدة تاني، أنا هنا دايماً! 🌟",
                "is_casual": True,
                "confidence_score": 1.0,
            }

    # Check thanks
    for t in THANKS_AR:
        if t in clean:
            return {
                "answer": "العفو! 😊 ده واجبي. لو عندك أي أسئلة تانية عن الجامعة، أنا في الخدمة! 🎓",
                "is_casual": True,
                "confidence_score": 1.0,
            }

    # Check identity questions
    for i in IDENTITY_AR:
        if i in clean or i in clean_no_punct:
            return {
                "answer": "أنا نور 🌟، المساعدة الذكية لجامعة العلوم والتقانة (UST).\nأقدر أساعدك في:\n• معلومات عن الكليات والأقسام\n• شروط القبول والتسجيل\n• الرسوم الدراسية\n• خدمات الطلاب والدعم الفني\n• وأي استفسار عن الجامعة!\n\nاسألني أي حاجة 😊",
                "is_casual": True,
                "confidence_score": 1.0,
            }

    # Check how are you
    for h in HOWRU_AR:
        if h in clean or h in clean_no_punct:
            return {
                "answer": "الحمد لله تمام! 😊 شكراً إنك سألت.\nكيف أقدر أساعدك اليوم؟ 🎓",
                "is_casual": True,
                "confidence_score": 1.0,
            }

    return None


class RAGPipeline:
    """
    Retrieval-Augmented Generation Pipeline for UST student chatbot.

    Flow:
    1. Receive student question
    2. Detect language
    3. Search vector store for relevant chunks
    4. Build context from retrieved chunks
    5. Construct prompt with system instructions + context + question
    6. Send to LLM for natural language generation
    7. Return response with metadata
    """

    def __init__(self):
        self.vector_store = get_vector_store()
        self.llm = get_llm_handler()

    async def answer(
        self,
        question: str,
        conversation_history: Optional[List[dict]] = None,
        language: str = "auto",
        top_k: int = TOP_K_RESULTS,
    ) -> dict:
        """
        Process a student question through the full RAG pipeline.

        Args:
            question: The student's question
            conversation_history: Previous messages [{role, content}, ...]
            language: "ar", "en", or "auto" (auto-detect)
            top_k: Number of chunks to retrieve

        Returns:
            dict with: answer, sources, confidence_score, language, response_time_ms
        """
        start_time = time.time()

        # Step 0: Check for casual conversation (instant response)
        casual = detect_casual(question)
        if casual:
            response_time_ms = int((time.time() - start_time) * 1000)
            return {
                "answer": casual["answer"],
                "sources": [],
                "confidence_score": 1.0,
                "language": "ar",
                "response_time_ms": response_time_ms,
                "chunks_retrieved": 0,
            }

        # Step 1: Detect language
        if language == "auto":
            language = detect_language(question)

        # Step 1.5: Query structured database
        from services.structured_query import StructuredQueryService
        from models.database import SessionLocal
        db = SessionLocal()
        try:
            sq = StructuredQueryService(db)
            structured_context = sq.detect_and_query(question)
        finally:
            db.close()

        # Step 2: Search for relevant chunks
        search_results = self.vector_store.search(query=question, top_k=top_k)

        # Step 3: Build context from retrieved chunks
        context_parts = []
        if structured_context:
            context_parts.append(f'[بيانات مباشرة | Direct Data]:\n{structured_context}')
        sources = []
        total_similarity = 0

        for i, result in enumerate(search_results):
            if result["similarity_score"] >= CONFIDENCE_THRESHOLD:
                context_parts.append(
                    f"[مصدر {i+1} | Source {i+1}]: {result['content']}"
                )
                sources.append({
                    "content": result["content"][:200] + "..." if len(result["content"]) > 200 else result["content"],
                    "source": result["metadata"].get("source", "unknown"),
                    "relevance_score": result["similarity_score"],
                })
                total_similarity += result["similarity_score"]

        # Calculate average confidence
        confidence_score = (total_similarity / len(sources)) if sources else 0.0

        # Build context string
        if context_parts:
            context = "\n\n".join(context_parts)
        else:
            context = "لا توجد معلومات ذات صلة في قاعدة المعرفة. | No relevant information found in the knowledge base."

        # Step 4: Build conversation history string
        history_text = ""
        if conversation_history:
            history_parts = []
            for msg in conversation_history[-8:]:  # Last 8 messages for better memory
                role_label = "الطالب" if msg["role"] == "user" else "نور"
                history_parts.append(f"{role_label}: {msg['content']}")
            history_text = "\n".join(history_parts)

        # Step 5: Select and fill the prompt template
        prompt_template = SYSTEM_PROMPT_AR if language == "ar" else SYSTEM_PROMPT_EN
        full_prompt = prompt_template.format(
            context=context,
            history=history_text or "لا توجد محادثة سابقة | No previous conversation",
            question=question,
        )

        # Step 6: Generate response from LLM
        try:
            answer = await self.llm.generate(prompt=full_prompt)
        except ConnectionError:
            answer = (
                "عذراً، لا يمكنني الاتصال بنموذج الذكاء الاصطناعي حالياً. "
                "يرجى التأكد من تشغيل Ollama والمحاولة مرة أخرى.\n\n"
                "Sorry, I cannot connect to the AI model right now. "
                "Please make sure Ollama is running and try again."
            )
            confidence_score = 0.0
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            answer = "حدث خطأ أثناء معالجة سؤالك. يرجى المحاولة مرة أخرى. | An error occurred. Please try again."
            confidence_score = 0.0

        # Step 7: Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)

        return {
            "answer": answer,
            "sources": sources,
            "confidence_score": round(confidence_score, 4),
            "language": language,
            "response_time_ms": response_time_ms,
            "chunks_retrieved": len(sources),
        }


    async def answer_stream(
        self,
        question: str,
        conversation_history: Optional[List[dict]] = None,
        language: str = "auto",
        top_k: int = TOP_K_RESULTS,
    ):
        """
        Stream a response through the RAG pipeline.
        Returns metadata first, then yields text chunks.
        """
        start_time = time.time()

        # Check for casual conversation (instant response)
        casual = detect_casual(question)
        if casual:
            metadata = {
                "sources": [],
                "confidence_score": 1.0,
                "language": "ar",
                "chunks_retrieved": 0,
            }
            async def instant_stream():
                yield casual["answer"]
            return metadata, instant_stream(), start_time

        # Detect language
        if language == "auto":
            language = detect_language(question)

        # Query structured database
        from services.structured_query import StructuredQueryService
        from models.database import SessionLocal
        db = SessionLocal()
        try:
            sq = StructuredQueryService(db)
            structured_context = sq.detect_and_query(question)
        finally:
            db.close()

        # Search for relevant chunks
        search_results = self.vector_store.search(query=question, top_k=top_k)

        # Build context
        context_parts = []
        if structured_context:
            context_parts.append(f'[بيانات مباشرة | Direct Data]:\n{structured_context}')
        sources = []
        total_similarity = 0

        for i, result in enumerate(search_results):
            if result["similarity_score"] >= CONFIDENCE_THRESHOLD:
                context_parts.append(
                    f"[مصدر {i+1} | Source {i+1}]: {result['content']}"
                )
                sources.append({
                    "content": result["content"][:200] + "..." if len(result["content"]) > 200 else result["content"],
                    "source": result["metadata"].get("source", "unknown"),
                    "relevance_score": result["similarity_score"],
                })
                total_similarity += result["similarity_score"]

        confidence_score = (total_similarity / len(sources)) if sources else 0.0

        if context_parts:
            context = "\n\n".join(context_parts)
        else:
            context = "لا توجد معلومات ذات صلة في قاعدة المعرفة."

        # Build history
        history_text = ""
        if conversation_history:
            history_parts = []
            for msg in conversation_history[-8:]:
                role_label = "الطالب" if msg["role"] == "user" else "نور"
                history_parts.append(f"{role_label}: {msg['content']}")
            history_text = "\n".join(history_parts)

        # Build prompt
        prompt_template = SYSTEM_PROMPT_AR if language == "ar" else SYSTEM_PROMPT_EN
        full_prompt = prompt_template.format(
            context=context,
            history=history_text or "لا توجد محادثة سابقة",
            question=question,
        )

        # Return metadata + stream generator
        metadata = {
            "sources": sources,
            "confidence_score": round(confidence_score, 4),
            "language": language,
            "chunks_retrieved": len(sources),
        }

        async def text_stream():
            try:
                async for chunk in self.llm.generate_stream(prompt=full_prompt):
                    yield chunk
            except Exception as e:
                logger.error(f"LLM stream error: {e}")
                yield "عذراً، حدث خطأ أثناء معالجة سؤالك."

        return metadata, text_stream(), start_time


# Global singleton
_rag_pipeline = None


def get_rag_pipeline() -> RAGPipeline:
    """Get or create the global RAGPipeline instance."""
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipeline()
    return _rag_pipeline

