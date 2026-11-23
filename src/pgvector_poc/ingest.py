"""
Ingestion pipeline for CSV & Excel files into PostgreSQL with pgvector.

Pipeline steps:
1. Load CSV (e.g., products.csv) using pandas.
2. Load XLSX (e.g., customer_tickets.xlsx) using pandas.
3. Transform rows into semantic textual representations.
4. Generate 384-dimensional vector embeddings using sentence-transformers.
5. Ingest structured columns + vectors into PostgreSQL tables using UPSERT.
6. Build HNSW (Hierarchical Navigable Small World) vector index.
"""

import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np

# Ensure package import works when run directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pgvector_poc.config import DATA_DIR, CSV_PATH, XLSX_PATH
from pgvector_poc.db import get_connection, init_database, create_vector_indexes
from pgvector_poc.embedder import embed_texts, row_to_search_text_product, row_to_search_text_ticket
from pgvector_poc import generate_data

def ensure_sample_data():
    if not os.path.exists(CSV_PATH) or not os.path.exists(XLSX_PATH):
        print("-> Sample files missing. Generating sample datasets...")
        generate_data.generate_csv()
        generate_data.generate_xlsx()

def ingest_products_csv():
    print(f"\n==========================================")
    print(f"STEP 1: Ingesting CSV File -> {CSV_PATH}")
    print(f"==========================================")
    
    df = pd.read_csv(CSV_PATH)
    print(f"-> Loaded {len(df)} rows from CSV.")
    print(f"-> Columns: {list(df.columns)}")

    # 1. Create text representation for each row
    print("-> Creating semantic text representations for each product row...")
    df['search_text'] = df.apply(lambda r: row_to_search_text_product(r.to_dict()), axis=1)

    # 2. Compute embeddings
    print("-> Generating 384-dimension vector embeddings using sentence-transformers...")
    vectors = embed_texts(df['search_text'].tolist())
    df['embedding'] = list(vectors)

    # 3. Insert into PostgreSQL
    conn = get_connection()
    cur = conn.cursor()
    print("-> Storing rows and vectors into 'products' table...")
    
    insert_sql = """
        INSERT INTO products (sku, name, category, price, rating, description, stock, search_text, embedding)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (sku) DO UPDATE SET
            name = EXCLUDED.name,
            category = EXCLUDED.category,
            price = EXCLUDED.price,
            rating = EXCLUDED.rating,
            description = EXCLUDED.description,
            stock = EXCLUDED.stock,
            search_text = EXCLUDED.search_text,
            embedding = EXCLUDED.embedding;
    """

    for _, row in df.iterrows():
        cur.execute(insert_sql, (
            row['sku'],
            row['name'],
            row['category'],
            float(row['price']),
            float(row['rating']),
            row['description'],
            int(row['stock']),
            row['search_text'],
            row['embedding']
        ))

    cur.close()
    conn.close()
    print(f"-> Successfully inserted/updated {len(df)} products with vector embeddings!")

def ingest_tickets_xlsx():
    print(f"\n==========================================")
    print(f"STEP 2: Ingesting Excel File -> {XLSX_PATH}")
    print(f"==========================================")
    
    df = pd.read_excel(XLSX_PATH, engine="openpyxl")
    print(f"-> Loaded {len(df)} rows from XLSX.")
    print(f"-> Columns: {list(df.columns)}")

    # 1. Create text representation
    print("-> Creating semantic text representations for each ticket row...")
    df['search_text'] = df.apply(lambda r: row_to_search_text_ticket(r.to_dict()), axis=1)

    # 2. Compute embeddings
    print("-> Generating 384-dimension vector embeddings using sentence-transformers...")
    vectors = embed_texts(df['search_text'].tolist())
    df['embedding'] = list(vectors)

    # 3. Insert into PostgreSQL
    conn = get_connection()
    cur = conn.cursor()
    print("-> Storing rows and vectors into 'customer_tickets' table...")
    
    insert_sql = """
        INSERT INTO customer_tickets (ticket_id, department, priority, title, description, resolution, search_text, embedding)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (ticket_id) DO UPDATE SET
            department = EXCLUDED.department,
            priority = EXCLUDED.priority,
            title = EXCLUDED.title,
            description = EXCLUDED.description,
            resolution = EXCLUDED.resolution,
            search_text = EXCLUDED.search_text,
            embedding = EXCLUDED.embedding;
    """

    for _, row in df.iterrows():
        cur.execute(insert_sql, (
            row['ticket_id'],
            row['department'],
            row['priority'],
            row['title'],
            row['description'],
            row['resolution'],
            row['search_text'],
            row['embedding']
        ))

    cur.close()
    conn.close()
    print(f"-> Successfully inserted/updated {len(df)} tickets with vector embeddings!")

def run_pipeline():
    ensure_sample_data()
    init_database()
    ingest_products_csv()
    ingest_tickets_xlsx()
    create_vector_indexes()
    print("\n[SUCCESS] Ingestion & Vector Indexing Pipeline complete!")

if __name__ == "__main__":
    run_pipeline()
