"""
ANALISIS COMPLETO: Riesgo de cruce de datos entre subcategorias y empresas.
Verifica:
1. Tablas origen compartidas
2. Tablas destino compartidas
3. Columnas calculadas compartidas
4. Filtros de aislamiento (company_id, subcategoria_id)
5. Correlativos de asiento - riesgo de colision
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from sqlalchemy import create_engine, text
from collections import defaultdict

LOCAL_DB = "postgresql://postgres:postgres@localhost:5434/migconta_db"

def main():
    engine = create_engine(LOCAL_DB)
    
    with engine.connect() as conn:
        # 1. Obtener TODAS las subcategorias activas con sus configuraciones
        print("=" * 80)
        print("ANALISIS DE RIESGO: CRUCE DE DATOS ENTRE SUBCATEGORIAS")
        print("=" * 80)
        
        subs = conn.execute(text("""
            SELECT s.id, s.nombre, s.tabla_origen, s.tabla_destino_cabecera, 
                   s.tabla_destino_detalle, s.clave_asiento, s.col_destino_nasiento,
                   s.generate_headers, s.is_active,
                   c.company_id, comp.name as empresa,
                   s.filter_rules::text as filter_rules,
                   s.control_column_origen
            FROM mapeo_subcategorias s
            JOIN mapeo_categorias c ON s.categoria_id = c.id
            JOIN companies comp ON c.company_id = comp.id
            WHERE s.is_active = true
            ORDER BY c.company_id, s.nombre
        """)).mappings().all()
        
        print(f"\nTotal subcategorias activas: {len(subs)}")
        
        # 2. Agrupar por tabla_origen
        print("\n" + "=" * 80)
        print("1. TABLAS ORIGEN COMPARTIDAS")
        print("=" * 80)
        por_tabla_origen = defaultdict(list)
        for s in subs:
            por_tabla_origen[s['tabla_origen']].append(s)
        
        for tabla, subcats in por_tabla_origen.items():
            if len(subcats) > 1:
                print(f"\n  TABLA ORIGEN: {tabla}")
                print(f"  Compartida por {len(subcats)} subcategorias:")
                for sc in subcats:
                    print(f"    - [{sc['empresa']}] {sc['nombre']} (ID={sc['id']}, company={sc['company_id']})")
                    print(f"      clave_asiento={sc['clave_asiento']}")
                    print(f"      control_col={sc['control_column_origen']}")
                    # Parse filter rules briefly
                    fr = sc['filter_rules'] or '[]'
                    if fr != '[]':
                        print(f"      filtros={fr[:200]}")
        
        # 3. Agrupar por tabla_destino
        print("\n" + "=" * 80)
        print("2. TABLAS DESTINO COMPARTIDAS")
        print("=" * 80)
        por_tabla_dest = defaultdict(list)
        for s in subs:
            det = s['tabla_destino_detalle'] or 'cf_diariol'
            cab = s['tabla_destino_cabecera'] or 'cf_diario'
            por_tabla_dest[f"{cab}/{det}"].append(s)
        
        for tabla, subcats in por_tabla_dest.items():
            print(f"\n  TABLA DESTINO: {tabla}")
            print(f"  Compartida por {len(subcats)} subcategorias:")
            for sc in subcats:
                print(f"    - [{sc['empresa']}] {sc['nombre']} (ID={sc['id']}, company={sc['company_id']})")
        
        # 4. Verificar que los datos en staging estan correctamente aislados
        print("\n" + "=" * 80)
        print("3. AISLAMIENTO EN STAGING LOCAL (cf_diario/cf_diariol)")
        print("=" * 80)
        
        # Check cf_diariol: cada registro tiene company_id Y subcategoria_id?
        null_company = conn.execute(text(
            "SELECT count(*) FROM cf_diariol WHERE company_id IS NULL"
        )).scalar()
        null_subcat = conn.execute(text(
            "SELECT count(*) FROM cf_diariol WHERE subcategoria_id IS NULL"
        )).scalar()
        print(f"\n  cf_diariol: registros sin company_id={null_company}, sin subcategoria_id={null_subcat}")
        
        null_company_h = conn.execute(text(
            "SELECT count(*) FROM cf_diario WHERE company_id IS NULL"
        )).scalar()
        null_subcat_h = conn.execute(text(
            "SELECT count(*) FROM cf_diario WHERE subcategoria_id IS NULL"
        )).scalar()
        print(f"  cf_diario: registros sin company_id={null_company_h}, sin subcategoria_id={null_subcat_h}")
        
        # 5. Verificar que NO hay cruces: un mismo (cper, cmes, ccodori, nasiento) 
        # pertenece a multiples subcategorias
        print("\n" + "=" * 80)
        print("4. RIESGO DE COLISION: Mismo asiento en multiples subcategorias")
        print("=" * 80)
        
        collisions_det = conn.execute(text("""
            SELECT cper, cmes, ccodori, nasiento, 
                   count(DISTINCT subcategoria_id) as num_subcats,
                   array_agg(DISTINCT subcategoria_id) as subcats,
                   count(DISTINCT company_id) as num_companies
            FROM cf_diariol
            WHERE cper IS NOT NULL AND cmes IS NOT NULL
            GROUP BY cper, cmes, ccodori, nasiento
            HAVING count(DISTINCT subcategoria_id) > 1
            LIMIT 10
        """)).fetchall()
        
        if collisions_det:
            print(f"\n  ALERTA! {len(collisions_det)} colisiones en cf_diariol:")
            for c in collisions_det:
                print(f"    cper={c[0]}, cmes={c[1]}, ccodori={c[2]}, nasiento={c[3]}")
                print(f"      subcategorias={c[5]}, companies={c[6]}")
        else:
            print("\n  OK: No hay colisiones en cf_diariol (cada asiento pertenece a una sola subcategoria)")
        
        # 6. Verificar ccodori - que subcategorias usan el mismo ccodori
        print("\n" + "=" * 80)
        print("5. CCODORI COMPARTIDO (Codigo de Origen en Contasis)")
        print("=" * 80)
        
        ccodori_map = defaultdict(list)
        for s in subs:
            # Get ccodori from lineas
            lineas = conn.execute(text("""
                SELECT DISTINCT mapeo_detalle->>'ccodori' as ccodori
                FROM mapeo_lineas_asiento
                WHERE subcategoria_id = :sid AND is_active = true
                AND mapeo_detalle->>'ccodori' IS NOT NULL
            """), {"sid": s['id']}).fetchall()
            for l in lineas:
                if l[0]:
                    ccodori_val = l[0].strip().strip('"').strip("'")
                    ccodori_map[ccodori_val].append(s)
        
        for ccodori, subcats in ccodori_map.items():
            if len(subcats) > 1:
                print(f"\n  ccodori='{ccodori}' compartido por {len(subcats)} subcategorias:")
                for sc in subcats:
                    print(f"    - [{sc['empresa']}] {sc['nombre']} (company={sc['company_id']})")
                
                # RIESGO: Si 2+ subcategorias de la MISMA empresa usan el mismo ccodori
                companies_with_ccodori = defaultdict(list)
                for sc in subcats:
                    companies_with_ccodori[sc['company_id']].append(sc)
                
                for cid, company_subcats in companies_with_ccodori.items():
                    if len(company_subcats) > 1:
                        print(f"    >>> RIESGO: Company {cid} tiene {len(company_subcats)} subcats con ccodori='{ccodori}'")
            else:
                empresa = subcats[0]['empresa'] if subcats else '?'
                print(f"  ccodori='{ccodori}': Solo [{empresa}] {subcats[0]['nombre']}")
        
        # 7. Verificar correlativos - riesgo de numeracion duplicada
        print("\n" + "=" * 80)
        print("6. CORRELATIVOS: Verificar que no hay duplicacion de nasiento")
        print("=" * 80)
        
        # Check per company: do different subcategories share nasiento numbering?
        for company_id_val in [1, 4, 5, 6]:
            company_name = next((s['empresa'] for s in subs if s['company_id'] == company_id_val), '?')
            dupe_seats = conn.execute(text("""
                SELECT cper, cmes, nasiento, 
                       count(DISTINCT subcategoria_id) as num_subcats,
                       array_agg(DISTINCT subcategoria_id) as subcats
                FROM cf_diariol
                WHERE company_id = :cid AND cper IS NOT NULL
                GROUP BY cper, cmes, nasiento
                HAVING count(DISTINCT subcategoria_id) > 1
                LIMIT 5
            """), {"cid": company_id_val}).fetchall()
            
            if dupe_seats:
                print(f"\n  ALERTA {company_name} (ID={company_id_val}):")
                print(f"    Hay {len(dupe_seats)} nasientos compartidos entre subcategorias")
                for d in dupe_seats[:3]:
                    print(f"    {d[0]}-{d[1]} nasiento={d[2]}: subcats={d[4]}")
            else:
                print(f"  OK {company_name} (ID={company_id_val}): Sin colision de nasiento")
        
        # 8. Conexiones destino final por empresa
        print("\n" + "=" * 80)
        print("7. CONEXIONES DESTINO FINAL (cada empresa -> su propia BD Contasis)")
        print("=" * 80)
        
        finals = conn.execute(text("""
            SELECT f.company_id, comp.name, f.host, f.port, f.database_name, f.is_active
            FROM final_dest_connections f
            JOIN companies comp ON f.company_id = comp.id
            WHERE f.is_active = true
            ORDER BY f.company_id
        """)).mappings().all()
        
        for f in finals:
            print(f"  Company {f['company_id']} [{f['name']}] -> {f['host']}:{f['port']}/{f['database_name']}")
        
        # Check: do different companies point to SAME database?
        db_map = defaultdict(list)
        for f in finals:
            key = f"{f['host']}:{f['port']}/{f['database_name']}"
            db_map[key].append(f)
        
        for db_key, companies in db_map.items():
            if len(companies) > 1:
                print(f"\n  ALERTA: Base {db_key} compartida por:")
                for c in companies:
                    print(f"    - Company {c['company_id']} [{c['name']}]")
            
        print("\n" + "=" * 80)
        print("RESUMEN")
        print("=" * 80)

if __name__ == "__main__":
    main()
