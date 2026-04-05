## 2024-03-22 - N+1 Issue Fix for PDF Chunks database inserts

**Learning:** When ingesting a large number of text chunks into an SQLite database during the ETL pipeline, using individual `cursor.execute` calls inside a loop creates significant N+1 query overhead.
**Action:** Replace sequential `cursor.execute` iterations with a single `cursor.executemany` using list comprehensions to batch prepare the parameterized tuples, leading to a massive speedup (~27% faster just in parsing and basic I/O).

## 2024-03-22 - Python Loop Bottleneck in Retrieval Vector Filtering

**Learning:** Filtering lists of metadata dictionaries using string manipulations inside Python list comprehensions (e.g., `[m["tipo"].lower() in list]`) during RAG retrieval creates a significant $O(N)$ CPU bottleneck on every query.
**Action:** Move the lowercase transformation to the vector load phase (`_carregar_vetores`), cache the results in a dedicated NumPy array (e.g., `_TIPOS_CACHE`), and use the highly optimized vectorized `np.isin()` function for real-time query filtering, which yields a ~10x speedup in mask generation.
## 2026-03-27 - Streamlit DataFrame Instantiation Overhead
**Learning:** In Streamlit dashboards, multiple sequential `pd.read_sql` calls or loops to gather database statistics cause severe N+1 query latency, largely dominated by Pandas DataFrame instantiation overhead rather than just DB round-trips.
**Action:** Always combine and batch database statistics into a single SQL query (using subselects or `GROUP BY` with an `IN` clause) and process the resulting single DataFrame to minimize latency.

## 2024-05-27 - Streamlit N+1 Query in Search Results Loop
**Learning:** In Streamlit dashboards, iterating over search results (`df_resultado.iterrows()`) and rendering an expander for each item that triggers a separate database query (e.g., `buscar_norma_detalhes(row["id"])`) causes severe N+1 latency. The sequential queries block rendering.
**Action:** Extract all IDs from the search results, execute a single batched SQL query using an `IN` clause to fetch all details simultaneously, and filter the resulting DataFrame in memory during the loop iteration.

## 2026-03-27 - Deferred Join with CTE in Paginated SQLite Searches
**Learning:** In SQLite paginated search queries that involve heavy LEFT JOINs across large tables (like `dispositivos` and `versoes_norma`), joining the tables *before* applying `WHERE`, `ORDER BY`, and `LIMIT` forces the engine to process combinations that are ultimately discarded.
**Action:** Extract the initial filtering (`WHERE`), ordering (`ORDER BY`), and `LIMIT` on the root table (`normas`) into a Common Table Expression (CTE) to create a subset. Then perform the JOIN operations only on this subset, yielding substantial performance improvements (typically >1.5x) while reducing computational overhead.
## 2025-05-24 - [Lazy Loading ML Dependencies]
**Learning:** Importing heavy ML dependencies like `sentence_transformers` or `torch` at the top level of a module causes massive performance penalties during application startup, even if the code path using them isn't hit immediately.
**Action:** Always utilize the lazy loading pattern for these libraries, importing them directly inside the initialization functions (e.g., `carregar_modelo()`) so main global imports remain fast.

## 2024-05-28 - Pandas DataFrame Iteration Bottleneck
**Learning:** In Python data applications, iterating over Pandas DataFrames using `iterrows()` yields a Series for each row and carries significant overhead, severely blocking thread execution and reducing UI responsiveness.
**Action:** For optimal performance when iterating over Pandas DataFrames, always replace `iterrows()` loops with `itertuples()`, which returns fast namedtuples instead of Series objects.
