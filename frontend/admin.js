/**
 * UST Chatbot Admin Panel JavaScript
 * Configuration-driven SPA architecture.
 */

// ══════════════════════════════════════════════════════
// Configuration
// ══════════════════════════════════════════════════════

const SECTIONS = {
    knowledge: {
        title: 'قاعدة المعرفة',
        endpoint: '/api/admin/knowledge',
        columns: [
            { key: 'title_ar', label: 'العنوان' },
            { key: 'category_ar', label: 'الفئة' },
            { key: 'is_active', label: 'الحالة', type: 'badge' }
        ],
        fields: [
            { key: 'category_ar', label: 'الفئة (عربي)', type: 'text', required: true },
            { key: 'category_en', label: 'Category (EN)', type: 'text' },
            { key: 'title_ar', label: 'العنوان (عربي)', type: 'text', required: true },
            { key: 'title_en', label: 'Title (EN)', type: 'text' },
            { key: 'content_ar', label: 'المحتوى (عربي)', type: 'textarea', required: true },
            { key: 'content_en', label: 'Content (EN)', type: 'textarea' },
            { key: 'keywords', label: 'الكلمات المفتاحية', type: 'text', hint: 'مفصولة بفاصلة' }
        ],
        hasToggle: true
    },
    faculties: {
        title: 'الكليات',
        endpoint: '/api/admin/faculties',
        columns: [
            { key: 'code', label: 'الرمز' },
            { key: 'name_ar', label: 'الاسم' },
            { key: 'dean_name_ar', label: 'العميد' },
            { key: 'is_active', label: 'الحالة', type: 'badge' }
        ],
        fields: [
            { key: 'name_ar', label: 'الاسم (عربي)', type: 'text', required: true },
            { key: 'name_en', label: 'Name (EN)', type: 'text' },
            { key: 'code', label: 'الرمز', type: 'text', required: true },
            { key: 'dean_name_ar', label: 'اسم العميد (عربي)', type: 'text' },
            { key: 'dean_name_en', label: 'Dean Name (EN)', type: 'text' },
            { key: 'email', label: 'البريد الإلكتروني', type: 'text' },
            { key: 'website', label: 'الموقع الإلكتروني', type: 'text' },
            { key: 'phone', label: 'الهاتف', type: 'text' },
            { key: 'established_year', label: 'سنة التأسيس', type: 'number' },
            { key: 'description_ar', label: 'الوصف (عربي)', type: 'textarea' },
            { key: 'description_en', label: 'Description (EN)', type: 'textarea' }
        ],
        hasToggle: true
    },
    departments: {
        title: 'الأقسام',
        endpoint: '/api/admin/departments',
        columns: [
            { key: 'name_ar', label: 'الاسم' },
            { key: 'head_name_ar', label: 'رئيس القسم' },
            { key: 'is_active', label: 'الحالة', type: 'badge' }
        ],
        fields: [
            { key: 'faculty_id', label: 'الكلية', type: 'select', source: '/api/admin/faculties', sourceLabel: 'name_ar', required: true },
            { key: 'name_ar', label: 'الاسم (عربي)', type: 'text', required: true },
            { key: 'name_en', label: 'Name (EN)', type: 'text' },
            { key: 'head_name_ar', label: 'رئيس القسم (عربي)', type: 'text' },
            { key: 'head_name_en', label: 'Head Name (EN)', type: 'text' },
            { key: 'email', label: 'البريد الإلكتروني', type: 'text' },
            { key: 'description_ar', label: 'الوصف (عربي)', type: 'textarea' },
            { key: 'description_en', label: 'Description (EN)', type: 'textarea' }
        ],
        hasToggle: true
    },
    programs: {
        title: 'البرامج الدراسية',
        endpoint: '/api/admin/programs',
        columns: [
            { key: 'name_ar', label: 'الاسم' },
            { key: 'degree_type', label: 'الدرجة' },
            { key: 'duration_years', label: 'المدة (سنوات)' },
            { key: 'is_active', label: 'الحالة', type: 'badge' }
        ],
        fields: [
            { key: 'department_id', label: 'القسم', type: 'select', source: '/api/admin/departments', sourceLabel: 'name_ar', required: true },
            { key: 'name_ar', label: 'الاسم (عربي)', type: 'text', required: true },
            { key: 'name_en', label: 'Name (EN)', type: 'text' },
            { key: 'degree_type', label: 'نوع الدرجة', type: 'select', options: [
                {value: 'honours_bachelor', label: 'بكالوريوس شرف'},
                {value: 'general_bachelor', label: 'بكالوريوس عام'},
                {value: 'diploma', label: 'دبلوم'},
                {value: 'masters', label: 'ماجستير'},
                {value: 'phd', label: 'دكتوراه'}
            ], required: true },
            { key: 'duration_years', label: 'المدة بالسنوات', type: 'number', required: true },
            { key: 'total_credit_hours', label: 'الساعات المعتمدة', type: 'number' },
            { key: 'description_ar', label: 'الوصف (عربي)', type: 'textarea' },
            { key: 'description_en', label: 'Description (EN)', type: 'textarea' }
        ],
        hasToggle: true
    },
    courses: {
        title: 'المقررات',
        endpoint: '/api/admin/courses',
        columns: [
            { key: 'course_code', label: 'الرمز' },
            { key: 'name_ar', label: 'الاسم' },
            { key: 'credit_hours', label: 'الساعات' },
            { key: 'is_active', label: 'الحالة', type: 'badge' }
        ],
        fields: [
            { key: 'department_id', label: 'القسم', type: 'select', source: '/api/admin/departments', sourceLabel: 'name_ar', required: true },
            { key: 'program_id', label: 'البرنامج', type: 'select', source: '/api/admin/programs', sourceLabel: 'name_ar' },
            { key: 'course_code', label: 'رمز المقرر', type: 'text', required: true },
            { key: 'name_ar', label: 'الاسم (عربي)', type: 'text', required: true },
            { key: 'name_en', label: 'Name (EN)', type: 'text' },
            { key: 'credit_hours', label: 'الساعات المعتمدة', type: 'number', required: true },
            { key: 'course_type', label: 'نوع المقرر', type: 'select', options: [
                {value: 'core', label: 'إجباري'}, {value: 'elective', label: 'اختياري'}, {value: 'university_requirement', label: 'مطلوب جامعة'}
            ] },
            { key: 'study_year', label: 'سنة الدراسة', type: 'number' },
            { key: 'semester', label: 'الفصل الدراسي', type: 'select', options: [{value: 'first', label: 'الأول'}, {value: 'second', label: 'الثاني'}, {value: 'both', label: 'الكل'}] },
            { key: 'description_ar', label: 'الوصف (عربي)', type: 'textarea' },
            { key: 'description_en', label: 'Description (EN)', type: 'textarea' }
        ],
        hasToggle: true
    },
    fees: {
        title: 'الرسوم الدراسية',
        endpoint: '/api/admin/fees',
        columns: [
            { key: 'academic_year', label: 'العام الأكاديمي' },
            { key: 'description_ar', label: 'الوصف' },
            { key: 'amount', label: 'المبلغ' },
            { key: 'currency', label: 'العملة' },
            { key: 'is_active', label: 'الحالة', type: 'badge' }
        ],
        fields: [
            { key: 'faculty_id', label: 'الكلية', type: 'select', source: '/api/admin/faculties', sourceLabel: 'name_ar' },
            { key: 'program_id', label: 'البرنامج (اختياري)', type: 'select', source: '/api/admin/programs', sourceLabel: 'name_ar' },
            { key: 'academic_year', label: 'العام الأكاديمي', type: 'text', required: true },
            { key: 'study_year', label: 'سنة الدراسة (مثال: 1)', type: 'number' },
            { key: 'fee_type', label: 'نوع الرسوم', type: 'select', options: [
                {value: 'registration', label: 'تسجيل'}, {value: 'semester', label: 'فصل دراسي'}, {value: 'annual', label: 'سنوي'}, {value: 'lab', label: 'معمل'}
            ], required: true },
            { key: 'amount', label: 'المبلغ', type: 'number', required: true },
            { key: 'currency', label: 'العملة', type: 'select', options: [{value: 'SDG', label: 'جنيه سوداني'}, {value: 'USD', label: 'دولار أمريكي'}], required: true },
            { key: 'description_ar', label: 'الوصف (عربي)', type: 'text', required: true },
            { key: 'description_en', label: 'Description (EN)', type: 'text' }
        ],
        hasToggle: true
    },
    'payment-plans': {
        title: 'خطط الدفع',
        endpoint: '/api/admin/payment-plans',
        columns: [
            { key: 'academic_year', label: 'العام الأكاديمي' },
            { key: 'installment_number', label: 'رقم القسط' },
            { key: 'percentage', label: 'النسبة (%)' },
            { key: 'notes_ar', label: 'ملاحظات' }
        ],
        fields: [
            { key: 'faculty_id', label: 'الكلية (اختياري)', type: 'select', source: '/api/admin/faculties', sourceLabel: 'name_ar' },
            { key: 'academic_year', label: 'العام الأكاديمي', type: 'text', required: true },
            { key: 'installment_number', label: 'رقم القسط', type: 'number', required: true },
            { key: 'due_date', label: 'تاريخ الاستحقاق', type: 'text' },
            { key: 'percentage', label: 'النسبة المئوية', type: 'number' },
            { key: 'amount', label: 'المبلغ', type: 'number' },
            { key: 'notes_ar', label: 'ملاحظات (عربي)', type: 'text' },
            { key: 'notes_en', label: 'Notes (EN)', type: 'text' }
        ],
        hasToggle: false
    },
    scholarships: {
        title: 'المنح الدراسية',
        endpoint: '/api/admin/scholarships',
        columns: [
            { key: 'name_ar', label: 'الاسم' },
            { key: 'type', label: 'النوع' },
            { key: 'discount_percentage', label: 'الخصم (%)' },
            { key: 'is_active', label: 'الحالة', type: 'badge' }
        ],
        fields: [
            { key: 'name_ar', label: 'الاسم (عربي)', type: 'text', required: true },
            { key: 'name_en', label: 'Name (EN)', type: 'text' },
            { key: 'type', label: 'النوع', type: 'select', options: [
                {value: 'excellence', label: 'تفوق'}, {value: 'need_based', label: 'حاجة مادية'}, {value: 'staff_family', label: 'أبناء عاملين'}
            ], required: true },
            { key: 'discount_percentage', label: 'نسبة الخصم (%)', type: 'number', required: true },
            { key: 'eligibility_ar', label: 'الشروط (عربي)', type: 'textarea' },
            { key: 'eligibility_en', label: 'Eligibility (EN)', type: 'textarea' },
            { key: 'application_process_ar', label: 'طريقة التقديم (عربي)', type: 'textarea' },
            { key: 'application_process_en', label: 'Process (EN)', type: 'textarea' },
            { key: 'deadline', label: 'آخر موعد', type: 'text' }
        ],
        hasToggle: true
    },
    calendar: {
        title: 'التقويم الأكاديمي',
        endpoint: '/api/admin/calendar',
        columns: [
            { key: 'academic_year', label: 'العام الأكاديمي' },
            { key: 'semester', label: 'الفصل الدراسي' },
            { key: 'event_name_ar', label: 'الحدث' },
            { key: 'start_date', label: 'التاريخ' }
        ],
        fields: [
            { key: 'academic_year', label: 'العام الأكاديمي', type: 'text', required: true },
            { key: 'semester', label: 'الفصل الدراسي', type: 'select', options: [
                {value: 'first', label: 'الأول'}, {value: 'second', label: 'الثاني'}, {value: 'summer', label: 'الصيفي'}
            ], required: true },
            { key: 'event_type', label: 'نوع الحدث', type: 'text' },
            { key: 'event_name_ar', label: 'الحدث (عربي)', type: 'text', required: true },
            { key: 'event_name_en', label: 'Event (EN)', type: 'text' },
            { key: 'start_date', label: 'تاريخ البداية (YYYY-MM-DD)', type: 'text', required: true },
            { key: 'end_date', label: 'تاريخ النهاية', type: 'text' },
            { key: 'notes_ar', label: 'ملاحظات (عربي)', type: 'textarea' },
            { key: 'notes_en', label: 'Notes (EN)', type: 'textarea' }
        ],
        hasToggle: false
    },
    regulations: {
        title: 'اللوائح الأكاديمية',
        endpoint: '/api/admin/regulations',
        columns: [
            { key: 'category', label: 'الفئة' },
            { key: 'rule_title_ar', label: 'اللائحة' },
            { key: 'is_active', label: 'الحالة', type: 'badge' }
        ],
        fields: [
            { key: 'category', label: 'الفئة', type: 'select', options: [
                {value: 'attendance', label: 'الحضور'}, {value: 'grading', label: 'التقييم'}, {value: 'disciplinary', label: 'انضباط'}, {value: 'examination', label: 'امتحانات'}
            ], required: true },
            { key: 'rule_title_ar', label: 'عنوان اللائحة (عربي)', type: 'text', required: true },
            { key: 'rule_title_en', label: 'Title (EN)', type: 'text' },
            { key: 'rule_content_ar', label: 'المحتوى (عربي)', type: 'textarea', required: true },
            { key: 'rule_content_en', label: 'Content (EN)', type: 'textarea' },
            { key: 'penalty_ar', label: 'العقوبة (عربي)', type: 'text' },
            { key: 'penalty_en', label: 'Penalty (EN)', type: 'text' }
        ],
        hasToggle: true
    },
    grading: {
        title: 'نظام الدرجات',
        endpoint: '/api/admin/grading',
        columns: [
            { key: 'grade_letter', label: 'التقدير' },
            { key: 'grade_points', label: 'النقاط' },
            { key: 'percentage_min', label: 'من (%)' },
            { key: 'percentage_max', label: 'إلى (%)' },
            { key: 'is_passing', label: 'نجاح؟', type: 'badge' }
        ],
        fields: [
            { key: 'grade_letter', label: 'رمز التقدير (مثال A+)', type: 'text', required: true },
            { key: 'grade_points', label: 'النقاط (مثال 4.0)', type: 'number', required: true },
            { key: 'percentage_min', label: 'النسبة الدنيا', type: 'number', required: true },
            { key: 'percentage_max', label: 'النسبة العليا', type: 'number', required: true },
            { key: 'description_ar', label: 'الوصف (عربي)', type: 'text' },
            { key: 'description_en', label: 'Description (EN)', type: 'text' },
            { key: 'is_passing', label: 'يعتبر نجاح؟', type: 'checkbox' }
        ],
        hasToggle: false
    },
    staff: {
        title: 'هيئة التدريس والموظفين',
        endpoint: '/api/admin/staff',
        columns: [
            { key: 'name_ar', label: 'الاسم' },
            { key: 'title_ar', label: 'اللقب' },
            { key: 'position_ar', label: 'المنصب' },
            { key: 'is_active', label: 'الحالة', type: 'badge' }
        ],
        fields: [
            { key: 'faculty_id', label: 'الكلية', type: 'select', source: '/api/admin/faculties', sourceLabel: 'name_ar' },
            { key: 'department_id', label: 'القسم', type: 'select', source: '/api/admin/departments', sourceLabel: 'name_ar' },
            { key: 'title_ar', label: 'اللقب (عربي - دكتور، أستاذ..)', type: 'text' },
            { key: 'title_en', label: 'Title (EN)', type: 'text' },
            { key: 'name_ar', label: 'الاسم (عربي)', type: 'text', required: true },
            { key: 'name_en', label: 'Name (EN)', type: 'text' },
            { key: 'position_ar', label: 'المنصب (عربي)', type: 'text' },
            { key: 'position_en', label: 'Position (EN)', type: 'text' },
            { key: 'email', label: 'البريد الإلكتروني', type: 'text' },
            { key: 'office_hours_ar', label: 'الساعات المكتبية', type: 'text' },
            { key: 'specialization_ar', label: 'التخصص (عربي)', type: 'text' },
            { key: 'specialization_en', label: 'Specialization (EN)', type: 'text' }
        ],
        hasToggle: true
    },
    services: {
        title: 'خدمات الطلاب',
        endpoint: '/api/admin/services',
        columns: [
            { key: 'service_name_ar', label: 'اسم الخدمة' },
            { key: 'service_type', label: 'النوع' },
            { key: 'is_active', label: 'الحالة', type: 'badge' }
        ],
        fields: [
            { key: 'service_name_ar', label: 'الاسم (عربي)', type: 'text', required: true },
            { key: 'service_name_en', label: 'Name (EN)', type: 'text' },
            { key: 'service_type', label: 'نوع الخدمة', type: 'select', options: [
                {value: 'library', label: 'مكتبة'}, {value: 'health', label: 'صحة'}, {value: 'sports', label: 'رياضة'}, {value: 'housing', label: 'سكن'}, {value: 'cafeteria', label: 'كافتيريا'}
            ], required: true },
            { key: 'description_ar', label: 'الوصف (عربي)', type: 'textarea' },
            { key: 'description_en', label: 'Description (EN)', type: 'textarea' },
            { key: 'availability_ar', label: 'أوقات العمل', type: 'text' },
            { key: 'location', label: 'الموقع', type: 'text' },
            { key: 'contact', label: 'للتواصل', type: 'text' }
        ],
        hasToggle: true
    },
    faqs: {
        title: 'الأسئلة الشائعة',
        endpoint: '/api/admin/faqs',
        columns: [
            { key: 'question_ar', label: 'السؤال' },
            { key: 'category', label: 'الفئة' },
            { key: 'is_active', label: 'الحالة', type: 'badge' }
        ],
        fields: [
            { key: 'category', label: 'الفئة', type: 'select', options: [
                {value: 'admission', label: 'قبول'}, {value: 'fees', label: 'رسوم'}, {value: 'academic', label: 'أكاديمي'}, {value: 'exams', label: 'امتحانات'}, {value: 'general', label: 'عام'}
            ], required: true },
            { key: 'question_ar', label: 'السؤال (عربي)', type: 'text', required: true },
            { key: 'question_en', label: 'Question (EN)', type: 'text' },
            { key: 'answer_ar', label: 'الإجابة (عربي)', type: 'textarea', required: true },
            { key: 'answer_en', label: 'Answer (EN)', type: 'textarea' },
            { key: 'is_featured', label: 'سؤال مميز؟', type: 'checkbox' }
        ],
        hasToggle: true
    },
    announcements: {
        title: 'الإعلانات',
        endpoint: '/api/admin/announcements',
        columns: [
            { key: 'title_ar', label: 'العنوان' },
            { key: 'type', label: 'النوع' },
            { key: 'is_active', label: 'الحالة', type: 'badge' }
        ],
        fields: [
            { key: 'type', label: 'النوع', type: 'select', options: [
                {value: 'news', label: 'أخبار'}, {value: 'announcement', label: 'إعلان'}, {value: 'urgent', label: 'عاجل'}, {value: 'event', label: 'فعالية'}
            ], required: true },
            { key: 'target_audience', label: 'الجمهور', type: 'select', options: [
                {value: 'all', label: 'الكل'}, {value: 'students', label: 'الطلاب'}, {value: 'new_students', label: 'الطلاب الجدد'}, {value: 'staff', label: 'الموظفين'}
            ], required: true },
            { key: 'title_ar', label: 'العنوان (عربي)', type: 'text', required: true },
            { key: 'title_en', label: 'Title (EN)', type: 'text' },
            { key: 'content_ar', label: 'المحتوى (عربي)', type: 'textarea', required: true },
            { key: 'content_en', label: 'Content (EN)', type: 'textarea' },
            { key: 'publish_date', label: 'تاريخ النشر', type: 'text' },
            { key: 'expiry_date', label: 'تاريخ الانتهاء', type: 'text' }
        ],
        hasToggle: true
    }
};

