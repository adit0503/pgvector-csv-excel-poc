import os
from pathlib import Path

# Base Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR", PROJECT_ROOT / "sample_data"))
CSV_PATH = DATA_DIR / "products.csv"
XLSX_PATH = DATA_DIR / "customer_tickets.xlsx"

# Database Configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "vectordb")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password123")

# Embedding Model Configuration
# 'all-MiniLM-L6-v2' maps sentences & paragraphs to a 384 dimensional dense vector space.
# It is very fast, accurate, runs locally on CPU with zero API costs.
MODEL_NAME = os.getenv("MODEL_NAME", "all-MiniLM-L6-v2")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "384"))
