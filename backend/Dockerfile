FROM python:3.13-slim

WORKDIR /app

# Copy pyproject.toml and README first
COPY pyproject.toml README.md ./

# Install dependencies from pyproject.toml
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Copy backend code
COPY backend/ /app/backend/

# Copy data directory (if needed)
COPY data/ /app/data/

# Expose port
EXPOSE 8000

# Run the FastAPI application with hot reload for development
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