// ══════════════════════════════════════════════════════
// Global State & Initialization
// ══════════════════════════════════════════════════════

let currentSection = '';
let currentItemId = null;
let currentConfig = null;
let cachedData = {}; // Cache for select field sources

const originalFetch = window.fetch;
window.fetch = async function(resource, config) {
    if (typeof resource === 'string' && resource.startsWith('/api/admin')) {
        config = config || {};
        config.headers = config.headers || {};
        const token = localStorage.getItem('ust_admin_token');
        if (resource !== '/api/admin/login' && token) {
            config.headers['Authorization'] = `Bearer ${token}`;
        }
    }
    const response = await originalFetch(resource, config);
    if (response.status === 401 && resource !== '/api/admin/login') {
        logout();
    } else if (response.status === 403) {
        showToast('ليس لديك الصلاحيات الكافية للقيام بهذا الإجراء', 'error');
    }
    return response;
};

let currentUserRole = null;

function parseJwt(token) {
    try {
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
            return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
        }).join(''));
        return JSON.parse(jsonPayload);
    } catch(e) {
        return null;
    }
}

function checkAuth() {
    const token = localStorage.getItem('ust_admin_token');
    const loginScreen = document.getElementById('loginScreen');
    const appContainer = document.getElementById('appContainer');
    if (!token) {
        if (loginScreen) loginScreen.style.display = 'flex';
        if (appContainer) appContainer.style.display = 'none';
        currentUserRole = null;
        return false;
    }
    
    const payload = parseJwt(token);
    if (payload && payload.role) {
        currentUserRole = payload.role;
    }
    
    if (loginScreen) loginScreen.style.display = 'none';
    if (appContainer) appContainer.style.display = 'flex';
    return true;
}

