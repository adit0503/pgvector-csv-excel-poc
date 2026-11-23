"""
End-to-End Automated Demonstration Script.
Walks through all key concepts:
1. Ingestion verification
2. CSV Semantic Search (Matching user intent without exact keywords)
3. CSV Hybrid Search (Vector similarity + SQL WHERE constraints)
4. Excel Semantic Search (Finding past incident troubleshooting steps)
5. Execution Plan Inspection (EXPLAIN ANALYZE showing HNSW Index Scan)
"""

import sys
import time
from pathlib import Path
from tabulate import tabulate

# Ensure package import works when run directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pgvector_poc import ingest
from pgvector_poc.query import (
    semantic_search_products,
    hybrid_search_products,
    search_tickets,
    explain_vector_query,
)

def print_header(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def main():
    print_header("PGVECTOR DEMO: SEMANTIC INDEXING & QUERYING FOR CSV & EXCEL")
    print("This proof-of-concept demonstrates how high-dimensional vector embeddings and")
    print("PostgreSQL's pgvector HNSW index unlock semantic search across tabular datasets.\n")

    # Step 1: Ingestion
    print_header("PHASE 1: PIPELINE INGESTION & HNSW INDEX CREATION")
    t0 = time.time()
    ingest.run_pipeline()
    print(f"Pipeline executed in {time.time() - t0:.2f} seconds.")

    # Step 2: Semantic Search on Products (CSV)
    print_header("PHASE 2: SEMANTIC SEARCH ON CSV DATA (products.csv)")
    print("Notice: The query does NOT use exact keywords present in the product title,")
    print("yet pgvector finds the exact matching items by conceptual proximity in vector space.\n")

    queries_csv = [
        "silent travel listening with comfortable ears on long flights",
        "work from home setup to fix severe lower back spine fatigue",
        "morning coffee brewing appliance with microfoam milk texture"
    ]

    for q in queries_csv:
        print(f"-> USER QUERY: \"{q}\"")
        results = semantic_search_products(q, top_k=2)
        print(tabulate(results, headers="keys", tablefmt="rounded_outline"))
        print()

    # Step 3: Hybrid Search (Vector + Relational Filters)
    print_header("PHASE 3: HYBRID SEARCH (METADATA FILTER + VECTOR SIMILARITY)")
    print("Unlike standalone vector databases that require awkward two-pass filtering,")
    print("PostgreSQL combines B-tree relational filters (price, category) and HNSW vector index.")
    
    hybrid_query = "heavy resistance muscle strength workout equipment"
    print(f"-> QUERY: \"{hybrid_query}\"")
    print("-> FILTER: price <= $100 AND category = 'Fitness'")
    res_hybrid = hybrid_search_products(hybrid_query, max_price=100.0, category="Fitness", top_k=3)
    print(tabulate(res_hybrid, headers="keys", tablefmt="rounded_outline"))
    print("(Notice how the expensive $310 dumbbell set was filtered out by SQL price <= 100, leaving the $54 yoga mat)")

    # Step 4: Semantic Search on Excel Data (XLSX)
    print_header("PHASE 4: SEMANTIC SEARCH ON EXCEL DATA (customer_tickets.xlsx)")
    print("Imagine an IT helpdesk or engineering support team querying historical spreadsheets")
    print("by describing a runtime error or production outage.\n")

    incident_queries = [
        "WAL archiving disk space ran out causing database failover",
        "container terminated because memory ceiling was reached during batch job"
    ]

    for q in incident_queries:
        print(f"-> SYMPTOM DESCRIPTION: \"{q}\"")
        matches = search_tickets(q, top_k=1)
        for m in matches:
            print(f"   MATCHED TICKET: [{m['Ticket ID']}] {m['Title']}")
            print(f"   DEPARTMENT    : {m['Department']} | PRIORITY: {m['Priority']} | SIMILARITY: {m['Similarity']}")
            print(f"   RESOLUTION    : {m['Resolution']}\n")

    # Step 5: Vector Index Under the Hood (HNSW vs Sequential Scan)
    print_header("PHASE 5: UNDER THE HOOD: HNSW VECTOR INDEX SCAN EXECUTION PLAN")
    print("Running EXPLAIN (ANALYZE, BUFFERS) on PostgreSQL:")
    plan = explain_vector_query("noise cancelling audio")
    print(plan)
    print("\nExplanation:")
    print("1. 'Index Scan using products_hnsw_idx': PostgreSQL traverses the multi-layer HNSW graph")
    print("   rather than scanning all table rows sequentially (O(N) -> O(log N)).")
    print("2. '<=>' operator calculates cosine distance: Distance = 1 - CosineSimilarity.")
    print("3. Ordered by distance ASC to retrieve the nearest neighbor vectors first.")

    print_header("DEMO SUMMARY")
    print("All tasks completed successfully!")
    print("You can explore interactively by running:")
    print("  python -m pgvector_poc.query")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
