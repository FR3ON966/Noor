FROM python:3.10-slim

# Set up a non-root user (required by Hugging Face Spaces)
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY --chown=user backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY --chown=user . .

# Initialize the database and knowledge base
RUN cd backend && python -c "from models.database import init_db; init_db()"
RUN cd backend && python seed_data.py
RUN cd backend && python migrate_json.py

# Expose the port
EXPOSE 7860
ENV PORT=7860

# Start the application
CMD cd backend && uvicorn main:app --host 0.0.0.0 --port 7860
