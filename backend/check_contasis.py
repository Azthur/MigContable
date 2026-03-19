import psycopg2

try:
    conn = psycopg2.connect("dbname='micont_db' user='postgres' password='migconta2024*' host='localhost'")
    cur = conn.cursor()
    
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='cf_diariol' AND column_name='idcontrol'")
    print("cf_diariol idcontrol:", cur.fetchall())
    
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='cf_diario' AND column_name='idcontrol'")
    print("cf_diario idcontrol:", cur.fetchall())
    
except Exception as e:
    print("Error:", e)
