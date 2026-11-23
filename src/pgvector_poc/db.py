"""
Database connection and schema setup helper.
Manages PostgreSQL connection, pgvector extension, table schemas, and HNSW indexes.
"""

import sys
from pathlib import Path
import psycopg2
from pgvector.psycopg2 import register_vector

# Ensure package import works when run directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pgvector_poc import config

def get_connection():
    """Establishes connection to PostgreSQL and registers pgvector adapter."""
    conn = psycopg2.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        dbname=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASSWORD
    )
    conn.autocommit = True
    try:
        register_vector(conn)
    except Exception:
        # If vector extension is not yet created in the DB, register_vector might fail
        pass
    return conn

def init_database():
    """
    Initializes pgvector extension and creates tables for:
    1. products (from CSV)
    2. customer_tickets (from XLSX)
    """
    conn = get_connection()
    cur = conn.cursor()

    print("-> Ensuring 'vector' extension is enabled in PostgreSQL...")
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    register_vector(conn)

    print("-> Creating 'products' table (CSV target)...")
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            sku VARCHAR(50) UNIQUE,
            name VARCHAR(255) NOT NULL,
            category VARCHAR(100) NOT NULL,
            price NUMERIC(10, 2) NOT NULL,
            rating NUMERIC(3, 1),
            description TEXT NOT NULL,
            stock INT,
            search_text TEXT,
            embedding vector({config.EMBEDDING_DIM})
        );
    """)

    print("-> Creating 'customer_tickets' table (XLSX target)...")
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS customer_tickets (
            id SERIAL PRIMARY KEY,
            ticket_id VARCHAR(50) UNIQUE,
            department VARCHAR(100) NOT NULL,
            priority VARCHAR(50) NOT NULL,
            title VARCHAR(255) NOT NULL,
            description TEXT NOT NULL,
            resolution TEXT NOT NULL,
            search_text TEXT,
            embedding vector({config.EMBEDDING_DIM})
        );
    """)

    cur.close()
    conn.close()
    print("-> Tables initialized successfully.")

def create_vector_indexes():
    """
    Creates HNSW (Hierarchical Navigable Small World) vector indexes.
    
    Why HNSW?
    - Provides fast Approximate Nearest Neighbor (ANN) search with high recall.
    - Uses a multi-layer graph navigation structure.
    - Parameter 'm': max bidirectional connections per layer node (default 16).
    - Parameter 'ef_construction': size of dynamic candidate list during graph building (default 64).
    - 'vector_cosine_ops': distance operator for Cosine distance (<=>).
    """
    conn = get_connection()
    cur = conn.cursor()

    print("-> Building HNSW vector index on products(embedding)...")
    cur.execute("""
        CREATE INDEX IF NOT EXISTS products_hnsw_idx 
        ON products 
        USING hnsw (embedding vector_cosine_ops) 
        WITH (m = 16, ef_construction = 64);
    """)

    print("-> Building HNSW vector index on customer_tickets(embedding)...")
    cur.execute("""
        CREATE INDEX IF NOT EXISTS tickets_hnsw_idx 
        ON customer_tickets 
        USING hnsw (embedding vector_cosine_ops) 
        WITH (m = 16, ef_construction = 64);
    """)

    # Also build standard B-tree indexes for hybrid filtering
    cur.execute("CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_products_price ON products(price);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_tickets_department ON customer_tickets(department);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_tickets_priority ON customer_tickets(priority);")

    cur.close()
    conn.close()
    print("-> Vector and hybrid indexes created successfully.")
