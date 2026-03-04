import psycopg2

def check_db(name, url):
    try:
        conn = psycopg2.connect(url)
        cur = conn.cursor()
        for t in ["mapeo_categorias", "mapeo_subcategorias", "mapeo_lineas_asiento"]:
            cur.execute(f"SELECT count(1) FROM {t}")
            print(f"{name} - {t}: {cur.fetchone()[0]}")
    except Exception as e:
        print(f"{name} Error:", e)

check_db("Source (Windows)", "postgresql://postgres:postgres@host.docker.internal:5433/migconta_db")
check_db("Dest (Docker)", "postgresql://postgres:postgres@db:5432/migconta_db")
