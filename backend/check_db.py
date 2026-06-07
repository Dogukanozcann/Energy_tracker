import sqlite3

conn = sqlite3.connect("C:/Users/dogukan.ozcan/Desktop/energy_tracker/backend/energy_tracker.db")
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
print("Tables:")
for t in tables:
    print(f"  {t[0]}")
print()
for t in tables:
    count = conn.execute(f"SELECT COUNT(*) FROM [{t[0]}]").fetchone()[0]
    print(f"  {t[0]}: {count} rows")
conn.close()
