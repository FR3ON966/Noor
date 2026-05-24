# 🎓 نور — نظام المحادثة الذكي | UST Smart Chatbot

> نظام شات بوت ذكي لاستفسارات طلاب جامعة العلوم والتقانة
> Smart Chatbot System for University of Science & Technology Student Inquiries

## 🏗️ Architecture

```
Student Question → Embedding → Vector Search (ChromaDB) → Context Retrieval → LLM (Ollama/qwen2.5) → Answer
```

**RAG Pipeline (Retrieval-Augmented Generation):** The system searches a knowledge base of university documents to find relevant information, then uses an LLM to generate natural, accurate answers grounded in official data.

## ⚡ Quick Start

### Prerequisites
- Python 3.10+
- [Ollama](https://ollama.ai) with `qwen2.5` model

### Setup
```bash
# 1. Create virtual environment
cd backend
python -m venv venv
venv\Scripts\activate   # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
# Edit .env file (already created from .env.example)

# 4. Start Ollama (in separate terminal)
ollama serve

# 5. Run the server
python main.py
```

### Access
- 💬 **Chat Interface:** http://localhost:8000
- ⚙️ **Admin Panel:** http://localhost:8000/admin
- 📚 **API Docs:** http://localhost:8000/docs

## 📁 Project Structure

```
├── backend/
│   ├── main.py              # FastAPI entry point
│   ├── config.py             # Configuration
│   ├── api/                  # API endpoints (chat, admin, analytics)
│   ├── core/                 # RAG pipeline, embeddings, vector store, LLM
│   ├── models/               # Database models & Pydantic schemas
│   ├── services/             # Document processor & conversation service
│   └── knowledge_base/       # UST knowledge base (JSON)
├── frontend/
│   ├── index.html/style.css/app.js    # Chat interface
│   └── admin.html/admin.css/admin.js  # Admin panel
└── data/                     # Test questions & evaluation sets
```

## 🔧 Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | FastAPI (Python) |
| LLM | Ollama + Qwen 2.5 |
| Embeddings | sentence-transformers (multilingual) |
| Vector DB | ChromaDB |
| Database | SQLite + SQLAlchemy |
| Frontend | HTML/CSS/JS (RTL, bilingual) |

## 📊 Evaluation Metrics

- **Retrieval Accuracy:** Are correct chunks retrieved?
- **Answer Relevance:** Is the answer relevant? (1-5 scale)
- **Response Time:** Average response latency
- **Coverage Rate:** % of questions answered vs "I don't know"

---
**جامعة العلوم والتقانة | University of Science & Technology**
"# Noor" 
