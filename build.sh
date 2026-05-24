#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r backend/requirements.txt

echo "🗄️ Initializing database and knowledge base..."
cd backend
python -c "from models.database import init_db; init_db()"
python seed_data.py
python migrate_json.py

echo "✅ Build complete!"
