# PostgreSQL + pgvector: CSV & Excel Semantic Search POC

A complete Proof of Concept (POC) demonstrating how **Vector Indexing** works in **PostgreSQL** using the **pgvector** extension, and how to ingest, index, and semantically query data from **CSV** and **Excel (.xlsx)** files using **Python** and **Docker**.

---

## Table of Contents
1. [Core Concepts: How a Vector Index Works](#1-core-concepts-how-a-vector-index-works)
   - [Embeddings: What Are They?](#embeddings-what-are-they)
   - [Distance Metrics (Cosine, L2, Inner Product)](#distance-metrics)
   - [The Scalability Problem: Flat Search vs. ANN](#the-scalability-problem-flat-search-vs-ann)
   - [HNSW (Hierarchical Navigable Small World) Deep-Dive](#hnsw-hierarchical-navigable-small-world-deep-dive)
   - [HNSW vs. IVFFlat Comparison](#hnsw-vs-ivfflat-comparison)
2. [Indexing CSV & Excel (Tabular Data)](#2-indexing-csv--excel-tabular-data)
   - [The Strategy: Entity Representation](#the-strategy-entity-representation)
   - [PostgreSQL Dual-Model Schema](#postgresql-dual-model-schema)
3. [Architecture of this POC](#3-architecture-of-this-poc)
4. [Prerequisites](#4-prerequisites)
5. [Quickstart (Choose Option A or B)](#5-quickstart)
   - [Option A: 100% Dockerized (Zero Local Installs)](#option-a-100-dockerized-zero-local-installs)
   - [Option B: Hybrid (Docker Postgres + Local Python)](#option-b-hybrid-docker-postgres--local-python)
6. [Interactive Exploration & Query CLI](#6-interactive-exploration--query-cli)
7. [Under the Hood: EXPLAIN ANALYZE Execution Plans](#7-under-the-hood-explain-analyze-execution-plans)
8. [File Structure](#8-file-structure)

---

## 1. Core Concepts: How a Vector Index Works

### Embeddings: What Are They?
An **embedding** is a dense numerical vector (a list of floating-point numbers, e.g. 384 dimensions) that captures the semantic meaning of a piece of text. 

* Semantically similar texts are placed **close together** in this 384-dimensional hyperspace.
* Dissimilar texts are placed **far apart**.

```
"wireless noise-cancelling headphones"  ───► [ 0.041, -0.128,  0.892, ..., -0.015 ]
"quiet audio earcups for airplane"       ───► [ 0.039, -0.119,  0.885, ..., -0.021 ]  (Very Close!)
"non-stick cast iron frying pan"        ───► [-0.512,  0.640, -0.081, ...,  0.312 ]  (Far Away!)
```

### Distance Metrics
To measure the "distance" or similarity between two vectors $u$ and $v$:

| Metric | Formula | pgvector Operator | Best Used For |
| :--- | :--- | :--- | :--- |
| **Cosine Distance** | $1 - \frac{u \cdot v}{\|u\| \|v\|}$ | `<=>` | Text & NLP embeddings (angles matter more than magnitude) |
| **L2 Distance (Euclidean)** | $\sqrt{\sum (u_i - v_i)^2}$ | `<->` | Coordinate/spatial data, image features |
| **Inner Product (Negative)** | $-(u \cdot v)$ | `<#>` | Normalized vectors (fastest cosine equivalent) |

In pgvector, Cosine Similarity is:
$$\text{Cosine Similarity} = 1 - (\text{embedding} \Leftrightarrow \text{query\_vector})$$
* Returns `1.0` for identical vectors, `0.0` for orthogonal vectors.

---

### The Scalability Problem: Flat Search vs. ANN

Without an index, querying the nearest neighbors requires a **Sequential Scan (Flat / Brute-Force KNN)**:
1. Compute the distance between the query vector and **every single row** in the database table.
2. Time complexity is $O(N \cdot D)$ where $N$ is row count and $D$ is vector dimensions.
3. At $10^5$ to $10^7$ rows, sequential vector scans take seconds or minutes, exhausting CPU and memory bandwidth.

To solve this, we use **Approximate Nearest Neighbor (ANN)** indexes. They sacrifice an imperceptible amount of precision (e.g. 99% recall) for a $100\times$ - $1000\times$ speedup ($O(\log N)$).

---

### HNSW (Hierarchical Navigable Small World) Deep-Dive

**HNSW** is the state-of-the-art graph-based ANN index. It operates on the principle of a **multi-layer graph** (conceptually similar to a multi-level skip list):

```
Layer 2 (Top - Sparse)       [Node A] ------------------------------> [Node F]
                                 \                                      \
Layer 1 (Medium)             [Node A] ---------> [Node C] ---------> [Node F]
                                 \                 \                   \
Layer 0 (Bottom - Dense)     [Node A] -> [Node B] -> [Node C] -> [Node D] -> [Node E] -> [Node F]
```

#### How Search Traversal Works:
1. **Entry**: The search starts at an entry point in the highest (sparsest) layer.
2. **Greedy Routing**: It calculates distance to neighbors and greedily jumps to the neighbor closest to the query vector.
3. **Layer Transition**: When no closer neighbor exists in the current layer, the algorithm drops down to the corresponding node in the next denser layer.
4. **Target Acquisition**: Once at Layer 0 (which contains all vectors), it explores localized neighbors within a candidate pool (`ef_search`) and returns the top-$K$ closest matches.

#### HNSW Configuration Parameters:
* `m`: Maximum number of bidirectional links per node (e.g., 16). Higher values increase recall and index build time.
* `ef_construction`: Size of the dynamic candidate list evaluated during index construction (e.g., 64). Higher values produce a higher quality graph at the cost of slower build.

```sql
CREATE INDEX products_hnsw_idx ON products 
USING hnsw (embedding vector_cosine_ops) 
WITH (m = 16, ef_construction = 64);
```

---

### HNSW vs. IVFFlat Comparison

| Feature | HNSW (Recommended) | IVFFlat |
| :--- | :--- | :--- |
| **Data Structure** | Multi-layer proximity graph | Inverted File (Voronoi cell clustering) |
| **Training Required?** | **No** (can build on empty tables) | **Yes** (must train clusters on existing data) |
| **Search Speed** | Extremely fast ($O(\log N)$) | Fast, but drops if `probes` increases |
| **Recall / Quality** | Excellent (typically >98%) | Good, but sensitive to cluster distribution |
| **Memory Footprint** | Higher (stores graph edges) | Low (only stores centroids and lists) |
| **Build Time** | Moderate to Slow | Very Fast |

---

## 2. Indexing CSV & Excel (Tabular Data)

### The Strategy: Entity Representation
Spreadsheets contain structured columns (numeric, categorical) and unstructured text:

```csv
sku,name,category,price,rating,description,stock
AUD-001,AcousticPro QuietComfort,Audio,199.99,4.8,Active noise cancelling wireless Bluetooth...,45
```

If we only embedded the `description`, a search for *"Audio under $200"* would miss the category context. If we embedded each cell separately, we would lose row-level relationships.

**The Solution:**
Synthesize each row into a structured **semantic document representation** before vectorization:

```python
search_text = (
    f"Product: {row['name']} | "
    f"Category: {row['category']} | "
    f"Price: ${row['price']} | "
    f"Rating: {row['rating']}/5.0 | "
    f"Description: {row['description']}"
)
```

### PostgreSQL Dual-Model Schema
PostgreSQL stores both the raw relational columns **and** the vector:

```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    sku VARCHAR(50) UNIQUE,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    price NUMERIC(10, 2) NOT NULL,
    rating NUMERIC(3, 1),
    description TEXT NOT NULL,
    stock INT,
    search_text TEXT,
    embedding vector(384)       -- pgvector 384-dimensional vector column
);
```

**Why this is superior to pure vector databases:**
In pure vector DBs, applying relational filters (`price < 100`) often requires external post-filtering or complex payloads. 
In PostgreSQL, you execute **true Hybrid Search in a single query**:

```sql
SELECT sku, name, category, price,
       1 - (embedding <=> %s) AS similarity
FROM products
WHERE price <= 100.00 AND category = 'Audio'
ORDER BY embedding <=> %s
LIMIT 5;
```

---

## 3. Architecture of this POC

```mermaid
flowchart LR
    subgraph InputFiles ["1. Tabular Data Files"]
        CSV["sample_data/products.csv"]
        XLSX["sample_data/customer_tickets.xlsx"]
    end

    subgraph PythonPipeline ["2. Python Ingestion Engine"]
        Pandas["Pandas & OpenPyXL"]
        TextPrep["Row Template Serializer"]
        ST["SentenceTransformers\n(all-MiniLM-L6-v2)"]
    end

    subgraph PostgresDB ["3. PostgreSQL (pgvector/pgvector:pg16)"]
        TableProd["Table: products\n(Structured Cols + embedding)"]
        TableTick["Table: customer_tickets\n(Structured Cols + embedding)"]
        HNSW["HNSW Graph Index\n(vector_cosine_ops)"]
        BTree["B-Tree Indexes\n(price, category, priority)"]
    end

    subgraph QueryLayer ["4. Query Engine (query.py)"]
        NaturalQuery["Natural Language Query"]
        QueryVec["Query Embedding"]
        HybridSQL["SQL: ORDER BY embedding <=> query_vec\nWHERE relational_filters"]
        Results["Top-K Ranked Results with Similarity"]
    end

    CSV --> Pandas
    XLSX --> Pandas
    Pandas --> TextPrep
    TextPrep --> ST
    ST -->|384-dim float[]| TableProd
    ST -->|384-dim float[]| TableTick
    TableProd --> HNSW
    TableTick --> HNSW
    TableProd --> BTree

    NaturalQuery --> QueryVec
    QueryVec --> HybridSQL
    HNSW --> HybridSQL
    BTree --> HybridSQL
    HybridSQL --> Results
```

---

## 4. Prerequisites
* **Docker & Docker Compose** (Installed and running)
* *(Optional)* Python 3.10+ (if running Python locally instead of in Docker)

---

## 5. Quickstart

### Option A: 100% Dockerized (Zero Local Installs)

1. **Clone or navigate to the repository directory:**
   ```bash
   cd /home/spc/Desktop/pgvector-csv-excel-poc
   ```

2. **Spin up Postgres and run the end-to-end automated demo:**
   ```bash
   docker compose up --build
   ```
   * This starts PostgreSQL with `pgvector`.
   * Automatically generates `products.csv` and `customer_tickets.xlsx`.
   * Generates embeddings, creates HNSW indexes, runs 5 semantic test scenarios, and prints `EXPLAIN ANALYZE` execution plans.

3. **Run the interactive query CLI inside Docker:**
   ```bash
   docker compose run --rm app python query.py
   ```

---

### Option B: Hybrid (Docker Postgres + Local Python)

1. **Start PostgreSQL with pgvector:**
   ```bash
   cd /home/spc/Desktop/pgvector-csv-excel-poc
   docker compose up -d db
   ```

2. **Set up local Python virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Generate sample files & ingest data into PostgreSQL:**
   ```bash
   python generate_data.py
   python ingest.py
   ```

4. **Run the automated walkthrough:**
   ```bash
   python demo.py
   ```

---

## 6. Interactive Exploration & Query CLI

Run `python query.py` (or `docker compose run --rm app python query.py`):

```text
============================================================
  PGVECTOR INTERACTIVE QUERY CONSOLE
============================================================
Options:
  1: Search Products (from CSV)
  2: Hybrid Filtered Search Products (e.g. price filter + semantic query)
  3: Search IT Support Incidents & Resolutions (from Excel)
  4: Show Query Execution Plan (EXPLAIN ANALYZE HNSW)
  q: Exit
============================================================
```

### Example Test Queries:
* **Product Search (Zero keyword overlap):**
  * Query: `"comfortable silence for long airline flight"`
  * *Result: Matches `AcousticPro QuietComfort Over-Ear Headphones` with 0.68+ similarity.*
* **Hybrid Search:**
  * Query: `"muscle strength weights"`
  * Filter: `price <= 100`, Category: `Fitness`
  * *Result: Filters out $310 dumbbells and recommends affordable fitness equipment.*
* **Excel IT Incident Search:**
  * Query: `"system disk ran out of space during log archive"`
  * *Result: Pulls `INC-1001` (WAL archiving root partition full) and prints exact resolution commands.*

---

## 7. Under the Hood: EXPLAIN ANALYZE Execution Plans

When running `explain_vector_query()`, PostgreSQL outputs the actual index traversal:

```text
Limit  (cost=12.25..12.35 rows=3 width=44) (actual time=0.082..0.085 rows=3 loops=1)
  Buffers: shared hit=4
  ->  Index Scan using products_hnsw_idx on products  (cost=12.25..15.50 rows=15 width=44) (actual time=0.081..0.084 rows=3 loops=1)
        Order By: (embedding <=> '[0.041, -0.012, ...]'::vector)
        Buffers: shared hit=4
Planning Time: 0.124 ms
Execution Time: 0.115 ms
```

**Key Takeaways:**
1. **`Index Scan using products_hnsw_idx`**: Confirms that PostgreSQL traverses the HNSW graph rather than performing a slow sequential scan.
2. **`Buffers: shared hit=4`**: Only 4 page buffers inspected to locate the top matches.
3. **`Execution Time: 0.115 ms`**: Sub-millisecond vector similarity search directly inside SQL.

---

## 8. File Structure

```
pgvector-csv-excel-poc/
├── docker-compose.yml          # Postgres + pgvector and App service definitions
├── Dockerfile                  # Container definition with pre-cached embedding model
├── requirements.txt            # Python dependencies (pgvector, sentence-transformers, pandas, etc.)
├── config.py                   # DB connection parameters & model configurations
├── generate_data.py            # Generates realistic CSV and Excel sample datasets
├── db.py                       # PostgreSQL connection, extension, and HNSW index management
├── embedder.py                 # SentenceTransformer vectorizer & row-to-text serializes
├── ingest.py                   # CSV & XLSX ingestion, vector generation, and UPSERT logic
├── query.py                    # Semantic, hybrid, and EXPLAIN query functions + Interactive CLI
├── demo.py                     # Full end-to-end automated demonstration
├── sample_data/                # Auto-generated CSV and Excel datasets
│   ├── products.csv
│   └── customer_tickets.xlsx
└── README.md                   # Comprehensive guide and documentation
```