function logout() {
    localStorage.removeItem('ust_admin_token');
    checkAuth();
}

document.addEventListener('DOMContentLoaded', () => {
    
    // Login form handler
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const user = document.getElementById('loginUsername').value;
            const pass = document.getElementById('loginPassword').value;
            const btn = e.target.querySelector('button');
            const err = document.getElementById('loginError');
            
            btn.textContent = 'جاري التحقق...';
            btn.disabled = true;
            err.style.display = 'none';
            
            try {
                const res = await originalFetch('/api/admin/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username: user, password: pass })
                });
                
                if (res.ok) {
                    const data = await res.json();
                    localStorage.setItem('ust_admin_token', data.token);
                    document.getElementById('loginPassword').value = '';
                    checkAuth();
                    const hash = window.location.hash.substring(1) || 'dashboard';
                    navigateTo(hash);
                } else {
                    err.style.display = 'block';
                }
            } catch (error) {
                err.style.display = 'block';
                err.textContent = 'خطأ في الاتصال بالخادم';
            } finally {
                btn.textContent = 'دخول';
                btn.disabled = false;
            }
        });
    }

    // Initial auth check and state setup
    const isAuthenticated = checkAuth();

    // Sidebar active state (only navigate if authenticated initially)
    if (isAuthenticated) {
        const hash = window.location.hash.substring(1) || 'dashboard';
        navigateTo(hash);
    }

    // Navigation listener
    window.addEventListener('hashchange', () => {
        if (!checkAuth()) return;
        const h = window.location.hash.substring(1);
        if (h) navigateTo(h);
    });

    // Mobile menu
    document.getElementById('menuToggle').addEventListener('click', () => {
        document.getElementById('sidebar').classList.toggle('active');
    });
    
    // Logout listener
    const logoutBtn = document.createElement('button');
    logoutBtn.className = 'btn btn-outline';
    logoutBtn.textContent = 'تسجيل الخروج';
    logoutBtn.style.marginRight = '10px';
    logoutBtn.onclick = logout;
    document.querySelector('.topbar-right').appendChild(logoutBtn);
});

