## 2024-03-22 - [O(1) Indexed max retrieval instead of O(N) full scan on unindexed columns]
**Learning:** SQLite MAX() over an unindexed datetime column causes a full table scan. Using ORDER BY id DESC LIMIT 1 leverages the AUTOINCREMENT PK index for an O(1) retrieval.
**Action:** Prefer sorting by ID DESC LIMIT 1 over MAX() on unindexed time columns to retrieve the latest record.
