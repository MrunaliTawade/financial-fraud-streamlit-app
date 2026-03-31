import sqlite3

conn = sqlite3.connect("transactions.db", check_same_thread=False)
cursor = conn.cursor()

# Create table
cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    txn_id TEXT,
    amount REAL,
    type INTEGER,
    oldbalanceOrg REAL,
    newbalanceOrig REAL,
    oldbalanceDest REAL,
    newbalanceDest REAL,
    isFlaggedFraud INTEGER,
    prediction TEXT
)
""")

conn.commit()


def insert_transaction(data):
    cursor.execute("""
    INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, data)
    conn.commit()