// ══════════════════════════════════════════════════════
// Navigation
// ══════════════════════════════════════════════════════

function navigateTo(sectionKey) {
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    const link = document.querySelector(`.nav-item[data-section="${sectionKey}"]`);
    if (link) link.classList.add('active');

    currentSection = sectionKey;
    
    // Close sidebar on mobile
    document.getElementById('sidebar').classList.remove('active');

    const contentArea = document.getElementById('mainContent');
    contentArea.innerHTML = '<div class="loading">جاري التحميل...</div>';

    if (sectionKey === 'dashboard') {
        renderDashboard();
    } else if (sectionKey === 'documents') {
        renderDocuments();
    } else if (sectionKey === 'conversations') {
        renderConversations();
    } else if (sectionKey === 'feedback') {
        renderFeedback();
    } else if (sectionKey === 'system') {
        renderSystem();
    } else if (SECTIONS[sectionKey]) {
        currentConfig = SECTIONS[sectionKey];
        renderCrudSection();
    } else {
        contentArea.innerHTML = '<h2>القسم غير موجود</h2>';
    }
}

// ══════════════════════════════════════════════════════
// Toast & Modals
// ══════════════════════════════════════════════════════

function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    let icon = '✅';
    if (type === 'error') icon = '❌';
    else if (type === 'warning') icon = '⚠️';
    
    toast.innerHTML = `<span class="toast-icon">${icon}</span> <span class="toast-text">${message}</span>`;
    container.appendChild(toast);
    
    setTimeout(() => {
        if (container.contains(toast)) container.removeChild(toast);
    }, 3500);
}

