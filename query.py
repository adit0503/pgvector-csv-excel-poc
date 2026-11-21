"""
Query interface demonstrating:
1. Pure Semantic Vector Search (Cosine Similarity)
2. Hybrid Search (SQL Relational Filtering + Vector Similarity)
3. Excel Ingested Ticket Search (Semantic incident resolution)
4. EXPLAIN ANALYZE execution plan breakdown (HNSW Index Scan)
"""

import sys
from tabulate import tabulate
from db import get_connection
from embedder import embed_query

def semantic_search_products(query_text: str, top_k: int = 3):
    """
    Finds the most semantically relevant products using pgvector's cosine distance operator (<=>).
    Formula: Cosine Similarity = 1 - (embedding <=> query_vector)
    """
    query_vector = embed_query(query_text)
    conn = get_connection()
    cur = conn.cursor()

    sql = """
        SELECT sku, name, category, price, rating, description,
               1 - (embedding <=> %s) AS similarity
        FROM products
        ORDER BY embedding <=> %s
        LIMIT %s;
    """
    cur.execute(sql, (query_vector, query_vector, top_k))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    results = []
    for r in rows:
        results.append({
            "SKU": r[0],
            "Name": r[1],
            "Category": r[2],
            "Price": f"${float(r[3]):.2f}",
            "Score": f"{float(r[6]):.4f}",
            "Description": r[5][:75] + "..." if len(r[5]) > 75 else r[5]
        })
    return results

def hybrid_search_products(query_text: str, max_price: float = None, category: str = None, top_k: int = 3):
    """
    Demonstrates Hybrid Search: Combining relational SQL WHERE filters with Vector Similarity.
    PostgreSQL's optimizer applies relational index filters alongside the HNSW vector index.
    """
    query_vector = embed_query(query_text)
    conn = get_connection()
    cur = conn.cursor()

    where_clauses = []
    params = [query_vector]

    if max_price is not None:
        where_clauses.append("price <= %s")
        params.append(max_price)
    
    if category is not None:
        where_clauses.append("category = %s")
        params.append(category)

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
    params.extend([query_vector, top_k])

    sql = f"""
        SELECT sku, name, category, price, rating,
               1 - (embedding <=> %s) AS similarity
        FROM products
        {where_sql}
        ORDER BY embedding <=> %s
        LIMIT %s;
    """

    cur.execute(sql, tuple(params))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    results = []
    for r in rows:
        results.append({
            "SKU": r[0],
            "Name": r[1],
            "Category": r[2],
            "Price": f"${float(r[3]):.2f}",
            "Score": f"{float(r[5]):.4f}"
        })
    return results

def search_tickets(query_text: str, top_k: int = 2):
    """
    Queries the customer_tickets table (ingested from Excel .xlsx) to find
    similar past incidents and their documented resolutions.
    """
    query_vector = embed_query(query_text)
    conn = get_connection()
    cur = conn.cursor()

    sql = """
        SELECT ticket_id, department, priority, title, resolution,
               1 - (embedding <=> %s) AS similarity
        FROM customer_tickets
        ORDER BY embedding <=> %s
        LIMIT %s;
    """
    cur.execute(sql, (query_vector, query_vector, top_k))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    results = []
    for r in rows:
        results.append({
            "Ticket ID": r[0],
            "Department": r[1],
            "Priority": r[2],
            "Title": r[3],
            "Resolution": r[4],
            "Similarity": f"{float(r[5]):.4f}"
        })
    return results

def explain_vector_query(query_text: str):
    """
    Runs EXPLAIN (ANALYZE, BUFFERS) to demonstrate Postgres using the HNSW index vs sequential scan.
    """
    query_vector = embed_query(query_text)
    conn = get_connection()
    cur = conn.cursor()

    # Note: On very small datasets, Postgres cost planner may choose Seq Scan unless
    # enable_seqscan = off is toggled to inspect the index path.
    cur.execute("SET enable_seqscan = off;")
    sql = """
        EXPLAIN (ANALYZE, BUFFERS)
        SELECT sku, name, 1 - (embedding <=> %s) AS similarity
        FROM products
        ORDER BY embedding <=> %s
        LIMIT 3;
    """
    cur.execute(sql, (query_vector, query_vector))
    plan_lines = [r[0] for r in cur.fetchall()]
    cur.execute("SET enable_seqscan = on;")

    cur.close()
    conn.close()
    return "\n".join(plan_lines)

def interactive_cli():
    print("\n" + "="*60)
    print("  PGVECTOR INTERACTIVE QUERY CONSOLE")
    print("="*60)
    print("Options:")
    print("  1: Search Products (from CSV)")
    print("  2: Hybrid Filtered Search Products (e.g., price filter + semantic query)")
    print("  3: Search IT Support Incidents & Resolutions (from Excel)")
    print("  4: Show Query Execution Plan (EXPLAIN ANALYZE HNSW)")
    print("  q: Exit")
    print("="*60)

    while True:
        choice = input("\nSelect option (1-4, q): ").strip()
        if choice in ['q', 'exit', 'quit']:
            print("Goodbye!")
            break

        if choice == "1":
            q = input("Enter product search query: ").strip()
            if not q:
                continue
            res = semantic_search_products(q, top_k=3)
            print("\nTop Matching Products:")
            print(tabulate(res, headers="keys", tablefmt="rounded_outline"))

        elif choice == "2":
            q = input("Enter product search query: ").strip()
            max_p = input("Enter max price (or press Enter to skip): ").strip()
            max_price = float(max_p) if max_p else None
            cat = input("Enter category filter (e.g. Audio, Electronics, Kitchen, Fitness) or Enter to skip: ").strip()
            category = cat if cat else None
            res = hybrid_search_products(q, max_price=max_price, category=category, top_k=3)
            print("\nHybrid Search Results:")
            print(tabulate(res, headers="keys", tablefmt="rounded_outline"))

        elif choice == "3":
            q = input("Enter IT incident symptom or error description: ").strip()
            if not q:
                continue
            res = search_tickets(q, top_k=2)
            print("\nMatching IT Incidents & Solutions:")
            for item in res:
                print(f"\n[{item['Ticket ID']}] ({item['Department']} - {item['Priority']}) | Similarity: {item['Similarity']}")
                print(f"Title: {item['Title']}")
                print(f"Resolution: {item['Resolution']}")

        elif choice == "4":
            q = input("Enter query for EXPLAIN ANALYZE: ").strip() or "wireless audio"
            plan = explain_vector_query(q)
            print("\nPostgreSQL Query Plan:")
            print(plan)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        query_arg = " ".join(sys.argv[1:])
        print(f"Executing semantic search for: '{query_arg}'")
        res = semantic_search_products(query_arg)
        print(tabulate(res, headers="keys", tablefmt="rounded_outline"))
    else:
        interactive_cli()
