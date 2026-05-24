"""
UST Smart Chatbot — Document Processor
Handles processing of various document formats (PDF, DOCX, TXT, JSON)
and splits them into chunks for the vector store.
"""

import json
import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Tuple

from config import CHUNK_SIZE, CHUNK_OVERLAP, KNOWLEDGE_BASE_DIR

logger = logging.getLogger(__name__)


def generate_chunk_id(source: str, index: int) -> str:
    """Generate a deterministic unique ID for a chunk."""
    raw = f"{source}::chunk_{index}"
    return hashlib.md5(raw.encode()).hexdigest()


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Split text into overlapping chunks by word count.

    Args:
        text: The full text to split
        chunk_size: Number of words per chunk
        overlap: Number of overlapping words between chunks

    Returns:
        List of text chunks
    """
    words = text.split()
    if len(words) <= chunk_size:
        return [text.strip()] if text.strip() else []

    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk.strip())
        start = end - overlap

    return chunks


def process_text_file(file_path: str, content: str = None) -> Tuple[List[str], List[Dict]]:
    """Process a plain text file into chunks."""
    if content is None:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

    chunks = chunk_text(content)
    source = Path(file_path).name if file_path else "manual_entry"

    metadatas = [
        {
            "source": source,
            "doc_type": "txt",
            "chunk_index": i,
            "total_chunks": len(chunks),
        }
        for i in range(len(chunks))
    ]

    return chunks, metadatas


def process_pdf_file(file_path: str) -> Tuple[List[str], List[Dict]]:
    """Process a PDF file into chunks."""
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        logger.error("PyPDF2 not installed. Run: pip install PyPDF2")
        return [], []

    reader = PdfReader(file_path)
    source = Path(file_path).name

    all_chunks = []
    all_metadatas = []

    for page_num, page in enumerate(reader.pages):
        text = page.extract_text()
        if not text or not text.strip():
            continue

        chunks = chunk_text(text)
        for i, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            all_metadatas.append({
                "source": source,
                "doc_type": "pdf",
                "page_number": page_num + 1,
                "chunk_index": len(all_chunks) - 1,
            })

    # Update total_chunks
    for meta in all_metadatas:
        meta["total_chunks"] = len(all_chunks)

    return all_chunks, all_metadatas


def process_docx_file(file_path: str) -> Tuple[List[str], List[Dict]]:
    """Process a Word document into chunks."""
    try:
        from docx import Document
    except ImportError:
        logger.error("python-docx not installed. Run: pip install python-docx")
        return [], []

    doc = Document(file_path)
    source = Path(file_path).name

    full_text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    chunks = chunk_text(full_text)

    metadatas = [
        {
            "source": source,
            "doc_type": "docx",
            "chunk_index": i,
            "total_chunks": len(chunks),
        }
        for i in range(len(chunks))
    ]

    return chunks, metadatas


def process_json_knowledge_base(file_path: str = None) -> Tuple[List[str], List[Dict]]:
    """
    Process the structured JSON knowledge base.
    Each entry becomes a separate chunk with rich metadata.
    """
    if file_path is None:
        file_path = str(KNOWLEDGE_BASE_DIR / "ust_data.json")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    chunks = []
    metadatas = []

    for entry in data:
        # Build a rich text chunk from the structured data
        text_parts = []

        if "category_ar" in entry:
            text_parts.append(f"التصنيف: {entry['category_ar']}")
        if "category_en" in entry:
            text_parts.append(f"Category: {entry['category_en']}")
        if "title_ar" in entry:
            text_parts.append(f"العنوان: {entry['title_ar']}")
        if "title_en" in entry:
            text_parts.append(f"Title: {entry['title_en']}")
        if "content_ar" in entry:
            text_parts.append(entry["content_ar"])
        if "content_en" in entry:
            text_parts.append(entry["content_en"])
        if "keywords" in entry:
            text_parts.append(f"الكلمات المفتاحية / Keywords: {', '.join(entry['keywords'])}")

        chunk_text_str = "\n".join(text_parts)

        # If chunk is too large, split it
        sub_chunks = chunk_text(chunk_text_str)
        if not sub_chunks:
            sub_chunks = [chunk_text_str]

        for i, sub in enumerate(sub_chunks):
            chunks.append(sub)
            metadatas.append({
                "source": "ust_knowledge_base",
                "doc_type": "json",
                "category": entry.get("category_en", "general"),
                "title": entry.get("title_en", ""),
                "chunk_index": len(chunks) - 1,
            })

    return chunks, metadatas


def process_file(file_path: str) -> Tuple[List[str], List[Dict], List[str]]:
    """
    Auto-detect file type and process accordingly.
    Returns (chunks, metadatas, chunk_ids).
    """
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext == ".pdf":
        chunks, metadatas = process_pdf_file(file_path)
    elif ext in (".docx", ".doc"):
        chunks, metadatas = process_docx_file(file_path)
    elif ext == ".json":
        chunks, metadatas = process_json_knowledge_base(file_path)
    elif ext in (".txt", ".md"):
        chunks, metadatas = process_text_file(file_path)
    else:
        logger.warning(f"Unsupported file type: {ext}")
        return [], [], []

    # Generate unique IDs
    ids = [generate_chunk_id(path.name, i) for i in range(len(chunks))]

    logger.info(f"Processed '{path.name}': {len(chunks)} chunks generated")
    return chunks, metadatas, ids


def export_db_to_json(db) -> Tuple[List[str], List[Dict], List[str]]:
    """
    Exports all active data from SQLite tables to unified JSON format,
    saves to ust_data.json, and returns chunks.
    """
    from models.database import (
        KnowledgeEntry, Faculty, Department, Program, TuitionFee, PaymentPlan,
        Scholarship, AcademicCalendar, AcademicRegulation, GradingSystem,
        Staff, Course, StudentService, FAQ, Announcement
    )
    import json

    entries = []

    # 1. KnowledgeEntries
    for k in db.query(KnowledgeEntry).filter(KnowledgeEntry.is_active == True).all():
        kw = []
        try:
            kw = json.loads(k.keywords) if k.keywords else []
        except:
            kw = [k.keywords] if k.keywords else []
        entries.append({
            "category_ar": k.category_ar, "category_en": k.category_en,
            "title_ar": k.title_ar, "title_en": k.title_en,
            "content_ar": k.content_ar, "content_en": k.content_en,
            "keywords": kw
        })

    # 2. Faculties
    for f in db.query(Faculty).filter(Faculty.is_active == True).all():
        entries.append({
            "category_ar": "كليات", "category_en": "Faculties",
            "title_ar": f.name_ar, "title_en": f.name_en,
            "content_ar": f"{f.description_ar}\nالعميد: {f.dean_name_ar}\nللتواصل: {f.email}",
            "content_en": f"{f.description_en}\nDean: {f.dean_name_en}\nContact: {f.email}",
            "keywords": ["faculty", "كلية", f.code]
        })

    # 3. Departments
    for d in db.query(Department).filter(Department.is_active == True).all():
        entries.append({
            "category_ar": "أقسام", "category_en": "Departments",
            "title_ar": d.name_ar, "title_en": d.name_en,
            "content_ar": f"{d.description_ar}\nرئيس القسم: {d.head_name_ar}",
            "content_en": f"{d.description_en}\nHead: {d.head_name_en}",
            "keywords": ["department", "قسم"]
        })

    # 4. Programs
    for p in db.query(Program).filter(Program.is_active == True).all():
        entries.append({
            "category_ar": "برامج دراسية", "category_en": "Programs",
            "title_ar": p.name_ar, "title_en": p.name_en,
            "content_ar": f"{p.description_ar}\nالمدة: {p.duration_years} سنوات",
            "content_en": f"{p.description_en}\nDuration: {p.duration_years} years",
            "keywords": ["program", "برنامج", p.degree_type]
        })

    # 5. Scholarships
    for s in db.query(Scholarship).filter(Scholarship.is_active == True).all():
        entries.append({
            "category_ar": "منح دراسية", "category_en": "Scholarships",
            "title_ar": s.name_ar, "title_en": s.name_en,
            "content_ar": f"الخصم: {s.discount_percentage}%\nالشروط: {s.eligibility_ar}\nالتقديم: {s.application_process_ar}",
            "content_en": f"Discount: {s.discount_percentage}%\nEligibility: {s.eligibility_en}\nProcess: {s.application_process_en}",
            "keywords": ["scholarship", "منحة", s.type]
        })

    # 6. Regulations
    for r in db.query(AcademicRegulation).filter(AcademicRegulation.is_active == True).all():
        entries.append({
            "category_ar": "لوائح أكاديمية", "category_en": "Academic Regulations",
            "title_ar": r.rule_title_ar, "title_en": r.rule_title_en,
            "content_ar": f"{r.rule_content_ar}\nالعقوبة: {r.penalty_ar}",
            "content_en": f"{r.rule_content_en}\nPenalty: {r.penalty_en}",
            "keywords": ["regulation", "لائحة", r.category]
        })

    # 7. FAQs
    for faq in db.query(FAQ).filter(FAQ.is_active == True).all():
        entries.append({
            "category_ar": "أسئلة شائعة", "category_en": "FAQs",
            "title_ar": faq.question_ar, "title_en": faq.question_en,
            "content_ar": faq.answer_ar, "content_en": faq.answer_en,
            "keywords": ["faq", "سؤال", faq.category]
        })

    # Save to file
    json_path = KNOWLEDGE_BASE_DIR / "ust_data.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

    # Return chunks
    return process_file(str(json_path))
