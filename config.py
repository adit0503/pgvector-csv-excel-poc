import os

# Database Configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "vectordb")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password123")

# Embedding Model Configuration
# 'all-MiniLM-L6-v2' maps sentences & paragraphs to a 384 dimensional dense vector space.
# It is very fast, accurate, runs locally on CPU with zero API costs.
MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384
