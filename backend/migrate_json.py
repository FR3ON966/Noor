"""
UST Smart Chatbot — Migration Script
Migrates the existing ust_data.json into the SQLite database.
"""

import json
import logging
import os
from datetime import datetime
from sqlalchemy.orm import Session
from models.database import init_db, SessionLocal, KnowledgeEntry
from config import KNOWLEDGE_BASE_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MigrateJSON")

def migrate_json_to_db():
    init_db()
    db = SessionLocal()
    
    json_path = os.path.join(KNOWLEDGE_BASE_DIR, "ust_data.json")
    if not os.path.exists(json_path):
        logger.error(f"File not found: {json_path}")
        return

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"Found {len(data)} entries in {json_path}. Migrating...")
        
        added_count = 0
        skipped_count = 0
        
        for item in data:
            title_en = item.get('title_en', '')
            
            # Check if entry exists by title_en
            existing = db.query(KnowledgeEntry).filter(KnowledgeEntry.title_en == title_en).first()
            if existing:
                skipped_count += 1
                continue
            
            keywords_str = ""
            if isinstance(item.get('keywords'), list):
                keywords_str = json.dumps(item.get('keywords'), ensure_ascii=False)
            else:
                keywords_str = item.get('keywords', '')
                
            entry = KnowledgeEntry(
                category_ar=item.get('category_ar'),
                category_en=item.get('category_en'),
                title_ar=item.get('title_ar'),
                title_en=item.get('title_en'),
                content_ar=item.get('content_ar'),
                content_en=item.get('content_en'),
                keywords=keywords_str,
                is_active=True,
                last_updated=datetime.utcnow()
            )
            db.add(entry)
            added_count += 1
            
        db.commit()
        logger.info(f"Migration completed. Added: {added_count}, Skipped (already exist): {skipped_count}.")
        
    except Exception as e:
        logger.error(f"Error during migration: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_json_to_db()
