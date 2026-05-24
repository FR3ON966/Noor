"""
UST Smart Chatbot — Database Models
SQLAlchemy ORM models for conversations, messages, documents, feedback,
and the structured university knowledge base.
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, String, Integer, Float, Text,
    DateTime, ForeignKey, JSON, Boolean
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

from config import DATABASE_URL

Base = declarative_base()


# ══════════════════════════════════════════════════════
#  Existing Models (unchanged)
# ══════════════════════════════════════════════════════

class Conversation(Base):
    """Stores chat conversation sessions."""
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    message_count = Column(Integer, default=0)
    language = Column(String, default="ar")  # "ar" or "en"

    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    """Stores individual chat messages with RAG metadata."""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    role = Column(String, nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    tokens_used = Column(Integer, nullable=True)
    retrieved_chunks = Column(JSON, nullable=True)  # List of chunk IDs used
    confidence_score = Column(Float, nullable=True)
    response_time_ms = Column(Integer, nullable=True)

    conversation = relationship("Conversation", back_populates="messages")
    feedback = relationship("Feedback", back_populates="message", uselist=False)


class Document(Base):
    """Tracks uploaded knowledge base documents."""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String, nullable=False)
    doc_type = Column(String, nullable=False)  # "pdf", "docx", "txt", "json", "manual"
    original_size = Column(Integer, nullable=True)  # bytes
    chunk_count = Column(Integer, default=0)
    added_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="pending")  # "processed", "pending", "failed"
    metadata_json = Column(JSON, nullable=True)


class Feedback(Base):
    """Stores user feedback on assistant responses."""
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5
    comment = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    message = relationship("Message", back_populates="feedback")


# ══════════════════════════════════════════════════════
#  New Models — University Knowledge Base
# ══════════════════════════════════════════════════════

class AdminUser(Base):
    """Admin users with role-based access control."""
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="content_manager")  # "super_admin", "content_manager"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class KnowledgeEntry(Base):
    """General knowledge base entries (bilingual)."""
    __tablename__ = "knowledge_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category_ar = Column(Text, nullable=True)
    category_en = Column(Text, nullable=True)
    title_ar = Column(Text, nullable=True)
    title_en = Column(Text, nullable=True)
    content_ar = Column(Text, nullable=True)
    content_en = Column(Text, nullable=True)
    keywords = Column(Text, nullable=True)  # JSON array of keywords
    is_active = Column(Boolean, default=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Faculty(Base):
    """University faculties."""
    __tablename__ = "faculties"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name_ar = Column(Text, nullable=True)
    name_en = Column(Text, nullable=True)
    code = Column(String, nullable=True)  # e.g. ENG, CS, MED
    dean_name_ar = Column(Text, nullable=True)
    dean_name_en = Column(Text, nullable=True)
    email = Column(String, nullable=True)
    website = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    description_ar = Column(Text, nullable=True)
    description_en = Column(Text, nullable=True)
    established_year = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)

    departments = relationship("Department", back_populates="faculty", cascade="all, delete-orphan")
    staff_members = relationship("Staff", back_populates="faculty")
    tuition_fees = relationship("TuitionFee", back_populates="faculty")
    payment_plans = relationship("PaymentPlan", back_populates="faculty")


class Department(Base):
    """Academic departments within faculties."""
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    faculty_id = Column(Integer, ForeignKey("faculties.id"), nullable=False)
    name_ar = Column(Text, nullable=True)
    name_en = Column(Text, nullable=True)
    head_name_ar = Column(Text, nullable=True)
    head_name_en = Column(Text, nullable=True)
    email = Column(String, nullable=True)
    description_ar = Column(Text, nullable=True)
    description_en = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

    faculty = relationship("Faculty", back_populates="departments")
    programs = relationship("Program", back_populates="department", cascade="all, delete-orphan")
    staff_members = relationship("Staff", back_populates="department")
    courses = relationship("Course", back_populates="department")


class Program(Base):
    """Degree programs within departments."""
    __tablename__ = "programs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    name_ar = Column(Text, nullable=True)
    name_en = Column(Text, nullable=True)
    degree_type = Column(String, nullable=True)  # honours_bachelor, general_bachelor, diploma, certificate, masters, phd
    duration_years = Column(Float, nullable=True)  # 5, 4, 3, 2, 1
    total_credit_hours = Column(Integer, nullable=True)
    description_ar = Column(Text, nullable=True)
    description_en = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

    department = relationship("Department", back_populates="programs")
    courses = relationship("Course", back_populates="program")
    tuition_fees = relationship("TuitionFee", back_populates="program")


class TuitionFee(Base):
    """Tuition fee schedules."""
    __tablename__ = "tuition_fees"

    id = Column(Integer, primary_key=True, autoincrement=True)
    faculty_id = Column(Integer, ForeignKey("faculties.id"), nullable=True)
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=True)
    academic_year = Column(String, nullable=True)  # '2025-2026'
    study_year = Column(Integer, nullable=True)  # 1, 2, 3, 4, 5
    fee_type = Column(String, nullable=True)  # registration, semester, annual, lab, library, activity, graduation
    amount = Column(Float, nullable=True)
    currency = Column(String, default="SDG")  # SDG | USD | EGP
    description_ar = Column(Text, nullable=True)
    description_en = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

    faculty = relationship("Faculty", back_populates="tuition_fees")
    program = relationship("Program", back_populates="tuition_fees")


class PaymentPlan(Base):
    """Installment payment plans."""
    __tablename__ = "payment_plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    faculty_id = Column(Integer, ForeignKey("faculties.id"), nullable=True)
    academic_year = Column(String, nullable=True)
    installment_number = Column(Integer, nullable=True)  # 1, 2, 3...
    due_date = Column(String, nullable=True)
    percentage = Column(Float, nullable=True)  # % of total
    amount = Column(Float, nullable=True)
    notes_ar = Column(Text, nullable=True)
    notes_en = Column(Text, nullable=True)

    faculty = relationship("Faculty", back_populates="payment_plans")


class Scholarship(Base):
    """Scholarships and discounts."""
    __tablename__ = "scholarships"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name_ar = Column(Text, nullable=True)
    name_en = Column(Text, nullable=True)
    type = Column(String, nullable=True)  # excellence, need_based, sports, staff_family, external
    discount_percentage = Column(Float, nullable=True)
    eligibility_ar = Column(Text, nullable=True)
    eligibility_en = Column(Text, nullable=True)
    application_process_ar = Column(Text, nullable=True)
    application_process_en = Column(Text, nullable=True)
    deadline = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)


class AcademicCalendar(Base):
    """Academic calendar events."""
    __tablename__ = "academic_calendar"

    id = Column(Integer, primary_key=True, autoincrement=True)
    academic_year = Column(String, nullable=True)  # '2025-2026'
    semester = Column(String, nullable=True)  # first, second, summer
    event_type = Column(String, nullable=True)  # semester_start, semester_end, etc.
    event_name_ar = Column(Text, nullable=True)
    event_name_en = Column(Text, nullable=True)
    start_date = Column(String, nullable=True)  # YYYY-MM-DD
    end_date = Column(String, nullable=True)
    notes_ar = Column(Text, nullable=True)
    notes_en = Column(Text, nullable=True)


class AcademicRegulation(Base):
    """Academic regulations and rules."""
    __tablename__ = "academic_regulations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String, nullable=True)  # attendance, grading, disciplinary, examination, graduation, withdrawal
    rule_title_ar = Column(Text, nullable=True)
    rule_title_en = Column(Text, nullable=True)
    rule_content_ar = Column(Text, nullable=True)
    rule_content_en = Column(Text, nullable=True)
    penalty_ar = Column(Text, nullable=True)
    penalty_en = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)


class GradingSystem(Base):
    """University grading system."""
    __tablename__ = "grading_system"

    id = Column(Integer, primary_key=True, autoincrement=True)
    grade_letter = Column(String, nullable=True)  # A+, A, B+, ...
    grade_points = Column(Float, nullable=True)  # 4.0, 4.0, 3.5, ...
    percentage_min = Column(Float, nullable=True)
    percentage_max = Column(Float, nullable=True)
    description_ar = Column(Text, nullable=True)
    description_en = Column(Text, nullable=True)
    is_passing = Column(Boolean, nullable=True)


class Staff(Base):
    """Faculty and staff members."""
    __tablename__ = "staff"

    id = Column(Integer, primary_key=True, autoincrement=True)
    faculty_id = Column(Integer, ForeignKey("faculties.id"), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    name_ar = Column(Text, nullable=True)
    name_en = Column(Text, nullable=True)
    title_ar = Column(Text, nullable=True)  # دكتور، أستاذ، ...
    title_en = Column(Text, nullable=True)
    position_ar = Column(Text, nullable=True)  # رئيس قسم، عضو هيئة تدريس
    position_en = Column(Text, nullable=True)
    email = Column(String, nullable=True)
    office_hours_ar = Column(Text, nullable=True)
    office_location = Column(String, nullable=True)
    specialization_ar = Column(Text, nullable=True)
    specialization_en = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

    faculty = relationship("Faculty", back_populates="staff_members")
    department = relationship("Department", back_populates="staff_members")


class Course(Base):
    """Course catalog."""
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=True)
    course_code = Column(String, nullable=True)  # CS301, ENG201, ...
    name_ar = Column(Text, nullable=True)
    name_en = Column(Text, nullable=True)
    credit_hours = Column(Integer, nullable=True)
    course_type = Column(String, nullable=True)  # core, elective, university_requirement, practical
    study_year = Column(Integer, nullable=True)
    semester = Column(String, nullable=True)  # first, second, both
    prerequisites = Column(Text, nullable=True)  # JSON array of course codes
    description_ar = Column(Text, nullable=True)
    description_en = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

    department = relationship("Department", back_populates="courses")
    program = relationship("Program", back_populates="courses")


class StudentService(Base):
    """Student services."""
    __tablename__ = "student_services"

    id = Column(Integer, primary_key=True, autoincrement=True)
    service_name_ar = Column(Text, nullable=True)
    service_name_en = Column(Text, nullable=True)
    service_type = Column(String, nullable=True)  # housing, health, library, sports, transport, cafeteria, clubs, counseling
    description_ar = Column(Text, nullable=True)
    description_en = Column(Text, nullable=True)
    availability_ar = Column(Text, nullable=True)
    availability_en = Column(Text, nullable=True)
    location = Column(String, nullable=True)
    contact = Column(String, nullable=True)
    fees = Column(Float, default=0)
    is_active = Column(Boolean, default=True)


class FAQ(Base):
    """Frequently asked questions."""
    __tablename__ = "faqs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    question_ar = Column(Text, nullable=True)
    question_en = Column(Text, nullable=True)
    answer_ar = Column(Text, nullable=True)
    answer_en = Column(Text, nullable=True)
    category = Column(String, nullable=True)  # admission, fees, academic, general, exams, housing
    is_featured = Column(Boolean, default=False)
    view_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)


class Announcement(Base):
    """News and announcements."""
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title_ar = Column(Text, nullable=True)
    title_en = Column(Text, nullable=True)
    content_ar = Column(Text, nullable=True)
    content_en = Column(Text, nullable=True)
    type = Column(String, nullable=True)  # news, announcement, urgent, event
    target_audience = Column(String, nullable=True)  # all, students, staff, new_students
    publish_date = Column(String, nullable=True)
    expiry_date = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)


class AuditLog(Base):
    """Audit log for admin changes."""
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String, nullable=False)  # e.g. 'faculty', 'course', 'knowledge_entry'
    entity_id = Column(Integer, nullable=True)
    action = Column(String, nullable=False)  # 'create', 'update', 'delete', 'toggle'
    changes = Column(JSON, nullable=True)  # JSON diff of changed fields
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(Text, nullable=True)  # Optional human-readable description


# ──────────── Database Setup ────────────

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
