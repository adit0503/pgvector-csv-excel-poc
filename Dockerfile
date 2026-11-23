FROM python:3.11-slim

WORKDIR /app

# Install system dependencies needed for building C extensions if necessary
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the Hugging Face sentence-transformers model to cache it inside image
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

COPY . .
RUN pip install --no-cache-dir -e .

ENV PYTHONPATH=/app/src

CMD ["python", "-m", "pgvector_poc.demo"]
