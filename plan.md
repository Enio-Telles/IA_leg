1. **Optimize `carregar_estatisticas` in `dashboard/app.py`**
   - Replace the multiple `pd.read_sql` queries with a single batched query to reduce N+1 query overhead and Pandas initialization time.
2. **Optimize `carregar_stats_jurisprudencia` in `dashboard/app.py`**
   - Replace the loop of 8 `pd.read_sql` queries (2 per category) with a single query using `GROUP BY` and an `IN` clause to fetch and process all jurisprudence stats in one database round-trip.
3. **Journal critical learnings**
   - Update `.jules/bolt.md` to document the performance bottleneck of repeated `pd.read_sql` calls inside Streamlit dashboards, and how to combine them into a single batched SQL query to minimize DB round-trips and DataFrame instantiation latency.
4. **Complete pre-commit steps to ensure proper testing, verification, review, and reflection are done.**
   - Run linter and any relevant tests.
5. **Submit the PR**
   - Submit the changes using the CLI with standard Bolt formats.