function openModal(title) {
    document.getElementById('modalTitle').textContent = title;
    document.getElementById('modalOverlay').classList.add('active');
}

function closeModal() {
    document.getElementById('modalOverlay').classList.remove('active');
    setTimeout(() => { document.getElementById('modalBody').innerHTML = ''; }, 300);
}

let confirmAction = null;
function confirmDelete(id) {
    document.getElementById('confirmText').textContent = 'هل أنت متأكد من حذف هذا العنصر نهائياً؟';
    document.getElementById('confirmOverlay').classList.add('active');
    confirmAction = () => { deleteItem(id); closeConfirm(); };
    document.getElementById('confirmBtn').onclick = confirmAction;
}

function closeConfirm() {
    document.getElementById('confirmOverlay').classList.remove('active');
}

// ══════════════════════════════════════════════════════
// Dashboard
// ══════════════════════════════════════════════════════

async function renderDashboard() {
    const content = document.getElementById('mainContent');
    
    try {
        const res = await fetch('/api/admin/dashboard-stats');
        const data = await res.json();
        
        let html = `
            <div class="section-header">
                <h2>لوحة التحكم</h2>
                <div>
                    <button class="btn btn-outline" onclick="loadKnowledgeBase()">📥 تحميل البيانات الأساسية</button>
                    ${currentUserRole === 'super_admin' ? `<button class="btn btn-primary" onclick="exportAndRebuild()">🔄 تحديث الفهرس</button>` : ''}
                </div>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-info"><h3>قاعدة المعرفة</h3><p>${data.stats.knowledge_entries}</p></div>
                    <div class="stat-icon">📚</div>
                </div>
                <div class="stat-card">
                    <div class="stat-info"><h3>الكليات</h3><p>${data.stats.faculties}</p></div>
                    <div class="stat-icon">🏛️</div>
                </div>
                <div class="stat-card">
                    <div class="stat-info"><h3>المقررات</h3><p>${data.stats.courses}</p></div>
                    <div class="stat-icon">📔</div>
                </div>
                <div class="stat-card">
                    <div class="stat-info"><h3>المحادثات</h3><p>${data.stats.conversations}</p></div>
                    <div class="stat-icon">💬</div>
                </div>
            </div>
            
            <div class="charts-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-top: 20px; margin-bottom: 20px;">
                <div class="chart-container" style="background: var(--bg-panel); padding: 20px; border-radius: 8px; border: 1px solid var(--border-color); height: 300px; display: flex; flex-direction: column;">
                    <h3 style="margin-bottom: 10px; font-size: 1rem;">المحادثات (آخر 7 أيام)</h3>
                    <div style="flex-grow: 1; position: relative;">
                        <canvas id="conversationsChart"></canvas>
                    </div>
                </div>
                <div class="chart-container" style="background: var(--bg-panel); padding: 20px; border-radius: 8px; border: 1px solid var(--border-color); height: 300px; display: flex; flex-direction: column;">
                    <h3 style="margin-bottom: 10px; font-size: 1rem;">توزيع التقييمات</h3>
                    <div style="flex-grow: 1; position: relative;">
                        <canvas id="feedbackChart"></canvas>
                    </div>
                </div>
            </div>

            <div class="table-container">
                <div class="table-header-bar">
                    <h3>أحدث النشاطات</h3>
                </div>
                <div class="table-responsive">
                    <table>
                        <thead>
                            <tr>
                                <th>الإجراء</th>
                                <th>النوع</th>
                                <th>الرقم</th>
                                <th>التاريخ</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.recent_activity.map(log => `
                                <tr>
                                    <td><span class="badge ${log.action === 'create' ? 'badge-success' : log.action === 'delete' ? 'badge-error' : 'badge-warning'}">${log.action}</span></td>
                                    <td>${log.entity_type}</td>
                                    <td>${log.entity_id || '-'}</td>
                                    <td class="ltr-text">${new Date(log.timestamp).toLocaleString('ar-EG')}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
        content.innerHTML = html;
        
        // Fetch and render charts
        try {
            const chartsRes = await fetch('/api/admin/analytics/charts');
            const chartsData = await chartsRes.json();
            
            // Conversations Chart
            const ctxConv = document.getElementById('conversationsChart');
            if (ctxConv) {
                new Chart(ctxConv, {
                    type: 'line',
                    data: {
                        labels: chartsData.conversations_chart.labels,
                        datasets: [{
                            label: 'عدد المحادثات',
                            data: chartsData.conversations_chart.data,
                            borderColor: '#3b82f6',
                            backgroundColor: 'rgba(59, 130, 246, 0.1)',
                            borderWidth: 2,
                            fill: true,
                            tension: 0.4
                        }]
                    },
                    options: { responsive: true, maintainAspectRatio: false }
                });
            }
            
            // Feedback Chart
            const ctxFeed = document.getElementById('feedbackChart');
            if (ctxFeed) {
                new Chart(ctxFeed, {
                    type: 'doughnut',
                    data: {
                        labels: ['إيجابي', 'سلبي'],
                        datasets: [{
                            data: [chartsData.feedback_chart.positive, chartsData.feedback_chart.negative],
                            backgroundColor: ['#10b981', '#ef4444'],
                            borderWidth: 0
                        }]
                    },
                    options: { responsive: true, maintainAspectRatio: false }
                });
            }
        } catch (err) {
            console.error('Failed to load charts', err);
        }
        
    } catch (e) {
        content.innerHTML = '<h2>خطأ في تحميل البيانات</h2>';
        showToast('فشل تحميل بيانات لوحة التحكم', 'error');
    }
}

