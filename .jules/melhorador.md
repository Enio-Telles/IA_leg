## 2024-05-20 - Batch Insert vs Individual Insert Latency
**Learning:** SQLite database loops using `cursor.execute` in data pipelines (such as ETL processes for document parsing and embedding persistence) create an N+1 query latency issue, scaling linearly with data size and slowing ingestion speeds.
**Action:** Always prefer array aggregation and `cursor.executemany` for database writes involving lists or data processing output blocks in `etl/` and `rag/` modules.
