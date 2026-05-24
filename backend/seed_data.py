"""
UST Smart Chatbot — Seed Data
Populates the structured SQLite database with sample data.
"""

import logging
from datetime import datetime
from sqlalchemy.orm import Session
from models.database import (
    init_db, SessionLocal,
    Faculty, Department, Program, TuitionFee, PaymentPlan,
    Scholarship, AcademicCalendar, AcademicRegulation, GradingSystem,
    Staff, Course, StudentService, FAQ, Announcement
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SeedData")

def seed_database():
    init_db()
    db = SessionLocal()
    
    try:
        # 1. Faculties
        if db.query(Faculty).count() == 0:
            logger.info("Seeding Faculties...")
            med = Faculty(name_ar="كلية الطب", name_en="Faculty of Medicine", code="MED", established_year=1998, email="medicine@ust.edu.sd")
            eng = Faculty(name_ar="كلية الهندسة", name_en="Faculty of Engineering", code="ENG", established_year=1995, email="engineering@ust.edu.sd")
            cs = Faculty(name_ar="كلية علوم الحاسوب", name_en="Faculty of Computer Science", code="CS", established_year=2000, email="cs@ust.edu.sd")
            db.add_all([med, eng, cs])
            db.commit()
            
            # 2. Departments
            logger.info("Seeding Departments...")
            # Med deps
            med_gen = Department(faculty_id=med.id, name_ar="الطب البشري", name_en="General Medicine")
            # Eng deps
            eng_se = Department(faculty_id=eng.id, name_ar="هندسة البرمجيات", name_en="Software Engineering")
            eng_ce = Department(faculty_id=eng.id, name_ar="الهندسة المدنية", name_en="Civil Engineering")
            eng_bme = Department(faculty_id=eng.id, name_ar="الهندسة الطبية الحيوية", name_en="Biomedical Engineering")
            eng_cs = Department(faculty_id=eng.id, name_ar="نظم الاتصالات", name_en="Communications Systems")
            eng_arch = Department(faculty_id=eng.id, name_ar="العمارة", name_en="Architecture")
            eng_chem = Department(faculty_id=eng.id, name_ar="الهندسة الكيميائية", name_en="Chemical Engineering")
            eng_ecs = Department(faculty_id=eng.id, name_ar="النظم الإلكترونية والحاسوبية", name_en="Electronic & Computer Systems")
            # CS deps
            cs_cs = Department(faculty_id=cs.id, name_ar="علوم الحاسوب", name_en="Computer Science")
            cs_it = Department(faculty_id=cs.id, name_ar="تقنية المعلومات", name_en="Information Technology")
            db.add_all([med_gen, eng_se, eng_ce, eng_bme, eng_cs, eng_arch, eng_chem, eng_ecs, cs_cs, cs_it])
            db.commit()
            
            # 3. Programs
            logger.info("Seeding Programs...")
            programs = [
                Program(department_id=med_gen.id, name_ar="بكالوريوس الطب والجراحة", name_en="Bachelor of Medicine and Surgery", degree_type="honours_bachelor", duration_years=5),
                Program(department_id=eng_se.id, name_ar="بكالوريوس هندسة البرمجيات", name_en="Bachelor of Software Engineering", degree_type="honours_bachelor", duration_years=5),
                Program(department_id=eng_ce.id, name_ar="بكالوريوس الهندسة المدنية", name_en="Bachelor of Civil Engineering", degree_type="honours_bachelor", duration_years=5),
                Program(department_id=eng_bme.id, name_ar="بكالوريوس الهندسة الطبية الحيوية", name_en="Bachelor of Biomedical Engineering", degree_type="honours_bachelor", duration_years=5),
                Program(department_id=eng_cs.id, name_ar="بكالوريوس نظم الاتصالات", name_en="Bachelor of Communications Systems", degree_type="honours_bachelor", duration_years=5),
                Program(department_id=eng_arch.id, name_ar="بكالوريوس العمارة", name_en="Bachelor of Architecture", degree_type="honours_bachelor", duration_years=5),
                Program(department_id=eng_chem.id, name_ar="بكالوريوس الهندسة الكيميائية", name_en="Bachelor of Chemical Engineering", degree_type="honours_bachelor", duration_years=5),
                Program(department_id=eng_ecs.id, name_ar="بكالوريوس النظم الإلكترونية والحاسوبية", name_en="Bachelor of Electronic & Computer Systems", degree_type="honours_bachelor", duration_years=5),
                Program(department_id=cs_cs.id, name_ar="بكالوريوس علوم الحاسوب (شرف)", name_en="Bachelor of Computer Science (Honours)", degree_type="honours_bachelor", duration_years=5),
                Program(department_id=cs_cs.id, name_ar="بكالوريوس علوم الحاسوب (عام)", name_en="Bachelor of Computer Science (General)", degree_type="general_bachelor", duration_years=4),
                Program(department_id=cs_it.id, name_ar="بكالوريوس تقنية المعلومات (شرف)", name_en="Bachelor of Information Technology (Honours)", degree_type="honours_bachelor", duration_years=5),
                Program(department_id=cs_it.id, name_ar="بكالوريوس تقنية المعلومات (عام)", name_en="Bachelor of Information Technology (General)", degree_type="general_bachelor", duration_years=4),
            ]
            db.add_all(programs)
            db.commit()

            # 4. Tuition Fees
            logger.info("Seeding Tuition Fees...")
            fees = [
                TuitionFee(faculty_id=med.id, academic_year="2025-2026", fee_type="registration", amount=500, currency="USD", description_ar="رسوم تسجيل", description_en="Registration fee"),
                TuitionFee(faculty_id=med.id, academic_year="2025-2026", study_year=1, fee_type="annual", amount=3000, currency="USD", description_ar="رسوم السنة الأولى", description_en="Year 1 annual fee"),
                TuitionFee(faculty_id=med.id, academic_year="2025-2026", study_year=2, fee_type="annual", amount=2500, currency="USD", description_ar="رسوم السنة الثانية فما بعد", description_en="Year 2+ annual fee"),
                TuitionFee(faculty_id=med.id, academic_year="2025-2026", fee_type="lab", amount=200, currency="USD", description_ar="رسوم المعمل", description_en="Lab fee"),
                
                TuitionFee(faculty_id=eng.id, academic_year="2025-2026", fee_type="registration", amount=300, currency="USD", description_ar="رسوم تسجيل", description_en="Registration fee"),
                TuitionFee(faculty_id=eng.id, academic_year="2025-2026", study_year=1, fee_type="annual", amount=1800, currency="USD", description_ar="رسوم السنة الأولى", description_en="Year 1 annual fee"),
                TuitionFee(faculty_id=eng.id, academic_year="2025-2026", study_year=2, fee_type="annual", amount=1500, currency="USD", description_ar="رسوم السنة الثانية فما بعد", description_en="Year 2+ annual fee"),
                
                TuitionFee(faculty_id=cs.id, academic_year="2025-2026", fee_type="registration", amount=250, currency="USD", description_ar="رسوم تسجيل", description_en="Registration fee"),
                TuitionFee(faculty_id=cs.id, academic_year="2025-2026", fee_type="annual", amount=1200, currency="USD", description_ar="رسوم سنوية", description_en="Annual fee"),
            ]
            db.add_all(fees)
            db.commit()

            # 5. Payment Plans
            logger.info("Seeding Payment Plans...")
            plans = [
                PaymentPlan(academic_year="2025-2026", installment_number=1, percentage=40, notes_ar="القسط الأول بداية الفصل الأول", notes_en="Installment 1 due at semester 1 start"),
                PaymentPlan(academic_year="2025-2026", installment_number=2, percentage=35, notes_ar="القسط الثاني منتصف الفصل الأول", notes_en="Installment 2 mid semester 1"),
                PaymentPlan(academic_year="2025-2026", installment_number=3, percentage=25, notes_ar="القسط الثالث بداية الفصل الثاني", notes_en="Installment 3 semester 2 start"),
            ]
            db.add_all(plans)
            db.commit()

        if db.query(Scholarship).count() == 0:
            logger.info("Seeding Scholarships...")
            scholarships = [
                Scholarship(name_ar="منحة التفوق", name_en="Excellence Scholarship", type="excellence", discount_percentage=25, eligibility_ar="معدل 85% فأكثر", eligibility_en="Requires 85%+ GPA"),
                Scholarship(name_ar="منحة أبناء الموظفين", name_en="Staff Family Scholarship", type="staff_family", discount_percentage=50, eligibility_ar="أبناء موظفي الجامعة", eligibility_en="For university staff children"),
                Scholarship(name_ar="منحة أبناء الشهداء", name_en="Martyrs' Children Scholarship", type="need_based", discount_percentage=100, eligibility_ar="أبناء الشهداء مع تقديم الوثائق", eligibility_en="Exemption with documentation"),
            ]
            db.add_all(scholarships)
            db.commit()

        if db.query(AcademicCalendar).count() == 0:
            logger.info("Seeding Academic Calendar...")
            calendar = [
                AcademicCalendar(academic_year="2025-2026", semester="first", event_type="registration_start", event_name_ar="بداية التسجيل", event_name_en="Registration start", start_date="2025-08-15"),
                AcademicCalendar(academic_year="2025-2026", semester="first", event_type="registration_end", event_name_ar="نهاية التسجيل", event_name_en="Registration end", start_date="2025-09-10"),
                AcademicCalendar(academic_year="2025-2026", semester="first", event_type="semester_start", event_name_ar="بداية الدراسة", event_name_en="Semester start", start_date="2025-09-15"),
                AcademicCalendar(academic_year="2025-2026", semester="first", event_type="midterm_start", event_name_ar="امتحانات منتصف الفصل", event_name_en="Midterm exams", start_date="2025-11-10", end_date="2025-11-20"),
                AcademicCalendar(academic_year="2025-2026", semester="first", event_type="semester_end", event_name_ar="نهاية الدراسة", event_name_en="Semester end", start_date="2026-01-05"),
                AcademicCalendar(academic_year="2025-2026", semester="first", event_type="final_start", event_name_ar="امتحانات نهاية الفصل", event_name_en="Final exams", start_date="2026-01-10", end_date="2026-01-30"),
                
                AcademicCalendar(academic_year="2025-2026", semester="second", event_type="semester_start", event_name_ar="بداية الدراسة", event_name_en="Semester start", start_date="2026-02-10"),
                AcademicCalendar(academic_year="2025-2026", semester="second", event_type="midterm_start", event_name_ar="امتحانات منتصف الفصل", event_name_en="Midterm exams", start_date="2026-04-05", end_date="2026-04-15"),
                AcademicCalendar(academic_year="2025-2026", semester="second", event_type="semester_end", event_name_ar="نهاية الدراسة", event_name_en="Semester end", start_date="2026-06-05"),
                AcademicCalendar(academic_year="2025-2026", semester="second", event_type="final_start", event_name_ar="امتحانات نهاية الفصل", event_name_en="Final exams", start_date="2026-06-10", end_date="2026-06-30"),
            ]
            db.add_all(calendar)
            db.commit()

        if db.query(AcademicRegulation).count() == 0:
            logger.info("Seeding Academic Regulations...")
            regulations = [
                AcademicRegulation(category="attendance", rule_title_ar="الحضور الواجب", rule_title_en="Required Attendance", rule_content_ar="75% من المحاضرات كحد أدنى", rule_content_en="75% minimum attendance"),
                AcademicRegulation(category="attendance", rule_title_ar="إنذار أول", rule_title_en="First Warning", rule_content_ar="عند غياب أكثر من 15%", rule_content_en=">15% absence"),
                AcademicRegulation(category="attendance", rule_title_ar="إنذار ثانٍ", rule_title_en="Second Warning", rule_content_ar="عند غياب أكثر من 20%", rule_content_en=">20% absence"),
                AcademicRegulation(category="attendance", rule_title_ar="الحرمان من الامتحان", rule_title_en="Exam Ban", rule_content_ar="عند غياب أكثر من 25%", rule_content_en=">25% absence"),
                AcademicRegulation(category="examination", rule_title_ar="البطاقة الجامعية", rule_title_en="University ID", rule_content_ar="يجب على الطلاب حمل البطاقة الجامعية", rule_content_en="Students must carry university ID"),
                AcademicRegulation(category="examination", rule_title_ar="الأجهزة الإلكترونية", rule_title_en="Electronic Devices", rule_content_ar="يمنع إدخال الأجهزة الإلكترونية", rule_content_en="No electronic devices allowed"),
                AcademicRegulation(category="disciplinary", rule_title_ar="الغش", rule_title_en="Cheating", rule_content_ar="الغش يؤدي للرسوب المباشر", rule_content_en="Cheating results in automatic failure", penalty_ar="رسوب", penalty_en="Failure"),
            ]
            db.add_all(regulations)
            db.commit()

        if db.query(GradingSystem).count() == 0:
            logger.info("Seeding Grading System...")
            grades = [
                GradingSystem(grade_letter="A+", grade_points=4.0, percentage_min=95, percentage_max=100, description_ar="ممتاز بامتياز", description_en="Excellent with Distinction", is_passing=True),
                GradingSystem(grade_letter="A", grade_points=4.0, percentage_min=90, percentage_max=94, description_ar="ممتاز", description_en="Excellent", is_passing=True),
                GradingSystem(grade_letter="B+", grade_points=3.5, percentage_min=85, percentage_max=89, description_ar="جيد جداً بامتياز", description_en="Very Good with Distinction", is_passing=True),
                GradingSystem(grade_letter="B", grade_points=3.0, percentage_min=80, percentage_max=84, description_ar="جيد جداً", description_en="Very Good", is_passing=True),
                GradingSystem(grade_letter="C+", grade_points=2.5, percentage_min=75, percentage_max=79, description_ar="جيد بامتياز", description_en="Good with Distinction", is_passing=True),
                GradingSystem(grade_letter="C", grade_points=2.0, percentage_min=70, percentage_max=74, description_ar="جيد", description_en="Good", is_passing=True),
                GradingSystem(grade_letter="D+", grade_points=1.5, percentage_min=65, percentage_max=69, description_ar="مقبول بامتياز", description_en="Acceptable with Distinction", is_passing=True),
                GradingSystem(grade_letter="D", grade_points=1.0, percentage_min=60, percentage_max=64, description_ar="مقبول", description_en="Acceptable", is_passing=True),
                GradingSystem(grade_letter="F", grade_points=0.0, percentage_min=0, percentage_max=59, description_ar="راسب", description_en="Fail", is_passing=False),
            ]
            db.add_all(grades)
            db.commit()

        if db.query(FAQ).count() == 0:
            logger.info("Seeding FAQs...")
            faqs = [
                FAQ(category="fees", question_ar="كم رسوم الدراسة في كلية الهندسة؟", question_en="How much are the tuition fees for the Faculty of Engineering?", answer_ar="رسوم السنة الأولى 1800 دولار، والسنوات التالية 1500 دولار، مع إمكانية التقسيط على 3 أقساط.", answer_en="1800 USD first year, 1500 USD after, installments available.", is_featured=True),
                FAQ(category="fees", question_ar="هل يمكن تقسيط الرسوم؟", question_en="Can tuition fees be paid in installments?", answer_ar="نعم، تتيح الجامعة نظام الأقساط (3 أقساط خلال العام الدراسي). يجب الاتفاق مع إدارة الشؤون المالية عند التسجيل.", answer_en="Yes, the university offers an installment system (3 installments during the academic year). You must agree with the Financial Affairs Department upon registration.", is_featured=True),
                FAQ(category="academic", question_ar="كم نسبة الحضور المطلوبة؟", question_en="What is the required attendance percentage?", answer_ar="يجب الحضور 75% على الأقل من المحاضرات. من يتجاوز 25% غياباً يُحرم من الامتحان النهائي.", answer_en="You must attend at least 75% of the lectures. Anyone exceeding 25% absence is banned from the final exam.", is_featured=True),
                FAQ(category="academic", question_ar="ماذا يحدث لو تغيبت كثيراً؟", question_en="What happens if I am frequently absent?", answer_ar="تصلك إنذارات تدريجية. عند الوصول لـ 25% غياب يُحرم الطالب من امتحان المادة ويُعتبر راسباً فيها.", answer_en="You will receive progressive warnings. Reaching 25% absence bans the student from the course exam and they are considered to have failed it.", is_featured=False),
                FAQ(category="exams", question_ar="متى امتحانات الفصل الأول 2025-2026؟", question_en="When are the first semester exams for 2025-2026?", answer_ar="امتحانات نهاية الفصل الأول ستكون من 10 يناير حتى 30 يناير 2026.", answer_en="First semester final exams will be from January 10 to January 30, 2026.", is_featured=True),
                FAQ(category="exams", question_ar="ماذا لو رسبت في مادة؟", question_en="What if I fail a course?", answer_ar="يمكنك إعادة المادة في الفصل التالي أو في امتحانات الدور الثاني إن وُجد. الدرجة الجديدة تحل محل القديمة في حساب المعدل.", answer_en="You can retake the course in the following semester or in the second round exams if available. The new grade replaces the old one in GPA calculation.", is_featured=False),
                FAQ(category="admission", question_ar="ما الحد الأدنى للقبول؟", question_en="What is the minimum admission requirement?", answer_ar="يختلف حسب الكلية. الطب يتطلب معدلاً أعلى من الكليات الأخرى. يجب أولاً الحصول على موافقة المجلس القومي للتعليم العالي.", answer_en="It varies by faculty. Medicine requires a higher GPA than other faculties. Approval from the National Council for Higher Education is required first.", is_featured=True),
                FAQ(category="admission", question_ar="كيف أتقدم للجامعة؟", question_en="How do I apply to the university?", answer_ar="من خلال بوابة التسجيل الإلكترونية: reg.ust.edu.sd", answer_en="Through the online registration portal: reg.ust.edu.sd", is_featured=True),
            ]
            db.add_all(faqs)
            db.commit()

        if db.query(StudentService).count() == 0:
            logger.info("Seeding Student Services...")
            services = [
                StudentService(service_name_ar="المكتبة", service_name_en="Library", service_type="library"),
                StudentService(service_name_ar="المركز الصحي", service_name_en="Health Center", service_type="health"),
                StudentService(service_name_ar="المرافق الرياضية", service_name_en="Sports Facilities", service_type="sports"),
                StudentService(service_name_ar="سكن الطلاب", service_name_en="Student Housing", service_type="housing"),
                StudentService(service_name_ar="الكافتيريا", service_name_en="Cafeteria", service_type="cafeteria"),
            ]
            db.add_all(services)
            db.commit()

        if db.query(Announcement).count() == 0:
            logger.info("Seeding Announcements...")
            announcements = [
                Announcement(title_ar="الترحيب بالطلاب الجدد 2025-2026", title_en="Welcome new students 2025-2026", type="announcement", target_audience="new_students"),
                Announcement(title_ar="فترة التسجيل مفتوحة", title_en="Registration period open", type="news", target_audience="all"),
            ]
            db.add_all(announcements)
            db.commit()
            
        logger.info("Database seeding completed successfully.")

    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
