import sqlite3
import time
import os

DB_PATH = "test_benchmark.db"

def setup_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.isolation_level = None
    cursor = conn.cursor()
    cursor.execute("BEGIN TRANSACTION;")
    cursor.execute('''
        CREATE TABLE embeddings (
            id INTEGER PRIMARY KEY,
            dispositivo_id INTEGER,
            vetor BLOB,
            modelo TEXT
        )
    ''')
    conn.commit()
    return conn

def benchmark_execute(conn, num_records):
    cursor = conn.cursor()
    cursor.execute("BEGIN TRANSACTION;")
    data = [(i, b'mock_vector_data_which_is_bytes', "bge-m3") for i in range(num_records)]

    start = time.time()
    for disp_id, vetor, modelo in data:
        cursor.execute(
            """
            INSERT INTO embeddings (dispositivo_id, vetor, modelo)
            VALUES (?, ?, ?)
            """,
            (disp_id, vetor, modelo)
        )
    conn.commit()
    return time.time() - start

def benchmark_executemany(conn, num_records):
    cursor = conn.cursor()
    cursor.execute("BEGIN TRANSACTION;")
    data = [(i, b'mock_vector_data_which_is_bytes', "bge-m3") for i in range(num_records)]

    start = time.time()
    cursor.executemany(
        """
        INSERT INTO embeddings (dispositivo_id, vetor, modelo)
        VALUES (?, ?, ?)
        """,
        data
    )
    conn.commit()
    return time.time() - start

conn1 = setup_db()
time_execute = benchmark_execute(conn1, 10000)
conn1.close()

conn2 = setup_db()
time_executemany = benchmark_executemany(conn2, 10000)
conn2.close()

print(f"cursor.execute loop time: {time_execute:.4f}s")
print(f"cursor.executemany time: {time_executemany:.4f}s")
if time_execute > 0:
    improvement = ((time_execute - time_executemany) / time_execute) * 100
    print(f"Improvement: {improvement:.2f}%")
