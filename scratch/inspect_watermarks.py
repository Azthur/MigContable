"""
Inspect MapeoSubcategoria watermarks and filter rules for CORPORACION YLV S.A.C.
to understand why only the current month (June 2026) is being processed.
"""
from sqlalchemy import create_engine, text
import json

engine = create_engine("postgresql://postgres:postgres@localhost:5434/migconta_db")

with engine.connect() as conn:
    # 1. Find the company
    print("=" * 80)
    print("1. EMPRESAS")
    print("=" * 80)
    rows = conn.execute(text("SELECT id, name FROM companies WHERE name ILIKE '%CORPO%'")).fetchall()
    for r in rows:
        print(f"  ID={r[0]}, Name={r[1]}")
    
    if not rows:
        print("  No companies matching 'CORPO' found!")
        exit()
    
    company_id = rows[0][0]
    
    # 2. Get subcategorias for this company
    print("\n" + "=" * 80)
    print(f"2. SUBCATEGORIAS for company_id={company_id}")
    print("=" * 80)
    subcats = conn.execute(text("""
        SELECT ms.id, ms.nombre, ms.tabla_origen, 
               ms.last_generated_control_value, ms.control_column_origen,
               ms.filter_rules, ms.is_active,
               ms.col_origen_periodo, ms.col_origen_mes
        FROM mapeo_subcategorias ms
        JOIN mapeo_categorias mc ON ms.categoria_id = mc.id
        WHERE mc.company_id = :cid
        ORDER BY ms.id
    """), {"cid": company_id}).fetchall()
    
    for s in subcats:
        print(f"\n  Sub ID={s[0]}: {s[1]}")
        print(f"    tabla_origen: {s[2]}")
        print(f"    last_generated_control_value: {s[3]}")
        print(f"    control_column_origen: {s[4]}")
        print(f"    is_active: {s[6]}")
        print(f"    col_origen_periodo: {s[7]}")
        print(f"    col_origen_mes: {s[8]}")
        if s[5]:
            print(f"    filter_rules: {json.dumps(s[5], indent=6, ensure_ascii=False)}")
        else:
            print(f"    filter_rules: None")
    
    # 3. Check the AsientoCorrelativo (period configs)
    print("\n" + "=" * 80)
    print(f"3. ASIENTO CORRELATIVOS for company_id={company_id}")
    print("=" * 80)
    
    # Find the subcategoria for '200-Cancelacion'
    subcat_200 = None
    for s in subcats:
        if '200' in str(s[1]):
            subcat_200 = s[0]
            break
    
    if subcat_200:
        corrs = conn.execute(text("""
            SELECT id, subcategoria_id, periodo, mes, asiento_actual, asiento_inicial
            FROM asiento_correlativos
            WHERE company_id = :cid AND subcategoria_id = :sid
            ORDER BY periodo, mes
        """), {"cid": company_id, "sid": subcat_200}).fetchall()
        
        print(f"\n  For subcategoria_id={subcat_200} (200-Cancelacion):")
        for c in corrs:
            print(f"    Periodo={c[2]}, Mes={c[3]}, actual={c[4]}, inicial={c[5]}")
    
    # 4. Check cf_diariol staging data counts by period
    print("\n" + "=" * 80)
    print(f"4. CF_DIARIOL STAGING counts by period for company_id={company_id}")
    print("=" * 80)
    
    try:
        staging_counts = conn.execute(text("""
            SELECT cper, cmes, subcategoria_id, estado, COUNT(*) as cnt
            FROM cf_diariol
            WHERE company_id = :cid
            GROUP BY cper, cmes, subcategoria_id, estado
            ORDER BY subcategoria_id, cper, cmes, estado
        """), {"cid": company_id}).fetchall()
        
        for sc in staging_counts:
            print(f"  Per={sc[0]}, Mes={sc[1]}, Sub={sc[2]}, Estado={sc[3]}, Count={sc[4]}")
    except Exception as e:
        print(f"  Error: {e}")

    # 5. Check the intermediate table data for 200-Cancelacion
    print("\n" + "=" * 80)
    print(f"5. INTERMEDIATE TABLE data for 200-Cancelacion")
    print("=" * 80)
    
    if subcat_200:
        # Get tabla_origen for this subcategoria
        tabla_info = conn.execute(text("""
            SELECT tabla_origen FROM mapeo_subcategorias WHERE id = :sid
        """), {"sid": subcat_200}).fetchone()
        
        if tabla_info and tabla_info[0]:
            tabla_name = tabla_info[0].lower().replace(" ", "_")
            try:
                # Check if table exists and count by period columns
                count_result = conn.execute(text(f"""
                    SELECT COUNT(*) FROM "{tabla_name}" WHERE company_id = :cid
                """), {"cid": company_id}).fetchone()
                print(f"  Total rows in '{tabla_name}' for company: {count_result[0]}")
                
                # Try to find period columns
                cols = conn.execute(text(f"""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = :tn
                    ORDER BY ordinal_position
                """), {"tn": tabla_name}).fetchall()
                col_names = [c[0] for c in cols]
                print(f"  Columns: {col_names[:20]}...")
                
                # Look for period-like columns
                period_cols = [c for c in col_names if any(p in c.lower() for p in ['per', 'mes', 'ano', 'fecha', 'date', 'periodo'])]
                print(f"  Period-like columns: {period_cols}")
                
            except Exception as e:
                print(f"  Error reading table '{tabla_name}': {e}")
