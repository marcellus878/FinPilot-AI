import os
import sqlite3
from app.core.database import Base
import app.models  # load all models

print("--- SQLALCHEMY MODELS IN CODE ---")
for table_name, table in Base.metadata.tables.items():
    print(f"\nModel Table: {table_name}")
    for col in table.columns:
        print(f"  {col.name} ({col.type}) [nullable={col.nullable}, default={col.default}]")

print("\n--- ACTUAL SQLITE DATABASE (finpilot.db) ---")
if os.path.exists("finpilot.db"):
    conn = sqlite3.connect("finpilot.db")
    cur = conn.cursor()
    tables = cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    for (tbl,) in tables:
        if tbl == "sqlite_sequence":
            continue
        cols = cur.execute(f"PRAGMA table_info('{tbl}')").fetchall()
        print(f"\nDatabase Table: {tbl}")
        for col in cols:
            print(f"  {col[1]} ({col[2]}) [notnull={col[3]}, dflt={col[4]}]")
    conn.close()
else:
    print("finpilot.db does not exist.")
