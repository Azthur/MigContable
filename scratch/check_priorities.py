import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="migconta_db",
    user="migconta",
    password="migconta"
)
cur = conn.cursor()

# Get table_selection_id for CcbRRdoc company 1
cur.execute("SELECT id FROM table_selections WHERE LOWER(table_name)='ccbrrdoc' AND company_id=1")
row = cur.fetchone()
if not row:
    print("No table selection found for CcbRRdoc company 1")
    conn.close()
    exit()

ts_id = row[0]
print(f"Table selection ID: {ts_id}")

cur.execute("""
    SELECT priority, new_column_name, source_column, condition_value, default_value
    FROM computed_column_rules 
    WHERE table_selection_id = %s AND is_active = true
    ORDER BY priority
""", (ts_id,))

rows = cur.fetchall()
print(f"\nTotal rules: {len(rows)}\n")
print(f"{'Pri':>3} | {'New Column':<25} | {'Source Col':<15} | {'Formula/Condition':<80} | Default")
print("-" * 160)
for r in rows:
    formula = r[3][:80] if r[3] else ""
    print(f"{r[0]:3d} | {r[1]:<25} | {(r[2] or ''):<15} | {formula:<80} | {r[4] or ''}")

conn.close()
