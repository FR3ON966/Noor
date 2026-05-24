"""
UST Smart Chatbot — Main Application
FastAPI entry point with CORS, static files, and startup initialization.

University of Science and Technology — Student Inquiry System
جامعة العلوم والتقانة — نظام استفسارات الطلبة
"""

import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, BackgroundTasks, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import secrets
from core.auth import verify_admin

from config import APP_HOST, APP_PORT, DEBUG, BASE_DIR, PROJECT_DIR
from models.database import init_db

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("UST-Chatbot")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # ──── Startup ────
    logger.info("=" * 60)
    logger.info("  UST Smart Chatbot — Starting Up")
    logger.info("  جامعة العلوم والتقانة — نظام الاستفسارات الذكي")
    logger.info("=" * 60)

    # Initialize database
    logger.info("Initializing database...")
    init_db()

    # Initialize vector store (loads ChromaDB)
    logger.info("Initializing vector store...")
    from core.vector_store import get_vector_store
    vs = get_vector_store()
    logger.info(f"Vector store ready: {vs.get_document_count()} chunks indexed")

    # Auto-load knowledge base if empty
    if vs.get_document_count() == 0:
        logger.info("Vector store is empty. Auto-loading UST knowledge base...")
        from services.document_processor import process_json_knowledge_base
        try:
            chunks, metadatas = process_json_knowledge_base()
            if chunks:
                import hashlib
                ids = [hashlib.md5(f"ust_kb::{i}".encode()).hexdigest() for i in range(len(chunks))]
                vs.add_documents(texts=chunks, metadatas=metadatas, ids=ids)
                logger.info(f"Successfully loaded {len(chunks)} chunks into vector store.")
        except Exception as e:
            logger.error(f"Failed to load knowledge base: {e}")
            
    # Auto-create default admin user
    from models.database import AdminUser, SessionLocal
    from core.auth import get_password_hash
    db = SessionLocal()
    if db.query(AdminUser).count() == 0:
        logger.info("Creating default admin user...")
        default_admin = AdminUser(
            username="admin",
            hashed_password=get_password_hash("ust1234"),
            role="super_admin"
        )
        db.add(default_admin)
        db.commit()
    db.close()

    # Check LLM status
    logger.info("Checking LLM connection...")
    from core.llm_handler import get_llm_handler
    llm = get_llm_handler()
    llm_status = await llm.health_check()
    logger.info(f"LLM Status: {llm_status}")

    logger.info("=" * 60)
    logger.info(f"  Server ready at http://localhost:{APP_PORT}")
    logger.info(f"  Chat UI: http://localhost:{APP_PORT}")
    logger.info(f"  Admin Panel: http://localhost:{APP_PORT}/admin")
    logger.info(f"  API Docs: http://localhost:{APP_PORT}/docs")
    logger.info("=" * 60)

    yield

    # ──── Shutdown ────
    logger.info("UST Smart Chatbot — Shutting Down")


# Create FastAPI app
app = FastAPI(
    title="UST Smart Chatbot API",
    description="نظام المحادثة الذكي لاستفسارات طلاب جامعة العلوم والتقانة\n\nSmart Chatbot System for UST Student Inquiries",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
from api.chat import router as chat_router
from api.admin import router as admin_router
from api.analytics import router as analytics_router

app.include_router(chat_router)
app.include_router(admin_router)
app.include_router(analytics_router)

# Serve frontend static files
frontend_dir = PROJECT_DIR / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")


@app.get("/")
async def serve_chat():
    """Serve the main chat interface."""
    index_path = frontend_dir / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "UST Smart Chatbot API is running. Visit /docs for API documentation."}


class LoginRequest(BaseModel):
    username: str
    password: str

from sqlalchemy.orm import Session
from models.database import get_db, AdminUser
from core.auth import verify_password, create_access_token

@app.post("/api/admin/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(AdminUser).filter(AdminUser.username == req.username).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")
        
    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    return {"token": access_token}


@app.get("/admin")
async def serve_admin():
    """Serve the admin panel."""
    admin_path = frontend_dir / "admin.html"
    if admin_path.exists():
        return FileResponse(str(admin_path))
    return {"message": "Admin panel not found."}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "UST Smart Chatbot"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=APP_HOST, port=APP_PORT, reload=DEBUG)
