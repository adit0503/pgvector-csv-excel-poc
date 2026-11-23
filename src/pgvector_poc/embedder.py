"""
Embedding Service using sentence-transformers (all-MiniLM-L6-v2).
Converts text descriptions or tabular rows into dense 384-dimensional vectors.
"""

import sys
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer

# Ensure package import works when run directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pgvector_poc import config

_model = None

def get_model():
    global _model
    if _model is None:
        print(f"-> Loading embedding model '{config.MODEL_NAME}' into memory...")
        _model = SentenceTransformer(config.MODEL_NAME)
    return _model

def embed_texts(texts: list[str]) -> np.ndarray:
    """Encodes a list of strings into normalized 384-dimensional float vectors as a numpy array."""
    model = get_model()
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return np.asarray(embeddings, dtype=np.float32)

def embed_query(query: str) -> np.ndarray:
    """Encodes a single query string into a 1D numpy vector."""
    return embed_texts([query])[0]

def row_to_search_text_product(row: dict) -> str:
    """
    Transforms tabular product row into a structured descriptive passage for embedding.
    Combining key attributes (Name, Category, Specs, Description) gives the model
    rich semantic context across both structured and unstructured fields.
    """
    return (
        f"Product: {row['name']} | "
        f"Category: {row['category']} | "
        f"Price: ${row['price']} | "
        f"Rating: {row.get('rating', 'N/A')}/5.0 | "
        f"Description: {row['description']}"
    )

def row_to_search_text_ticket(row: dict) -> str:
    """
    Transforms tabular ticket row into a searchable incident summary.
    """
    return (
        f"Ticket: {row['ticket_id']} | "
        f"Department: {row['department']} | "
        f"Priority: {row['priority']} | "
        f"Title: {row['title']} | "
        f"Issue Description: {row['description']} | "
        f"Resolution: {row['resolution']}"
    )