async function exportAndRebuild() {
    showToast('جاري التصدير وإعادة البناء... قد يستغرق هذا بضع دقائق', 'warning');
    try {
        const res = await fetch('/api/admin/export-and-rebuild', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            showToast(data.message);
        } else {
            showToast('حدث خطأ أثناء العملية', 'error');
        }
    } catch (e) {
        showToast('فشل الاتصال بالخادم', 'error');
    }
}

async function loadKnowledgeBase() {
    try {
        const res = await fetch('/api/admin/load-knowledge-base', { method: 'POST' });
        const data = await res.json();
        if (data.success) showToast(data.message);
    } catch (e) {
        showToast('فشل التحميل', 'error');
    }
}

// ══════════════════════════════════════════════════════
// Dynamic CRUD Generator
// ══════════════════════════════════════════════════════

async function renderCrudSection() {
    const content = document.getElementById('mainContent');
    content.innerHTML = `
        <div class="section-header">
            <h2>${currentConfig.title}</h2>
            <div style="display: flex; gap: 10px;">
                <button class="btn btn-outline" onclick="exportCurrentSection()">⬇️ تصدير Excel</button>
                <button class="btn btn-outline" onclick="document.getElementById('importFile').click()">⬆️ استيراد Excel</button>
                <input type="file" id="importFile" style="display:none" accept=".xlsx" onchange="importCurrentSection(event)">
                <button class="btn btn-primary" onclick="openCreateForm()">➕ إضافة جديد</button>
            </div>
        </div>
        <div class="table-container">
            <div class="table-responsive" id="tableContainer">
                <div style="padding:20px;">جاري تحميل البيانات...</div>
            </div>
        </div>
    `;
    
    await loadTableData();
}

async function loadTableData() {
    const container = document.getElementById('tableContainer');
    try {
        const res = await fetch(currentConfig.endpoint);
        const data = await res.json();
        
        if (data.items.length === 0) {
            container.innerHTML = '<div style="padding: 20px; text-align: center; color: var(--text-tertiary);">لا توجد بيانات. انقر على إضافة جديد.</div>';
            return;
        }
        
        let html = `<table><thead><tr>`;
        currentConfig.columns.forEach(col => {
            html += `<th>${col.label}</th>`;
        });
        html += `<th style="width: 120px;">الإجراءات</th></tr></thead><tbody>`;
        
        data.items.forEach(item => {
            html += `<tr>`;
            currentConfig.columns.forEach(col => {
                let val = item[col.key];
                if (col.type === 'badge') {
                    const badgeClass = val ? 'badge-success' : 'badge-error';
                    const text = val ? 'نشط' : 'غير نشط';
                    html += `<td><span class="badge ${badgeClass}">${text}</span></td>`;
                } else if (val === null || val === undefined) {
                    html += `<td>-</td>`;
                } else {
                    html += `<td>${val}</td>`;
                }
            });
            
            html += `<td>
                <button class="btn-icon edit" onclick='openEditForm(${JSON.stringify(item).replace(/'/g, "&#39;")})'>✏️</button>
                ${currentConfig.hasToggle ? `<button class="btn-icon toggle" onclick="toggleItem(${item.id})">🔄</button>` : ''}
                ${currentUserRole === 'super_admin' ? `<button class="btn-icon delete" onclick="confirmDelete(${item.id})">🗑️</button>` : ''}
            </td></tr>`;
        });
        
        html += `</tbody></table>`;
        container.innerHTML = html;
        
    } catch (e) {
        container.innerHTML = '<div style="padding: 20px; color: var(--error);">خطأ في جلب البيانات</div>';
    }
}

async function fetchSourceOptions(field) {
    if (cachedData[field.source]) return cachedData[field.source];
    try {
        const res = await fetch(field.source);
        const data = await res.json();
        const options = data.items.map(item => ({ value: item.id, label: item[field.sourceLabel] }));
        cachedData[field.source] = options;
        return options;
    } catch (e) {
        return [];
    }
}

async function renderFormFields(item = null) {
    const body = document.getElementById('modalBody');
    body.innerHTML = '<div class="loading">جاري تحضير النموذج...</div>';
    
    let html = '<div class="bilingual-grid">';
    
    for (const field of currentConfig.fields) {
        const value = item ? (item[field.key] !== null ? item[field.key] : '') : '';
        const required = field.required ? 'required' : '';
        const reqMark = field.required ? '<span style="color:red">*</span>' : '';
        
        html += `<div class="form-group">
            <label class="form-label">${field.label} ${reqMark}</label>`;
            
        if (field.type === 'textarea') {
            html += `<textarea class="form-control" id="field_${field.key}" ${required}>${value}</textarea>`;
        } else if (field.type === 'select') {
            html += `<select class="form-control" id="field_${field.key}" ${required}>
                <option value="">اختر...</option>`;
                
            let options = field.options;
            if (field.source) {
                options = await fetchSourceOptions(field);
            }
            
            if (options) {
                options.forEach(opt => {
                    const sel = (value == opt.value) ? 'selected' : '';
                    html += `<option value="${opt.value}" ${sel}>${opt.label}</option>`;
                });
            }
            html += `</select>`;
        } else if (field.type === 'checkbox') {
            const chk = value ? 'checked' : '';
            html += `<div class="checkbox-group">
                <input type="checkbox" id="field_${field.key}" ${chk}>
                <label for="field_${field.key}">نعم</label>
            </div>`;
        } else {
            html += `<input type="${field.type}" class="form-control" id="field_${field.key}" value="${value}" ${required}>`;
        }
        
        if (field.hint) html += `<div style="font-size:0.8rem; color:var(--text-tertiary); margin-top:5px;">${field.hint}</div>`;
        html += `</div>`;
    }
    
    html += '</div>';
    body.innerHTML = html;
}

function getFormData() {
    const data = {};
    for (const field of currentConfig.fields) {
        const el = document.getElementById(`field_${field.key}`);
        if (!el) continue;
        
        if (field.type === 'checkbox') {
            data[field.key] = el.checked;
        } else if (field.type === 'number') {
            data[field.key] = el.value ? Number(el.value) : null;
        } else {
            data[field.key] = el.value || null;
        }
    }
    return data;
}

