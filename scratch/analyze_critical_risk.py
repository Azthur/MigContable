"""
ANALISIS CRITICO: Verificar que las "colisiones" en staging local
NO causan problemas en Contasis final, porque cada empresa va a BD diferente.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from sqlalchemy import create_engine, text

LOCAL_DB = "postgresql://postgres:postgres@localhost:5434/migconta_db"

def main():
    engine = create_engine(LOCAL_DB)
    
    with engine.connect() as conn:
        print("=" * 80)
        print("ANALISIS CRITICO: Seguridad del aislamiento")
        print("=" * 80)
        
        # PUNTO CLAVE: En staging local, las colisiones (mismo cper/cmes/ccodori/nasiento 
        # entre subcategorias) NO son problema porque:
        # 1. En local, cada registro tiene company_id + subcategoria_id
        # 2. En Contasis final, cada empresa va a su propia BD
        
        # PERO: El overwrite DELETE en migrate_to_final usa:
        # WHERE cper=X AND cmes=Y AND ccodori=Z AND nasiento=N
        # (SIN company_id porque Contasis no tiene ese campo!)
        
        # Esto es SEGURO porque cada empresa va a BD DIFERENTE.
        # PERO seria PELIGROSO si 2 subcategorias de la MISMA empresa
        # usan el mismo ccodori Y coinciden en nasiento.
        
        print("\n=== VERIFICACION CRITICA: Dentro de MISMA empresa, ===")
        print("=== mismo ccodori, hay colision de nasiento? ===\n")
        
        for company_id_val, company_name in [(1, "BOTICA"), (4, "YLV IND"), (5, "YLV NAT"), (6, "CORPO")]:
            # Get subcategorias with their ccodori
            subcats = conn.execute(text("""
                SELECT s.id, s.nombre, 
                       l.mapeo_detalle->>'ccodori' as ccodori
                FROM mapeo_subcategorias s
                JOIN mapeo_categorias c ON s.categoria_id = c.id
                JOIN mapeo_lineas_asiento l ON l.subcategoria_id = s.id AND l.is_active = true
                WHERE c.company_id = :cid AND s.is_active = true
                AND l.mapeo_detalle->>'ccodori' IS NOT NULL
                GROUP BY s.id, s.nombre, l.mapeo_detalle->>'ccodori'
            """), {"cid": company_id_val}).fetchall()
            
            # Group by ccodori within same company
            from collections import defaultdict
            ccodori_groups = defaultdict(list)
            for s in subcats:
                ccodori_val = s[2].strip().strip('"').strip("'") if s[2] else None
                if ccodori_val:
                    ccodori_groups[ccodori_val].append((s[0], s[1]))
            
            has_risk = False
            for ccodori, subs_list in ccodori_groups.items():
                if len(subs_list) > 1:
                    has_risk = True
                    print(f"  RIESGO en {company_name} (ID={company_id_val}):")
                    print(f"    ccodori='{ccodori}' usado por {len(subs_list)} subcategorias:")
                    for sid, sname in subs_list:
                        print(f"      - {sname} (ID={sid})")
                    
                    # Check if they actually have overlapping nasiento values
                    if len(subs_list) == 2:
                        s1, s2 = subs_list[0][0], subs_list[1][0]
                        overlap = conn.execute(text("""
                            SELECT count(*) FROM (
                                SELECT DISTINCT cper, cmes, nasiento FROM cf_diariol
                                WHERE company_id = :cid AND subcategoria_id = :s1
                                INTERSECT
                                SELECT DISTINCT cper, cmes, nasiento FROM cf_diariol
                                WHERE company_id = :cid AND subcategoria_id = :s2
                            ) x
                        """), {"cid": company_id_val, "s1": s1, "s2": s2}).scalar()
                        if overlap > 0:
                            print(f"      >>> PELIGRO: {overlap} nasientos coinciden!")
                        else:
                            print(f"      OK: No hay nasientos coincidentes")
            
            if not has_risk:
                print(f"  OK {company_name}: Cada subcategoria usa ccodori diferente")
        
        # Now check: does the migrate_to_final properly filter by subcategoria_id 
        # when querying LOCAL staging?
        print("\n" + "=" * 80)
        print("VERIFICACION: migrate_to_final filtra por subcategoria_id?")
        print("=" * 80)
        print("""
  SI - La funcion migrate_to_final filtra local staging asi:
    LocalDetTable.select().where(
        LocalDetTable.c.company_id == company_id,      <-- FILTRO
        LocalDetTable.c.estado == target_estado,        <-- FILTRO 
        LocalDetTable.c.subcategoria_id == sub.id       <-- FILTRO
    )
  
  Esto significa que SOLO toma los registros de ESA subcategoria.
  Luego los inserta en Contasis SIN company_id ni subcategoria_id
  (porque Contasis no tiene esos campos).
  
  PERO: Si 2 subcategorias de la MISMA empresa generan asientos
  con el MISMO ccodori y el MISMO nasiento, al migrar ambos
  intentarian insertar el mismo (cper, cmes, ccodori, nasiento)
  en Contasis, lo que causaria un DUPLICADO o ERROR.
""")
        
        # Check the actual state in each Contasis DB
        print("=" * 80)
        print("ESTADO ACTUAL EN CADA BD CONTASIS")
        print("=" * 80)
        
        dbs = {
            1: ("192.168.2.90", 5432, "contasis_003", "BOTICA"),
            4: ("192.168.2.90", 5432, "contasis_005", "YLV IND"),
            5: ("192.168.2.90", 5432, "contasis_002", "YLV NAT"),
            6: ("192.168.2.90", 5432, "contasis_004", "CORPO"),
        }
        
        for cid, (host, port, dbname, label) in dbs.items():
            try:
                ce = create_engine(f"postgresql://postgres:postgres@{host}:{port}/{dbname}")
                with ce.connect() as cc:
                    # Check for duplicate (cper, cmes, ccodori, nasiento) in cf_diariol
                    dupes = cc.execute(text("""
                        SELECT cper, cmes, ccodori, nasiento, count(*) as cnt
                        FROM cf_diario
                        GROUP BY cper, cmes, ccodori, nasiento
                        HAVING count(*) > 1
                        LIMIT 5
                    """)).fetchall()
                    
                    if dupes:
                        print(f"\n  ALERTA {label} ({dbname}): Hay cabeceras duplicadas!")
                        for d in dupes[:3]:
                            print(f"    {d[0]}-{d[1]} ccodori={d[2]} nasiento={d[3]}: {d[4]} duplicados")
                    else:
                        total_h = cc.execute(text("SELECT count(*) FROM cf_diario")).scalar()
                        total_d = cc.execute(text("SELECT count(*) FROM cf_diariol")).scalar()
                        print(f"  OK {label} ({dbname}): {total_h} cabeceras, {total_d} detalles, SIN duplicados")
            except Exception as ex:
                print(f"  ERROR conectando a {label} ({dbname}): {ex}")

if __name__ == "__main__":
    main()
