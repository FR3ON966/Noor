"""
UST Smart Chatbot — Structured Query Service
Provides intent-based querying of the structured database tables to augment the context.
"""

import re
from typing import Optional, List
from sqlalchemy.orm import Session
from models.database import (
    Faculty, Department, Program, TuitionFee, PaymentPlan,
    Scholarship, AcademicCalendar, AcademicRegulation, GradingSystem,
    Staff, Course, FAQ
)

class StructuredQueryService:
    def __init__(self, db: Session):
        self.db = db
        
        # Keyword mapping for intent detection (expanded with Sudanese dialect)
        self.intent_keywords = {
            'faculties': ['كلية', 'كليات', 'faculty', 'faculties', 'college', 'قسم', 'أقسام', 'اقسام', 'departments', 'department', 'برنامج', 'برامج', 'تخصص', 'تخصصات', 'program', 'هندسة', 'طب', 'حاسوب', 'علوم'],
            'fees': ['رسوم', 'fees', 'دولار', 'تكلفة', 'سعر', 'مصاريف', 'أقساط', 'تقسيط', 'cost', 'tuition', 'price', 'payment', 'كم', 'بكم', 'فلوس', 'دفع', 'قسط', 'مبلغ'],
            'calendar': ['تقويم', 'امتحان', 'امتحانات', 'فصل دراسي', 'calendar', 'exam', 'semester', 'تسجيل', 'registration', 'متى', 'when', 'موعد', 'مواعيد', 'فترة', 'بداية', 'نهاية', 'اجازة', 'إجازة', 'عطلة'],
            'regulations': ['غياب', 'حضور', 'حرمان', 'إنذار', 'انذار', 'لائحة', 'لوائح', 'attendance', 'absence', 'regulation', 'warning', 'قانون', 'نظام', 'ساعات', 'حد أدنى', 'حد ادنى', 'شروط'],
            'scholarships': ['منح', 'منحة', 'خصم', 'إعفاء', 'اعفاء', 'scholarship', 'discount', 'grant', 'مجاني', 'تخفيض'],
            'courses': ['مقرر', 'مقررات', 'مادة', 'مواد', 'ساعات معتمدة', 'course', 'courses', 'credit', 'subject', 'محاضرة', 'محاضرات'],
            'staff': ['دكتور', 'أستاذ', 'استاذ', 'بروفيسور', 'مدرس', 'doctor', 'professor', 'staff', 'teacher', 'عميد', 'رئيس قسم', 'معيد'],
            'grading': ['درجات', 'درجة', 'تقدير', 'معدل', 'نتيجة', 'نتائج', 'grade', 'gpa', 'result', 'امتياز', 'جيد', 'مقبول', 'راسب', 'ناجح', 'نجاح', 'رسوب'],
            'admission': ['قبول', 'admission', 'تقديم', 'apply', 'شروط القبول', 'requirements', 'مستندات', 'وثائق', 'شهادة ثانوية', 'ثانوي', 'نسبة', 'معدل القبول'],
            'services': ['خدمة', 'خدمات', 'service', 'services', 'مكتبة', 'library', 'سكن', 'نقل', 'مواصلات', 'كافتيريا', 'مختبر', 'معمل'],
        }

    def detect_and_query(self, question: str) -> Optional[str]:
        """Main entry: detect intent and return structured data as formatted string."""
        question_lower = question.lower()
        
        # Try FAQ first (fastest)
        faq_result = self._query_faqs(question_lower)
        if faq_result:
            return faq_result
            
        # Detect intent and query appropriate table
        intents = self._detect_intents(question_lower)
        results = []
        
        for intent in intents:
            if intent == 'faculties': results.append(self._query_faculties(question_lower))
            elif intent == 'fees': results.append(self._query_fees(question_lower))
            elif intent == 'calendar': results.append(self._query_calendar(question_lower))
            elif intent == 'regulations': results.append(self._query_regulations(question_lower))
            elif intent == 'scholarships': results.append(self._query_scholarships())
            elif intent == 'courses': results.append(self._query_courses(question_lower))
            elif intent == 'staff': results.append(self._query_staff(question_lower))
            elif intent == 'grading': results.append(self._query_grading())
            elif intent == 'admission': results.append(self._query_faculties(question_lower))
            elif intent == 'services': results.append(self._query_services(question_lower))
            
        combined = '\n\n'.join(filter(None, results))
        return combined if combined else None

    def _detect_intents(self, question: str) -> List[str]:
        """Return list of detected intents based on keywords."""
        detected = []
        for intent, keywords in self.intent_keywords.items():
            if any(kw in question for kw in keywords):
                detected.append(intent)
        return detected

    def _query_faqs(self, question: str) -> Optional[str]:
        """Search FAQs for matching questions."""
        # A simple keyword match against active FAQs
        faqs = self.db.query(FAQ).filter(FAQ.is_active == True).all()
        matches = []
        
        words = set(re.findall(r'\w+', question))
        
        for faq in faqs:
            q_ar = (faq.question_ar or "").lower()
            q_en = (faq.question_en or "").lower()
            
            # If any significant word matches
            if any(w in q_ar or w in q_en for w in words if len(w) > 3):
                matches.append(faq)
                
        if not matches:
            return None
            
        result = "[الأسئلة الشائعة | FAQs]\n"
        for faq in matches[:3]: # limit to top 3
            result += f"س: {faq.question_ar} | Q: {faq.question_en}\n"
            result += f"ج: {faq.answer_ar} | A: {faq.answer_en}\n\n"
        return result

    def _query_fees(self, question: str) -> str:
        """Query tuition_fees + payment_plans tables."""
        fees = self.db.query(TuitionFee).filter(TuitionFee.is_active == True).all()
        plans = self.db.query(PaymentPlan).all()
        
        result = "[الرسوم الدراسية | Tuition Fees]\n"
        for fee in fees:
            fac_name = fee.faculty.name_ar if fee.faculty else "عام"
            result += f"- {fac_name}: {fee.description_ar} ({fee.description_en}) - {fee.amount} {fee.currency}\n"
            
        if plans:
            result += "\n[خطط الدفع | Payment Plans]\n"
            for p in plans:
                result += f"- القسط {p.installment_number}: {p.percentage}% - {p.notes_ar}\n"
                
        return result

    def _query_calendar(self, question: str) -> str:
        """Query academic_calendar table."""
        events = self.db.query(AcademicCalendar).all()
        if not events: return ""
        
        result = "[التقويم الأكاديمي | Academic Calendar]\n"
        for ev in events:
            dates = ev.start_date
            if ev.end_date: dates += f" to {ev.end_date}"
            result += f"- {ev.event_name_ar} ({ev.event_name_en}): {dates}\n"
        return result

    def _query_regulations(self, question: str) -> str:
        """Query academic_regulations table."""
        regs = self.db.query(AcademicRegulation).filter(AcademicRegulation.is_active == True).all()
        if not regs: return ""
        
        result = "[اللوائح الأكاديمية | Academic Regulations]\n"
        for r in regs:
            result += f"- {r.rule_title_ar}: {r.rule_content_ar}\n"
            if r.penalty_ar:
                result += f"  العقوبة: {r.penalty_ar}\n"
        return result

    def _query_scholarships(self) -> str:
        """Query scholarships table."""
        schols = self.db.query(Scholarship).filter(Scholarship.is_active == True).all()
        if not schols: return ""
        
        result = "[المنح الدراسية | Scholarships]\n"
        for s in schols:
            result += f"- {s.name_ar} ({s.discount_percentage}%): {s.eligibility_ar}\n"
        return result

    def _query_courses(self, question: str) -> str:
        """Query courses table."""
        courses = self.db.query(Course).filter(Course.is_active == True).limit(20).all()
        if not courses: return ""
        
        result = "[المقررات | Courses]\n"
        for c in courses:
            result += f"- {c.course_code}: {c.name_ar} ({c.credit_hours} ساعات)\n"
        return result

    def _query_staff(self, question: str) -> str:
        """Query staff table."""
        staff_members = self.db.query(Staff).filter(Staff.is_active == True).limit(20).all()
        if not staff_members: return ""
        
        result = "[هيئة التدريس | Staff]\n"
        for s in staff_members:
            result += f"- {s.title_ar} {s.name_ar} - {s.position_ar}\n"
        return result

    def _query_grading(self) -> str:
        """Query grading_system table."""
        grades = self.db.query(GradingSystem).all()
        if not grades: return ""
        
        result = "[نظام الدرجات | Grading System]\n"
        for g in grades:
            status = "نجاح" if g.is_passing else "رسوب"
            result += f"- {g.grade_letter} ({g.percentage_min}-{g.percentage_max}%): {g.grade_points} نقاط - {g.description_ar} ({status})\n"
        return result

    def _query_faculties(self, question: str) -> str:
        """Query faculties, departments, and programs."""
        from models.database import StudentService
        faculties = self.db.query(Faculty).all()
        if not faculties: return ""
        
        result = "[الكليات والأقسام | Faculties & Departments]\n"
        for f in faculties:
            result += f"\n🏛️ {f.name_ar} ({f.name_en}) - رمز: {f.code}\n"
            if f.email:
                result += f"  البريد: {f.email}\n"
            # Get departments
            deps = self.db.query(Department).filter(Department.faculty_id == f.id).all()
            for d in deps:
                result += f"  - قسم: {d.name_ar} ({d.name_en})\n"
            # Get programs
            progs = self.db.query(Program).join(Department).filter(Department.faculty_id == f.id).all()
            for p in progs:
                result += f"  - برنامج: {p.name_ar} ({p.degree_type}) - {p.duration_years} سنوات\n"
        return result

    def _query_services(self, question: str) -> str:
        """Query student services."""
        from models.database import StudentService
        services = self.db.query(StudentService).filter(StudentService.is_active == True).all()
        if not services: return ""
        
        result = "[خدمات الطلاب | Student Services]\n"
        for s in services:
            result += f"- {s.name_ar} ({s.name_en})"
            if hasattr(s, 'description_ar') and s.description_ar:
                result += f": {s.description_ar}"
            result += "\n"
        return result
