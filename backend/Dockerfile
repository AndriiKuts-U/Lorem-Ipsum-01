FROM python:3.13-slim

WORKDIR /app

# Copy pyproject.toml first
COPY pyproject.toml .

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir fastapi openai pydantic-settings qdrant-client uvicorn requests beautifulsoup4

# Copy backend code
COPY backend/ /app/backend/

# Copy data directory (if needed)
COPY data/ /app/data/

# Expose port
EXPOSE 8000

# Run the FastAPI application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
