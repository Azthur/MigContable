import psycopg2

conn = psycopg2.connect('postgresql://postgres:postgres@db:5432/migconta_db')
conn.autocommit = True
cur = conn.cursor()
cur.execute("SELECT sequence_name FROM information_schema.sequences WHERE sequence_schema = 'public'")
sequences = [row[0] for row in cur.fetchall()]

for seq in sequences:
    table_name = seq.replace('_id_seq', '').replace('_seq', '')
    try:
        # Some sequence names might not perfectly match the table, but this works for most standard ones
        cur.execute(f"SELECT max(id) FROM {table_name}")
        max_id = cur.fetchone()[0] or 1
        cur.execute(f"SELECT setval('{seq}', {max_id})")
        print(f"Sync {seq} for {table_name} to {max_id}")
    except Exception as e:
        print(f"Skipping {seq}: {e}")