async function openCreateForm() {
    currentItemId = null;
    openModal('إضافة جديد');
    await renderFormFields();
    document.getElementById('modalSaveBtn').onclick = saveItem;
}

async function openEditForm(item) {
    currentItemId = item.id;
    openModal('تعديل البيانات');
    await renderFormFields(item);
    document.getElementById('modalSaveBtn').onclick = saveItem;
}

async function saveItem() {
    // Validate required fields
    for (const field of currentConfig.fields) {
        if (field.required) {
            const el = document.getElementById(`field_${field.key}`);
            if (!el || !el.value) {
                showToast(`الرجاء إدخال الحقل المطلوب: ${field.label}`, 'error');
                return;
            }
        }
    }
    
    const data = getFormData();
    const isUpdate = currentItemId !== null;
    const url = isUpdate ? `${currentConfig.endpoint}/${currentItemId}` : currentConfig.endpoint;
    const method = isUpdate ? 'PUT' : 'POST';
    
    const btn = document.getElementById('modalSaveBtn');
    btn.textContent = 'جاري الحفظ...';
    btn.disabled = true;
    
    try {
        const res = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (res.ok) {
            showToast('تم حفظ البيانات بنجاح');
            closeModal();
            loadTableData();
        } else {
            showToast('حدث خطأ أثناء الحفظ', 'error');
        }
    } catch (e) {
        showToast('فشل الاتصال بالخادم', 'error');
    } finally {
        btn.textContent = 'حفظ';
        btn.disabled = false;
    }
}

async function deleteItem(id) {
    try {
        const res = await fetch(`${currentConfig.endpoint}/${id}`, { method: 'DELETE' });
        if (res.ok) {
            showToast('تم الحذف بنجاح');
            loadTableData();
        } else {
            showToast('حدث خطأ أثناء الحذف', 'error');
        }
    } catch (e) {
        showToast('فشل الاتصال بالخادم', 'error');
    }
}

async function toggleItem(id) {
    try {
        const res = await fetch(`${currentConfig.endpoint}/${id}/toggle`, { method: 'PATCH' });
        if (res.ok) {
            showToast('تم تغيير الحالة بنجاح');
            loadTableData();
        } else {
            showToast('حدث خطأ أثناء تغيير الحالة', 'error');
        }
    } catch (e) {
        showToast('فشل الاتصال بالخادم', 'error');
    }
}

// ══════════════════════════════════════════════════════
// Existing Specialized Sections
// ══════════════════════════════════════════════════════

async function renderDocuments() {
    const content = document.getElementById('mainContent');
    content.innerHTML = `
        <div class="section-header">
            <h2>الوثائق والملفات</h2>
            <button class="btn btn-outline" onclick="loadKnowledgeBase()">📥 تحميل Knowledge Base</button>
        </div>
        
        <div class="upload-zone" id="uploadZone">
            <div class="upload-icon">📄</div>
            <h3>اسحب الملفات هنا أو انقر للرفع</h3>
            <p>يدعم PDF, DOCX, TXT, JSON</p>
            <input type="file" id="fileInput" hidden accept=".pdf,.docx,.doc,.txt,.json">
        </div>
        
        <div class="table-container" style="margin-top: 30px;">
            <div class="table-header-bar">
                <h3>الملفات المرفوعة</h3>
            </div>
            <div class="table-responsive" id="docsTableContainer">
                <div style="padding:20px;">جاري التحميل...</div>
            </div>
        </div>
    `;
    
    // Upload logic
    const dropzone = document.getElementById('uploadZone');
    const input = document.getElementById('fileInput');
    
    dropzone.addEventListener('click', () => input.click());
    dropzone.addEventListener('dragover', (e) => { e.preventDefault(); dropzone.classList.add('dragover'); });
    dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
        if (e.dataTransfer.files.length) uploadFile(e.dataTransfer.files[0]);
    });
    input.addEventListener('change', () => {
        if (input.files.length) uploadFile(input.files[0]);
    });
    
    loadDocuments();
}

async function uploadFile(file) {
    showToast(`جاري رفع ${file.name}...`, 'warning');
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const res = await fetch('/api/admin/upload', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        
        if (res.ok) {
            showToast(data.message);
            loadDocuments();
        } else {
            showToast(data.detail || 'فشل الرفع', 'error');
        }
    } catch (e) {
        showToast('خطأ في الاتصال', 'error');
    }
}

async function loadDocuments() {
    const container = document.getElementById('docsTableContainer');
    try {
        const res = await fetch('/api/admin/documents');
        const data = await res.json();
        
        let html = `<table><thead><tr>
            <th>اسم الملف</th>
            <th>النوع</th>
            <th>عدد الأجزاء</th>
            <th>الحالة</th>
            <th>التاريخ</th>
            <th>حذف</th>
        </tr></thead><tbody>`;
        
        data.documents.forEach(doc => {
            html += `<tr>
                <td class="ltr-text">${doc.filename}</td>
                <td class="ltr-text">${doc.doc_type}</td>
                <td>${doc.chunk_count}</td>
                <td><span class="badge ${doc.status === 'processed' ? 'badge-success' : 'badge-warning'}">${doc.status}</span></td>
                <td class="ltr-text">${new Date(doc.added_at).toLocaleDateString()}</td>
                <td><button class="btn-icon delete" onclick="deleteDocument(${doc.id})">🗑️</button></td>
            </tr>`;
        });
        
        html += `</tbody></table>`;
        container.innerHTML = html;
    } catch (e) {
        container.innerHTML = '<div style="padding:20px;color:var(--error);">خطأ في تحميل الوثائق</div>';
    }
}

async function deleteDocument(id) {
    try {
        const res = await fetch(`/api/admin/documents/${id}`, { method: 'DELETE' });
        if (res.ok) {
            showToast('تم حذف الملف بنجاح');
            loadDocuments();
        }
    } catch (e) {
        showToast('خطأ في الحذف', 'error');
    }
}

