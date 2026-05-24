"""
UST Smart Chatbot — Admin API
Handles document management, knowledge base operations, CRUD for structured data, and system administration.
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io

from models.database import (
    get_db, Document, KnowledgeEntry, Faculty, Department, Program, TuitionFee, 
    PaymentPlan, Scholarship, AcademicCalendar, AcademicRegulation, GradingSystem,
    Staff, Course, StudentService, FAQ, Announcement, AuditLog, Conversation, Message
)
from models.schemas import DocumentOut, DocumentListResponse
from core.vector_store import get_vector_store
from services.document_processor import process_file, process_json_knowledge_base
from services.conversation_service import ConversationService
from config import KNOWLEDGE_BASE_DIR

from core.auth import verify_admin, require_super_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["Admin"], dependencies=[Depends(verify_admin)])

UPLOAD_DIR = KNOWLEDGE_BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ══════════════════════════════════════════════════════
# Helper Functions
# ══════════════════════════════════════════════════════

def serialize(obj):
    """Convert SQLAlchemy model to dictionary, formatting datetimes."""
    if not obj:
        return None
    data = {}
    for column in obj.__table__.columns:
        val = getattr(obj, column.name)
        if isinstance(val, datetime):
            data[column.name] = val.isoformat()
        else:
            data[column.name] = val
    return data

def log_audit(db: Session, entity_type: str, entity_id: int, action: str, changes: dict = None):
    """Log an admin operation to the audit log."""
    log = AuditLog(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        changes=changes,
        timestamp=datetime.utcnow()
    )
    db.add(log)
    db.commit()


# ══════════════════════════════════════════════════════
# Dashboard & Export
# ══════════════════════════════════════════════════════

@router.get('/dashboard-stats')
async def dashboard_stats(db: Session = Depends(get_db)):
    """Return counts for each entity type + recent audit log."""
    stats = {
        'knowledge_entries': db.query(KnowledgeEntry).count(),
        'faculties': db.query(Faculty).count(),
        'departments': db.query(Department).count(),
        'courses': db.query(Course).count(),
        'programs': db.query(Program).count(),
        'staff': db.query(Staff).count(),
        'faqs': db.query(FAQ).count(),
        'conversations': db.query(Conversation).count(),
        'documents': db.query(Document).count()
    }
    
    recent_logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(10).all()
    logs_data = [serialize(log) for log in recent_logs]
    
    return {'stats': stats, 'recent_activity': logs_data}

# ══════════════════════════════════════════════════════
# Import / Export
# ══════════════════════════════════════════════════════

RESOURCE_MODEL_MAP = {
    'knowledge': KnowledgeEntry,
    'faculties': Faculty,
    'departments': Department,
    'programs': Program,
    'courses': Course,
    'staff': Staff,
    'fees': TuitionFee,
    'payment-plans': PaymentPlan,
    'scholarships': Scholarship,
    'calendar': AcademicCalendar,
    'regulations': AcademicRegulation,
    'grading': GradingSystem,
    'services': StudentService,
    'faqs': FAQ,
    'announcements': Announcement
}

@router.get('/export/{resource}')
async def export_resource_excel(resource: str, db: Session = Depends(get_db)):
    import pandas as pd
    model = RESOURCE_MODEL_MAP.get(resource)
    if not model:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    items = db.query(model).all()
    data = [serialize(item) for item in items]
    
    df = pd.DataFrame(data)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name=resource)
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={resource}_export.xlsx"}
    )

@router.post('/import/{resource}')
async def import_resource_excel(resource: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    import pandas as pd
    model = RESOURCE_MODEL_MAP.get(resource)
    if not model:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        # Replace NaNs with None
        df = df.where(pd.notnull(df), None)
        
        records = df.to_dict('records')
        count = 0
        for rec in records:
            rec.pop('id', None)
            clean_rec = {k: v for k, v in rec.items() if hasattr(model, k)}
            item = model(**clean_rec)
            db.add(item)
            count += 1
            
        db.commit()
        log_audit(db, resource, 0, 'import', {'count': count})
        
        return {"success": True, "message": f"تم الاستيراد بنجاح: {count} صفوف (Successfully imported {count} records)."}
    except Exception as e:
        logger.error(f"Import error: {e}")
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to import file: {str(e)}")

@router.post('/export-and-rebuild')
async def export_and_rebuild(db: Session = Depends(get_db), current_user = Depends(require_super_admin)):
    """Call export_db_to_json() then rebuild vector index."""
    # This will be implemented in document_processor.py
    from services.document_processor import export_db_to_json
    
    try:
        chunks, metadatas, ids = export_db_to_json(db)
        
        vector_store = get_vector_store()
        vector_store.delete_by_source("ust_knowledge_base")
        if chunks:
            vector_store.add_documents(texts=chunks, metadatas=metadatas, ids=ids)
            
        return {
            "success": True,
            "chunks_exported": len(chunks),
            "message": f"تم التصدير وإعادة بناء الفهرس: {len(chunks)} جزء | Export and rebuild successful: {len(chunks)} chunks"
        }
    except Exception as e:
        logger.error(f"Export and rebuild error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ══════════════════════════════════════════════════════
# CRUD Endpoints Pattern Factory
# ══════════════════════════════════════════════════════

def create_crud_endpoints(router, path, model, entity_name, filters=None):
    @router.get(path)
    async def list_items(db: Session = Depends(get_db), **kwargs):
        query = db.query(model)
        if filters:
            for query_param, db_column in filters.items():
                val = kwargs.get(query_param)
                if val:
                    query = query.filter(getattr(model, db_column) == val)
        items = query.order_by(model.id.desc()).all()
        return {'items': [serialize(item) for item in items], 'total': len(items)}

    @router.post(path)
    async def create_item(data: dict = Body(...), db: Session = Depends(get_db)):
        item = model(**{k: v for k, v in data.items() if hasattr(model, k) and k != 'id'})
        db.add(item)
        db.commit()
        db.refresh(item)
        log_audit(db, entity_name, item.id, 'create', data)
        return {'success': True, 'id': item.id}

    @router.get(f"{path}/{{item_id}}")
    async def get_item(item_id: int, db: Session = Depends(get_db)):
        item = db.query(model).filter(model.id == item_id).first()
        if not item: 
            raise HTTPException(404, detail="Item not found")
        return serialize(item)

    @router.put(f"{path}/{{item_id}}")
    async def update_item(item_id: int, data: dict = Body(...), db: Session = Depends(get_db)):
        item = db.query(model).filter(model.id == item_id).first()
        if not item: 
            raise HTTPException(404, detail="Item not found")
        for k, v in data.items():
            if hasattr(item, k) and k != 'id': 
                setattr(item, k, v)
        db.commit()
        log_audit(db, entity_name, item.id, 'update', data)
        return {'success': True}

    @router.delete(f"{path}/{{item_id}}")
    async def delete_item(item_id: int, db: Session = Depends(get_db), current_user = Depends(require_super_admin)):
        item = db.query(model).filter(model.id == item_id).first()
        if not item: 
            raise HTTPException(404, detail="Item not found")
        db.delete(item)
        db.commit()
        log_audit(db, entity_name, item_id, 'delete')
        return {'success': True}

    # Add toggle endpoint if the model has 'is_active'
    if hasattr(model, 'is_active'):
        @router.patch(f"{path}/{{item_id}}/toggle")
        async def toggle_item(item_id: int, db: Session = Depends(get_db)):
            item = db.query(model).filter(model.id == item_id).first()
            if not item: 
                raise HTTPException(404, detail="Item not found")
            item.is_active = not item.is_active
            db.commit()
            log_audit(db, entity_name, item.id, 'toggle', {'is_active': item.is_active})
            return {'success': True, 'is_active': item.is_active}


# Define all 15 CRUD routes
# 1. Knowledge
@router.get('/knowledge')
async def list_knowledge(category: str = None, db: Session = Depends(get_db)):
    query = db.query(KnowledgeEntry)
    if category:
        query = query.filter(KnowledgeEntry.category_en == category)
    items = query.order_by(KnowledgeEntry.id.desc()).all()
    return {'items': [serialize(item) for item in items], 'total': len(items)}

@router.post('/knowledge')
async def create_knowledge(data: dict = Body(...), db: Session = Depends(get_db)):
    item = KnowledgeEntry(**{k: v for k, v in data.items() if hasattr(KnowledgeEntry, k)})
    db.add(item)
    db.commit()
    db.refresh(item)
    log_audit(db, 'knowledge_entry', item.id, 'create', data)
    return {'success': True, 'id': item.id}

@router.get('/knowledge/{item_id}')
async def get_knowledge(item_id: int, db: Session = Depends(get_db)):
    item = db.query(KnowledgeEntry).filter(KnowledgeEntry.id == item_id).first()
    if not item: raise HTTPException(404)
    return serialize(item)

@router.put('/knowledge/{item_id}')
async def update_knowledge(item_id: int, data: dict = Body(...), db: Session = Depends(get_db)):
    item = db.query(KnowledgeEntry).filter(KnowledgeEntry.id == item_id).first()
    if not item: raise HTTPException(404)
    for k, v in data.items():
        if hasattr(item, k) and k != 'id': setattr(item, k, v)
    db.commit()
    log_audit(db, 'knowledge_entry', item.id, 'update', data)
    return {'success': True}

@router.delete('/knowledge/{item_id}')
async def delete_knowledge(item_id: int, db: Session = Depends(get_db), current_user = Depends(require_super_admin)):
    item = db.query(KnowledgeEntry).filter(KnowledgeEntry.id == item_id).first()
    if not item: raise HTTPException(404)
    db.delete(item); db.commit()
    log_audit(db, 'knowledge_entry', item_id, 'delete')
    return {'success': True}

@router.patch('/knowledge/{item_id}/toggle')
async def toggle_knowledge(item_id: int, db: Session = Depends(get_db)):
    item = db.query(KnowledgeEntry).filter(KnowledgeEntry.id == item_id).first()
    if not item: raise HTTPException(404)
    item.is_active = not item.is_active; db.commit()
    log_audit(db, 'knowledge_entry', item.id, 'toggle', {'is_active': item.is_active})
    return {'success': True, 'is_active': item.is_active}


# For the other models, we can do it manually to ensure exact parameter signatures for FastAPI docs
# 2. Faculties
@router.get('/faculties')
async def list_faculties(db: Session = Depends(get_db)):
    items = db.query(Faculty).order_by(Faculty.id.desc()).all()
    return {'items': [serialize(item) for item in items], 'total': len(items)}

@router.post('/faculties')
async def create_faculty(data: dict = Body(...), db: Session = Depends(get_db)):
    item = Faculty(**{k: v for k, v in data.items() if hasattr(Faculty, k) and k != 'id'})
    db.add(item); db.commit(); db.refresh(item)
    log_audit(db, 'faculty', item.id, 'create', data)
    return {'success': True, 'id': item.id}

@router.get('/faculties/{item_id}')
async def get_faculty(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Faculty).filter(Faculty.id == item_id).first()
    if not item: raise HTTPException(404)
    return serialize(item)

@router.put('/faculties/{item_id}')
async def update_faculty(item_id: int, data: dict = Body(...), db: Session = Depends(get_db)):
    item = db.query(Faculty).filter(Faculty.id == item_id).first()
    if not item: raise HTTPException(404)
    for k, v in data.items():
        if hasattr(item, k) and k != 'id': setattr(item, k, v)
    db.commit()
    log_audit(db, 'faculty', item.id, 'update', data)
    return {'success': True}

@router.delete('/faculties/{item_id}')
async def delete_faculty(item_id: int, db: Session = Depends(get_db), current_user = Depends(require_super_admin)):
    item = db.query(Faculty).filter(Faculty.id == item_id).first()
    if not item: raise HTTPException(404)
    db.delete(item); db.commit()
    log_audit(db, 'faculty', item_id, 'delete')
    return {'success': True}

@router.patch('/faculties/{item_id}/toggle')
async def toggle_faculty(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Faculty).filter(Faculty.id == item_id).first()
    if not item: raise HTTPException(404)
    item.is_active = not item.is_active; db.commit()
    log_audit(db, 'faculty', item.id, 'toggle', {'is_active': item.is_active})
    return {'success': True, 'is_active': item.is_active}


# 3. Departments
@router.get('/departments')
async def list_departments(faculty_id: int = None, db: Session = Depends(get_db)):
    query = db.query(Department)
    if faculty_id is not None: query = query.filter(Department.faculty_id == faculty_id)
    items = query.order_by(Department.id.desc()).all()
    return {'items': [serialize(item) for item in items], 'total': len(items)}

@router.post('/departments')
async def create_department(data: dict = Body(...), db: Session = Depends(get_db)):
    item = Department(**{k: v for k, v in data.items() if hasattr(Department, k) and k != 'id'})
    db.add(item); db.commit(); db.refresh(item)
    log_audit(db, 'department', item.id, 'create', data)
    return {'success': True, 'id': item.id}

@router.get('/departments/{item_id}')
async def get_department(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Department).filter(Department.id == item_id).first()
    if not item: raise HTTPException(404)
    return serialize(item)

@router.put('/departments/{item_id}')
async def update_department(item_id: int, data: dict = Body(...), db: Session = Depends(get_db)):
    item = db.query(Department).filter(Department.id == item_id).first()
    if not item: raise HTTPException(404)
    for k, v in data.items():
        if hasattr(item, k) and k != 'id': setattr(item, k, v)
    db.commit()
    log_audit(db, 'department', item.id, 'update', data)
    return {'success': True}

@router.delete('/departments/{item_id}')
async def delete_department(item_id: int, db: Session = Depends(get_db), current_user = Depends(require_super_admin)):
    item = db.query(Department).filter(Department.id == item_id).first()
    if not item: raise HTTPException(404)
    db.delete(item); db.commit()
    log_audit(db, 'department', item_id, 'delete')
    return {'success': True}

@router.patch('/departments/{item_id}/toggle')
async def toggle_department(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Department).filter(Department.id == item_id).first()
    if not item: raise HTTPException(404)
    item.is_active = not item.is_active; db.commit()
    log_audit(db, 'department', item.id, 'toggle', {'is_active': item.is_active})
    return {'success': True, 'is_active': item.is_active}


# 4. Programs
@router.get('/programs')
async def list_programs(department_id: int = None, db: Session = Depends(get_db)):
    query = db.query(Program)
    if department_id is not None: query = query.filter(Program.department_id == department_id)
    items = query.order_by(Program.id.desc()).all()
    return {'items': [serialize(item) for item in items], 'total': len(items)}

@router.post('/programs')
async def create_program(data: dict = Body(...), db: Session = Depends(get_db)):
    item = Program(**{k: v for k, v in data.items() if hasattr(Program, k) and k != 'id'})
    db.add(item); db.commit(); db.refresh(item)
    log_audit(db, 'program', item.id, 'create', data)
    return {'success': True, 'id': item.id}

@router.get('/programs/{item_id}')
async def get_program(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Program).filter(Program.id == item_id).first()
    if not item: raise HTTPException(404)
    return serialize(item)

@router.put('/programs/{item_id}')
async def update_program(item_id: int, data: dict = Body(...), db: Session = Depends(get_db)):
    item = db.query(Program).filter(Program.id == item_id).first()
    if not item: raise HTTPException(404)
    for k, v in data.items():
        if hasattr(item, k) and k != 'id': setattr(item, k, v)
    db.commit()
    log_audit(db, 'program', item.id, 'update', data)
    return {'success': True}

@router.delete('/programs/{item_id}')
async def delete_program(item_id: int, db: Session = Depends(get_db), current_user = Depends(require_super_admin)):
    item = db.query(Program).filter(Program.id == item_id).first()
    if not item: raise HTTPException(404)
    db.delete(item); db.commit()
    log_audit(db, 'program', item_id, 'delete')
    return {'success': True}

@router.patch('/programs/{item_id}/toggle')
async def toggle_program(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Program).filter(Program.id == item_id).first()
    if not item: raise HTTPException(404)
    item.is_active = not item.is_active; db.commit()
    log_audit(db, 'program', item.id, 'toggle', {'is_active': item.is_active})
    return {'success': True, 'is_active': item.is_active}


# 5. Tuition Fees
@router.get('/fees')
async def list_fees(faculty_id: int = None, academic_year: str = None, db: Session = Depends(get_db)):
    query = db.query(TuitionFee)
    if faculty_id is not None: query = query.filter(TuitionFee.faculty_id == faculty_id)
    if academic_year is not None: query = query.filter(TuitionFee.academic_year == academic_year)
    items = query.order_by(TuitionFee.id.desc()).all()
    return {'items': [serialize(item) for item in items], 'total': len(items)}

@router.post('/fees')
async def create_fee(data: dict = Body(...), db: Session = Depends(get_db)):
    item = TuitionFee(**{k: v for k, v in data.items() if hasattr(TuitionFee, k) and k != 'id'})
    db.add(item); db.commit(); db.refresh(item)
    log_audit(db, 'tuition_fee', item.id, 'create', data)
    return {'success': True, 'id': item.id}

@router.get('/fees/{item_id}')
async def get_fee(item_id: int, db: Session = Depends(get_db)):
    item = db.query(TuitionFee).filter(TuitionFee.id == item_id).first()
    if not item: raise HTTPException(404)
    return serialize(item)

@router.put('/fees/{item_id}')
async def update_fee(item_id: int, data: dict = Body(...), db: Session = Depends(get_db)):
    item = db.query(TuitionFee).filter(TuitionFee.id == item_id).first()
    if not item: raise HTTPException(404)
    for k, v in data.items():
        if hasattr(item, k) and k != 'id': setattr(item, k, v)
    db.commit()
    log_audit(db, 'tuition_fee', item.id, 'update', data)
    return {'success': True}

@router.delete('/fees/{item_id}')
async def delete_fee(item_id: int, db: Session = Depends(get_db), current_user = Depends(require_super_admin)):
    item = db.query(TuitionFee).filter(TuitionFee.id == item_id).first()
    if not item: raise HTTPException(404)
    db.delete(item); db.commit()
    log_audit(db, 'tuition_fee', item_id, 'delete')
    return {'success': True}

@router.patch('/fees/{item_id}/toggle')
async def toggle_fee(item_id: int, db: Session = Depends(get_db)):
    item = db.query(TuitionFee).filter(TuitionFee.id == item_id).first()
    if not item: raise HTTPException(404)
    item.is_active = not item.is_active; db.commit()
    log_audit(db, 'tuition_fee', item.id, 'toggle', {'is_active': item.is_active})
    return {'success': True, 'is_active': item.is_active}


# 6. Payment Plans
@router.get('/payment-plans')
async def list_payment_plans(faculty_id: int = None, db: Session = Depends(get_db)):
    query = db.query(PaymentPlan)
    if faculty_id is not None: query = query.filter(PaymentPlan.faculty_id == faculty_id)
    items = query.order_by(PaymentPlan.id.desc()).all()
    return {'items': [serialize(item) for item in items], 'total': len(items)}

@router.post('/payment-plans')
async def create_payment_plan(data: dict = Body(...), db: Session = Depends(get_db)):
    item = PaymentPlan(**{k: v for k, v in data.items() if hasattr(PaymentPlan, k) and k != 'id'})
    db.add(item); db.commit(); db.refresh(item)
    log_audit(db, 'payment_plan', item.id, 'create', data)
    return {'success': True, 'id': item.id}

@router.get('/payment-plans/{item_id}')
async def get_payment_plan(item_id: int, db: Session = Depends(get_db)):
    item = db.query(PaymentPlan).filter(PaymentPlan.id == item_id).first()
    if not item: raise HTTPException(404)
    return serialize(item)

@router.put('/payment-plans/{item_id}')
async def update_payment_plan(item_id: int, data: dict = Body(...), db: Session = Depends(get_db)):
    item = db.query(PaymentPlan).filter(PaymentPlan.id == item_id).first()
    if not item: raise HTTPException(404)
    for k, v in data.items():
        if hasattr(item, k) and k != 'id': setattr(item, k, v)
    db.commit()
    log_audit(db, 'payment_plan', item.id, 'update', data)
    return {'success': True}

@router.delete('/payment-plans/{item_id}')
async def delete_payment_plan(item_id: int, db: Session = Depends(get_db), current_user = Depends(require_super_admin)):
    item = db.query(PaymentPlan).filter(PaymentPlan.id == item_id).first()
    if not item: raise HTTPException(404)
    db.delete(item); db.commit()
    log_audit(db, 'payment_plan', item_id, 'delete')
    return {'success': True}


# 7. Scholarships
@router.get('/scholarships')
async def list_scholarships(type: str = None, db: Session = Depends(get_db)):
    query = db.query(Scholarship)
    if type is not None: query = query.filter(Scholarship.type == type)
    items = query.order_by(Scholarship.id.desc()).all()
    return {'items': [serialize(item) for item in items], 'total': len(items)}

@router.post('/scholarships')
async def create_scholarship(data: dict = Body(...), db: Session = Depends(get_db)):
    item = Scholarship(**{k: v for k, v in data.items() if hasattr(Scholarship, k) and k != 'id'})
    db.add(item); db.commit(); db.refresh(item)
    log_audit(db, 'scholarship', item.id, 'create', data)
    return {'success': True, 'id': item.id}

@router.get('/scholarships/{item_id}')
async def get_scholarship(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Scholarship).filter(Scholarship.id == item_id).first()
    if not item: raise HTTPException(404)
    return serialize(item)

@router.put('/scholarships/{item_id}')
async def update_scholarship(item_id: int, data: dict = Body(...), db: Session = Depends(get_db)):
    item = db.query(Scholarship).filter(Scholarship.id == item_id).first()
    if not item: raise HTTPException(404)
    for k, v in data.items():
        if hasattr(item, k) and k != 'id': setattr(item, k, v)
    db.commit()
    log_audit(db, 'scholarship', item.id, 'update', data)
    return {'success': True}

@router.delete('/scholarships/{item_id}')
async def delete_scholarship(item_id: int, db: Session = Depends(get_db), current_user = Depends(require_super_admin)):
    item = db.query(Scholarship).filter(Scholarship.id == item_id).first()
    if not item: raise HTTPException(404)
    db.delete(item); db.commit()
    log_audit(db, 'scholarship', item_id, 'delete')
    return {'success': True}

@router.patch('/scholarships/{item_id}/toggle')
async def toggle_scholarship(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Scholarship).filter(Scholarship.id == item_id).first()
    if not item: raise HTTPException(404)
    item.is_active = not item.is_active; db.commit()
    log_audit(db, 'scholarship', item.id, 'toggle', {'is_active': item.is_active})
    return {'success': True, 'is_active': item.is_active}


# 8. Academic Calendar
@router.get('/calendar')
async def list_calendar(academic_year: str = None, semester: str = None, db: Session = Depends(get_db)):
    query = db.query(AcademicCalendar)
    if academic_year is not None: query = query.filter(AcademicCalendar.academic_year == academic_year)
    if semester is not None: query = query.filter(AcademicCalendar.semester == semester)
    items = query.order_by(AcademicCalendar.id.desc()).all()
    return {'items': [serialize(item) for item in items], 'total': len(items)}

@router.post('/calendar')
async def create_calendar(data: dict = Body(...), db: Session = Depends(get_db)):
    item = AcademicCalendar(**{k: v for k, v in data.items() if hasattr(AcademicCalendar, k) and k != 'id'})
    db.add(item); db.commit(); db.refresh(item)
    log_audit(db, 'academic_calendar', item.id, 'create', data)
    return {'success': True, 'id': item.id}

@router.get('/calendar/{item_id}')
async def get_calendar(item_id: int, db: Session = Depends(get_db)):
    item = db.query(AcademicCalendar).filter(AcademicCalendar.id == item_id).first()
    if not item: raise HTTPException(404)
    return serialize(item)

@router.put('/calendar/{item_id}')
async def update_calendar(item_id: int, data: dict = Body(...), db: Session = Depends(get_db)):
    item = db.query(AcademicCalendar).filter(AcademicCalendar.id == item_id).first()
    if not item: raise HTTPException(404)
    for k, v in data.items():
        if hasattr(item, k) and k != 'id': setattr(item, k, v)
    db.commit()
    log_audit(db, 'academic_calendar', item.id, 'update', data)
    return {'success': True}

@router.delete('/calendar/{item_id}')
async def delete_calendar(item_id: int, db: Session = Depends(get_db), current_user = Depends(require_super_admin)):
    item = db.query(AcademicCalendar).filter(AcademicCalendar.id == item_id).first()
    if not item: raise HTTPException(404)
    db.delete(item); db.commit()
    log_audit(db, 'academic_calendar', item_id, 'delete')
    return {'success': True}


# 9. Academic Regulations
@router.get('/regulations')
async def list_regulations(category: str = None, db: Session = Depends(get_db)):
    query = db.query(AcademicRegulation)
    if category is not None: query = query.filter(AcademicRegulation.category == category)
    items = query.order_by(AcademicRegulation.id.desc()).all()
    return {'items': [serialize(item) for item in items], 'total': len(items)}

@router.post('/regulations')
async def create_regulation(data: dict = Body(...), db: Session = Depends(get_db)):
    item = AcademicRegulation(**{k: v for k, v in data.items() if hasattr(AcademicRegulation, k) and k != 'id'})
    db.add(item); db.commit(); db.refresh(item)
    log_audit(db, 'academic_regulation', item.id, 'create', data)
    return {'success': True, 'id': item.id}

@router.get('/regulations/{item_id}')
async def get_regulation(item_id: int, db: Session = Depends(get_db)):
    item = db.query(AcademicRegulation).filter(AcademicRegulation.id == item_id).first()
    if not item: raise HTTPException(404)
    return serialize(item)

@router.put('/regulations/{item_id}')
async def update_regulation(item_id: int, data: dict = Body(...), db: Session = Depends(get_db)):
    item = db.query(AcademicRegulation).filter(AcademicRegulation.id == item_id).first()
    if not item: raise HTTPException(404)
    for k, v in data.items():
        if hasattr(item, k) and k != 'id': setattr(item, k, v)
    db.commit()
    log_audit(db, 'academic_regulation', item.id, 'update', data)
    return {'success': True}

@router.delete('/regulations/{item_id}')
async def delete_regulation(item_id: int, db: Session = Depends(get_db), current_user = Depends(require_super_admin)):
    item = db.query(AcademicRegulation).filter(AcademicRegulation.id == item_id).first()
    if not item: raise HTTPException(404)
    db.delete(item); db.commit()
    log_audit(db, 'academic_regulation', item_id, 'delete')
    return {'success': True}

@router.patch('/regulations/{item_id}/toggle')
async def toggle_regulation(item_id: int, db: Session = Depends(get_db)):
    item = db.query(AcademicRegulation).filter(AcademicRegulation.id == item_id).first()
    if not item: raise HTTPException(404)
    item.is_active = not item.is_active; db.commit()
    log_audit(db, 'academic_regulation', item.id, 'toggle', {'is_active': item.is_active})
    return {'success': True, 'is_active': item.is_active}


# 10. Grading System
@router.get('/grading')
async def list_grading(db: Session = Depends(get_db)):
    items = db.query(GradingSystem).order_by(GradingSystem.id.desc()).all()
    return {'items': [serialize(item) for item in items], 'total': len(items)}

@router.post('/grading')
async def create_grading(data: dict = Body(...), db: Session = Depends(get_db)):
    item = GradingSystem(**{k: v for k, v in data.items() if hasattr(GradingSystem, k) and k != 'id'})
    db.add(item); db.commit(); db.refresh(item)
    log_audit(db, 'grading_system', item.id, 'create', data)
    return {'success': True, 'id': item.id}

@router.get('/grading/{item_id}')
async def get_grading(item_id: int, db: Session = Depends(get_db)):
    item = db.query(GradingSystem).filter(GradingSystem.id == item_id).first()
    if not item: raise HTTPException(404)
    return serialize(item)

@router.put('/grading/{item_id}')
async def update_grading(item_id: int, data: dict = Body(...), db: Session = Depends(get_db)):
    item = db.query(GradingSystem).filter(GradingSystem.id == item_id).first()
    if not item: raise HTTPException(404)
    for k, v in data.items():
        if hasattr(item, k) and k != 'id': setattr(item, k, v)
    db.commit()
    log_audit(db, 'grading_system', item.id, 'update', data)
    return {'success': True}

@router.delete('/grading/{item_id}')
async def delete_grading(item_id: int, db: Session = Depends(get_db), current_user = Depends(require_super_admin)):
    item = db.query(GradingSystem).filter(GradingSystem.id == item_id).first()
    if not item: raise HTTPException(404)
    db.delete(item); db.commit()
    log_audit(db, 'grading_system', item_id, 'delete')
    return {'success': True}


# 11. Staff
@router.get('/staff')
async def list_staff(faculty_id: int = None, department_id: int = None, db: Session = Depends(get_db)):
    query = db.query(Staff)
    if faculty_id is not None: query = query.filter(Staff.faculty_id == faculty_id)
    if department_id is not None: query = query.filter(Staff.department_id == department_id)
    items = query.order_by(Staff.id.desc()).all()
    return {'items': [serialize(item) for item in items], 'total': len(items)}

@router.post('/staff')
async def create_staff(data: dict = Body(...), db: Session = Depends(get_db)):
    item = Staff(**{k: v for k, v in data.items() if hasattr(Staff, k) and k != 'id'})
    db.add(item); db.commit(); db.refresh(item)
    log_audit(db, 'staff', item.id, 'create', data)
    return {'success': True, 'id': item.id}

@router.get('/staff/{item_id}')
async def get_staff(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Staff).filter(Staff.id == item_id).first()
    if not item: raise HTTPException(404)
    return serialize(item)

@router.put('/staff/{item_id}')
async def update_staff(item_id: int, data: dict = Body(...), db: Session = Depends(get_db)):
    item = db.query(Staff).filter(Staff.id == item_id).first()
    if not item: raise HTTPException(404)
    for k, v in data.items():
        if hasattr(item, k) and k != 'id': setattr(item, k, v)
    db.commit()
    log_audit(db, 'staff', item.id, 'update', data)
    return {'success': True}

@router.delete('/staff/{item_id}')
async def delete_staff(item_id: int, db: Session = Depends(get_db), current_user = Depends(require_super_admin)):
    item = db.query(Staff).filter(Staff.id == item_id).first()
    if not item: raise HTTPException(404)
    db.delete(item); db.commit()
    log_audit(db, 'staff', item_id, 'delete')
    return {'success': True}

@router.patch('/staff/{item_id}/toggle')
async def toggle_staff(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Staff).filter(Staff.id == item_id).first()
    if not item: raise HTTPException(404)
    item.is_active = not item.is_active; db.commit()
    log_audit(db, 'staff', item.id, 'toggle', {'is_active': item.is_active})
    return {'success': True, 'is_active': item.is_active}


# 12. Courses
@router.get('/courses')
async def list_courses(department_id: int = None, program_id: int = None, db: Session = Depends(get_db)):
    query = db.query(Course)
    if department_id is not None: query = query.filter(Course.department_id == department_id)
    if program_id is not None: query = query.filter(Course.program_id == program_id)
    items = query.order_by(Course.id.desc()).all()
    return {'items': [serialize(item) for item in items], 'total': len(items)}

@router.post('/courses')
async def create_course(data: dict = Body(...), db: Session = Depends(get_db)):
    item = Course(**{k: v for k, v in data.items() if hasattr(Course, k) and k != 'id'})
    db.add(item); db.commit(); db.refresh(item)
    log_audit(db, 'course', item.id, 'create', data)
    return {'success': True, 'id': item.id}

@router.get('/courses/{item_id}')
async def get_course(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Course).filter(Course.id == item_id).first()
    if not item: raise HTTPException(404)
    return serialize(item)

@router.put('/courses/{item_id}')
async def update_course(item_id: int, data: dict = Body(...), db: Session = Depends(get_db)):
    item = db.query(Course).filter(Course.id == item_id).first()
    if not item: raise HTTPException(404)
    for k, v in data.items():
        if hasattr(item, k) and k != 'id': setattr(item, k, v)
    db.commit()
    log_audit(db, 'course', item.id, 'update', data)
    return {'success': True}

@router.delete('/courses/{item_id}')
async def delete_course(item_id: int, db: Session = Depends(get_db), current_user = Depends(require_super_admin)):
    item = db.query(Course).filter(Course.id == item_id).first()
    if not item: raise HTTPException(404)
    db.delete(item); db.commit()
    log_audit(db, 'course', item_id, 'delete')
    return {'success': True}

@router.patch('/courses/{item_id}/toggle')
async def toggle_course(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Course).filter(Course.id == item_id).first()
    if not item: raise HTTPException(404)
    item.is_active = not item.is_active; db.commit()
    log_audit(db, 'course', item.id, 'toggle', {'is_active': item.is_active})
    return {'success': True, 'is_active': item.is_active}


# 13. Student Services
@router.get('/services')
async def list_services(service_type: str = None, db: Session = Depends(get_db)):
    query = db.query(StudentService)
    if service_type is not None: query = query.filter(StudentService.service_type == service_type)
    items = query.order_by(StudentService.id.desc()).all()
    return {'items': [serialize(item) for item in items], 'total': len(items)}

@router.post('/services')
async def create_service(data: dict = Body(...), db: Session = Depends(get_db)):
    item = StudentService(**{k: v for k, v in data.items() if hasattr(StudentService, k) and k != 'id'})
    db.add(item); db.commit(); db.refresh(item)
    log_audit(db, 'student_service', item.id, 'create', data)
    return {'success': True, 'id': item.id}

@router.get('/services/{item_id}')
async def get_service(item_id: int, db: Session = Depends(get_db)):
    item = db.query(StudentService).filter(StudentService.id == item_id).first()
    if not item: raise HTTPException(404)
    return serialize(item)

@router.put('/services/{item_id}')
async def update_service(item_id: int, data: dict = Body(...), db: Session = Depends(get_db)):
    item = db.query(StudentService).filter(StudentService.id == item_id).first()
    if not item: raise HTTPException(404)
    for k, v in data.items():
        if hasattr(item, k) and k != 'id': setattr(item, k, v)
    db.commit()
    log_audit(db, 'student_service', item.id, 'update', data)
    return {'success': True}

@router.delete('/services/{item_id}')
async def delete_service(item_id: int, db: Session = Depends(get_db), current_user = Depends(require_super_admin)):
    item = db.query(StudentService).filter(StudentService.id == item_id).first()
    if not item: raise HTTPException(404)
    db.delete(item); db.commit()
    log_audit(db, 'student_service', item_id, 'delete')
    return {'success': True}

@router.patch('/services/{item_id}/toggle')
async def toggle_service(item_id: int, db: Session = Depends(get_db)):
    item = db.query(StudentService).filter(StudentService.id == item_id).first()
    if not item: raise HTTPException(404)
    item.is_active = not item.is_active; db.commit()
    log_audit(db, 'student_service', item.id, 'toggle', {'is_active': item.is_active})
    return {'success': True, 'is_active': item.is_active}


# 14. FAQs
@router.get('/faqs')
async def list_faqs(category: str = None, db: Session = Depends(get_db)):
    query = db.query(FAQ)
    if category is not None: query = query.filter(FAQ.category == category)
    items = query.order_by(FAQ.id.desc()).all()
    return {'items': [serialize(item) for item in items], 'total': len(items)}

@router.post('/faqs')
async def create_faq(data: dict = Body(...), db: Session = Depends(get_db)):
    item = FAQ(**{k: v for k, v in data.items() if hasattr(FAQ, k) and k != 'id'})
    db.add(item); db.commit(); db.refresh(item)
    log_audit(db, 'faq', item.id, 'create', data)
    return {'success': True, 'id': item.id}

@router.get('/faqs/{item_id}')
async def get_faq(item_id: int, db: Session = Depends(get_db)):
    item = db.query(FAQ).filter(FAQ.id == item_id).first()
    if not item: raise HTTPException(404)
    return serialize(item)

@router.put('/faqs/{item_id}')
async def update_faq(item_id: int, data: dict = Body(...), db: Session = Depends(get_db)):
    item = db.query(FAQ).filter(FAQ.id == item_id).first()
    if not item: raise HTTPException(404)
    for k, v in data.items():
        if hasattr(item, k) and k != 'id': setattr(item, k, v)
    db.commit()
    log_audit(db, 'faq', item.id, 'update', data)
    return {'success': True}

@router.delete('/faqs/{item_id}')
async def delete_faq(item_id: int, db: Session = Depends(get_db), current_user = Depends(require_super_admin)):
    item = db.query(FAQ).filter(FAQ.id == item_id).first()
    if not item: raise HTTPException(404)
    db.delete(item); db.commit()
    log_audit(db, 'faq', item_id, 'delete')
    return {'success': True}

@router.patch('/faqs/{item_id}/toggle')
async def toggle_faq(item_id: int, db: Session = Depends(get_db)):
    item = db.query(FAQ).filter(FAQ.id == item_id).first()
    if not item: raise HTTPException(404)
    item.is_active = not item.is_active; db.commit()
    log_audit(db, 'faq', item.id, 'toggle', {'is_active': item.is_active})
    return {'success': True, 'is_active': item.is_active}


# 15. Announcements
@router.get('/announcements')
async def list_announcements(type: str = None, db: Session = Depends(get_db)):
    query = db.query(Announcement)
    if type is not None: query = query.filter(Announcement.type == type)
    items = query.order_by(Announcement.id.desc()).all()
    return {'items': [serialize(item) for item in items], 'total': len(items)}

@router.post('/announcements')
async def create_announcement(data: dict = Body(...), db: Session = Depends(get_db)):
    item = Announcement(**{k: v for k, v in data.items() if hasattr(Announcement, k) and k != 'id'})
    db.add(item); db.commit(); db.refresh(item)
    log_audit(db, 'announcement', item.id, 'create', data)
    return {'success': True, 'id': item.id}

@router.get('/announcements/{item_id}')
async def get_announcement(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Announcement).filter(Announcement.id == item_id).first()
    if not item: raise HTTPException(404)
    return serialize(item)

@router.put('/announcements/{item_id}')
async def update_announcement(item_id: int, data: dict = Body(...), db: Session = Depends(get_db)):
    item = db.query(Announcement).filter(Announcement.id == item_id).first()
    if not item: raise HTTPException(404)
    for k, v in data.items():
        if hasattr(item, k) and k != 'id': setattr(item, k, v)
    db.commit()
    log_audit(db, 'announcement', item.id, 'update', data)
    return {'success': True}

@router.delete('/announcements/{item_id}')
async def delete_announcement(item_id: int, db: Session = Depends(get_db), current_user = Depends(require_super_admin)):
    item = db.query(Announcement).filter(Announcement.id == item_id).first()
    if not item: raise HTTPException(404)
    db.delete(item); db.commit()
    log_audit(db, 'announcement', item_id, 'delete')
    return {'success': True}

@router.patch('/announcements/{item_id}/toggle')
async def toggle_announcement(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Announcement).filter(Announcement.id == item_id).first()
    if not item: raise HTTPException(404)
    item.is_active = not item.is_active; db.commit()
    log_audit(db, 'announcement', item.id, 'toggle', {'is_active': item.is_active})
    return {'success': True, 'is_active': item.is_active}


# ══════════════════════════════════════════════════════
# Existing Document/System Endpoints
# ══════════════════════════════════════════════════════

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload and process a document (PDF, DOCX, TXT) into the knowledge base."""
    # Validate file type
    allowed_extensions = {".pdf", ".docx", ".doc", ".txt", ".md", ".json"}
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Allowed: {', '.join(allowed_extensions)}"
        )

    # Save file
    file_path = UPLOAD_DIR / file.filename
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # Create document record
    doc = Document(
        filename=file.filename,
        doc_type=ext.replace(".", ""),
        original_size=len(content),
        status="pending",
        added_at=datetime.utcnow(),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Process the document
    try:
        chunks, metadatas, ids = process_file(str(file_path))

        if not chunks:
            doc.status = "failed"
            db.commit()
            raise HTTPException(status_code=400, detail="No content could be extracted from the file")

        # Add to vector store
        vector_store = get_vector_store()
        vector_store.add_documents(texts=chunks, metadatas=metadatas, ids=ids)

        # Update document record
        doc.chunk_count = len(chunks)
        doc.status = "processed"
        db.commit()

        return {
            "success": True,
            "document_id": doc.id,
            "filename": doc.filename,
            "chunks_created": len(chunks),
            "message": f"تم معالجة الملف بنجاح: {len(chunks)} جزء | File processed: {len(chunks)} chunks",
        }

    except HTTPException:
        raise
    except Exception as e:
        doc.status = "failed"
        db.commit()
        logger.error(f"Document processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(db: Session = Depends(get_db)):
    """List all uploaded documents."""
    docs = db.query(Document).order_by(Document.added_at.desc()).all()
    return DocumentListResponse(
        documents=[
            DocumentOut(
                id=d.id,
                filename=d.filename,
                doc_type=d.doc_type,
                chunk_count=d.chunk_count,
                added_at=d.added_at,
                status=d.status,
            )
            for d in docs
        ],
        total=len(docs),
    )


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: int, db: Session = Depends(get_db)):
    """Delete a document and its chunks from the knowledge base."""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Remove from vector store
    vector_store = get_vector_store()
    deleted_count = vector_store.delete_by_source(doc.filename)

    # Remove file
    file_path = UPLOAD_DIR / doc.filename
    if file_path.exists():
        os.remove(file_path)

    # Remove from database
    db.delete(doc)
    db.commit()

    return {
        "success": True,
        "message": f"تم حذف {doc.filename}: {deleted_count} جزء | Deleted {doc.filename}: {deleted_count} chunks",
    }


@router.post("/load-knowledge-base")
async def load_knowledge_base(db: Session = Depends(get_db)):
    """Load the built-in UST knowledge base into the vector store."""
    kb_path = KNOWLEDGE_BASE_DIR / "ust_data.json"
    if not kb_path.exists():
        raise HTTPException(status_code=404, detail="Knowledge base file not found")

    try:
        chunks, metadatas, ids = process_file(str(kb_path))
        vector_store = get_vector_store()

        # Clear existing knowledge base entries
        vector_store.delete_by_source("ust_knowledge_base")

        # Add new entries
        vector_store.add_documents(texts=chunks, metadatas=metadatas, ids=ids)

        # Record in documents table
        existing = db.query(Document).filter(Document.filename == "ust_data.json").first()
        if existing:
            existing.chunk_count = len(chunks)
            existing.status = "processed"
            existing.added_at = datetime.utcnow()
        else:
            doc = Document(
                filename="ust_data.json",
                doc_type="json",
                chunk_count=len(chunks),
                status="processed",
            )
            db.add(doc)

        db.commit()

        return {
            "success": True,
            "chunks_loaded": len(chunks),
            "message": f"تم تحميل قاعدة المعرفة: {len(chunks)} جزء | Knowledge base loaded: {len(chunks)} chunks",
        }

    except Exception as e:
        logger.error(f"Knowledge base loading error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rebuild-index")
async def rebuild_index(db: Session = Depends(get_db)):
    """Rebuild the entire vector store index from all documents."""
    vector_store = get_vector_store()
    vector_store.reset()

    # Re-process all documents
    docs = db.query(Document).filter(Document.status == "processed").all()
    total_chunks = 0

    for doc in docs:
        if doc.filename == "ust_data.json":
            file_path = str(KNOWLEDGE_BASE_DIR / doc.filename)
        else:
            file_path = str(UPLOAD_DIR / doc.filename)

        if Path(file_path).exists():
            chunks, metadatas, ids = process_file(file_path)
            if chunks:
                vector_store.add_documents(texts=chunks, metadatas=metadatas, ids=ids)
                total_chunks += len(chunks)

    return {
        "success": True,
        "total_chunks": total_chunks,
        "documents_processed": len(docs),
        "message": f"تم إعادة بناء الفهرس: {total_chunks} جزء | Index rebuilt: {total_chunks} chunks",
    }


@router.get("/conversations")
async def list_conversations(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """List all conversations for admin review."""
    conv_service = ConversationService(db)
    conversations = conv_service.get_all_conversations(skip=skip, limit=limit)

    return {
        "conversations": [
            {
                "id": c.id,
                "started_at": c.started_at.isoformat(),
                "message_count": c.message_count,
                "language": c.language,
            }
            for c in conversations
        ],
        "total": len(conversations),
    }


@router.get("/system-status")
async def system_status():
    """Get system health status."""
    from core.llm_handler import get_llm_handler
    from core.embeddings import get_embedding_manager

    vector_store = get_vector_store()
    llm = get_llm_handler()

    llm_status = await llm.health_check()
    embedding_info = get_embedding_manager().get_model_info()
    vector_stats = vector_store.get_stats()

    return {
        "status": "running",
        "llm": llm_status,
        "embeddings": embedding_info,
        "vector_store": vector_stats,
    }