async function renderConversations() {
    const content = document.getElementById('mainContent');
    content.innerHTML = `
        <div class="section-header"><h2>سجل المحادثات</h2></div>
        <div class="table-container">
            <div class="table-responsive" id="convTableContainer">
                <div style="padding:20px;">جاري التحميل...</div>
            </div>
        </div>
    `;
    
    try {
        const res = await fetch('/api/admin/conversations?limit=100');
        const data = await res.json();
        
        let html = `<table><thead><tr>
            <th>معرف المحادثة</th>
            <th>عدد الرسائل</th>
            <th>اللغة</th>
            <th>التاريخ</th>
        </tr></thead><tbody>`;
        
        data.conversations.forEach(c => {
            html += `<tr>
                <td class="ltr-text">${c.id.substring(0, 8)}...</td>
                <td>${c.message_count}</td>
                <td><span class="badge badge-neutral">${c.language.toUpperCase()}</span></td>
                <td class="ltr-text">${new Date(c.started_at).toLocaleString()}</td>
            </tr>`;
        });
        
        html += `</tbody></table>`;
        document.getElementById('convTableContainer').innerHTML = html;
    } catch (e) {
        document.getElementById('convTableContainer').innerHTML = '<div style="padding:20px;color:var(--error);">خطأ في التحميل</div>';
    }
}

async function renderSystem() {
    const content = document.getElementById('mainContent');
    content.innerHTML = '<div style="padding:20px;">جاري فحص النظام...</div>';
    
    try {
        const res = await fetch('/api/admin/system-status');
        const data = await res.json();
        
        const llmStatus = data.llm.status === "available" ? "badge-success" : "badge-error";
        
        content.innerHTML = `
            <div class="section-header"><h2>حالة النظام</h2></div>
            
            <div class="stats-grid">
                <div class="stat-card" style="grid-column: span 2;">
                    <div>
                        <h3 style="color:var(--text-secondary); margin-bottom:10px;">LLM (Ollama)</h3>
                        <p><span class="badge ${llmStatus}">${data.llm.status.toUpperCase()}</span></p>
                        <p style="margin-top:10px; color:var(--text-tertiary);" class="ltr-text">Model: ${data.llm.model}</p>
                    </div>
                </div>
                
                <div class="stat-card" style="grid-column: span 2;">
                    <div>
                        <h3 style="color:var(--text-secondary); margin-bottom:10px;">Vector Store (ChromaDB)</h3>
                        <p><span class="badge badge-success">ONLINE</span></p>
                        <p style="margin-top:10px; color:var(--text-tertiary);" class="ltr-text">Chunks: ${data.vector_store.total_chunks}</p>
                    </div>
                </div>
            </div>
        `;
    } catch (e) {
        content.innerHTML = '<div style="padding:20px;color:var(--error);">فشل الاتصال بالخادم</div>';
    }
}

async function renderFeedback() {
    const content = document.getElementById('mainContent');
    content.innerHTML = `
        <div class="section-header"><h2>مراجعة الإجابات الخاطئة</h2></div>
        <div class="table-container">
            <div class="table-responsive" id="feedbackTableContainer">
                <div style="padding:20px;">جاري التحميل...</div>
            </div>
        </div>
    `;
    
    try {
        const res = await fetch('/api/admin/analytics/feedback-review');
        const data = await res.json();
        
        if (!data.reviews || data.reviews.length === 0) {
            document.getElementById('feedbackTableContainer').innerHTML = '<div style="padding:20px;text-align:center;">لا توجد تقييمات سلبية لمراجعتها ✅</div>';
            return;
        }
        
        let html = `<table><thead><tr>
            <th>سؤال الطالب</th>
            <th>إجابة البوت</th>
            <th>تعليق الطالب</th>
            <th>التاريخ</th>
        </tr></thead><tbody>`;
        
        data.reviews.forEach(fb => {
            html += `<tr>
                <td style="max-width: 200px; white-space: normal;">${fb.user_question || '-'}</td>
                <td style="max-width: 300px; white-space: normal; color: var(--error);">${fb.bot_response || '-'}</td>
                <td>${fb.comment || '-'}</td>
                <td class="ltr-text">${new Date(fb.timestamp).toLocaleString('ar-EG')}</td>
            </tr>`;
        });
        
        html += `</tbody></table>`;
        document.getElementById('feedbackTableContainer').innerHTML = html;
    } catch (e) {
        document.getElementById('feedbackTableContainer').innerHTML = '<div style="padding:20px;color:var(--error);">خطأ في التحميل</div>';
    }
}

// ══════════════════════════════════════════════════════
// Export and Import Logic
// ══════════════════════════════════════════════════════

async function exportCurrentSection() {
    if (!currentSection || currentSection === 'dashboard' || currentSection === 'documents' || currentSection === 'conversations' || currentSection === 'system' || currentSection === 'feedback') {
        showToast('لا يمكن التصدير من هذا القسم', 'error');
        return;
    }
    
    const exportUrl = `/api/admin/export/${currentSection}`;
    showToast('جاري تحضير ملف التصدير...', 'warning');
    
    try {
        const res = await fetch(exportUrl);
        if (!res.ok) {
            showToast('حدث خطأ أثناء التصدير (تأكد من صلاحياتك)', 'error');
            return;
        }
        
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `export_${currentSection}_${new Date().toISOString().slice(0,10)}.xlsx`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
        
        showToast('تم تحميل الملف بنجاح', 'success');
    } catch (e) {
        showToast('فشل الاتصال بالخادم', 'error');
    }
}

async function importCurrentSection(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    if (!currentSection || currentSection === 'dashboard' || currentSection === 'documents' || currentSection === 'conversations' || currentSection === 'system' || currentSection === 'feedback') {
        showToast('لا يمكن الاستيراد إلى هذا القسم', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    showToast('جاري رفع واستيراد الملف...', 'warning');
    
    try {
        const res = await fetch(`/api/admin/import/${currentSection}`, {
            method: 'POST',
            body: formData,
            // Don't set Content-Type header here; fetch handles boundary automatically for FormData
        });
        
        const data = await res.json();
        if (res.ok && data.success) {
            showToast(data.message, 'success');
            renderCrudSection(); // reload table
        } else {
            showToast(data.detail || 'حدث خطأ أثناء الاستيراد', 'error');
        }
    } catch (err) {
        console.error('Import error', err);
        showToast('فشل الاتصال بالخادم', 'error');
    } finally {
        // Reset the file input
        event.target.value = '';
    }
}
