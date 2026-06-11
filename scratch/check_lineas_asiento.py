"""
Check lineas de asiento (accounting line mappings) for subcategory 43.
"""
from sqlalchemy import create_engine, text

LOCAL_DB = "postgresql://postgres:postgres@localhost:5434/migconta_db"

def main():
    engine = create_engine(LOCAL_DB)
    
    with engine.connect() as conn:
        print("=== LINEAS DE ASIENTO for subcat 43 ===")
        lineas = conn.execute(text("""
            SELECT id, orden, nombre, nivel, condicion_aplicacion, 
                   aplica_ajuste_redondeo, is_active,
                   LEFT(mapeo_detalle::text, 500) as mapeo_preview
            FROM mapeo_lineas_asiento
            WHERE subcategoria_id = 43
            ORDER BY orden
        """)).mappings().all()
        for l in lineas:
            print(f"\n  Linea ID={l['id']}, orden={l['orden']}, nombre={l['nombre']}")
            print(f"    nivel={l['nivel']}, active={l['is_active']}")
            print(f"    condicion_aplicacion={l['condicion_aplicacion']}")
            print(f"    aplica_ajuste_redondeo={l['aplica_ajuste_redondeo']}")
            print(f"    mapeo (preview): {l['mapeo_preview']}")

        # Also check the source table for the subcategory
        print("\n=== SUBCATEGORY 43 CONFIG ===")
        sub = conn.execute(text("""
            SELECT id, nombre, tabla_origen, clave_asiento, 
                   tabla_destino_cabecera, tabla_destino_detalle,
                   col_destino_nasiento, col_destino_nidlin,
                   control_column_origen, last_generated_control_value,
                   col_origen_periodo, col_origen_mes,
                   LEFT(filter_rules::text, 500) as filter_preview,
                   LEFT(mapeo_cabecera::text, 500) as cabecera_preview,
                   generate_headers
            FROM mapeo_subcategorias
            WHERE id = 43
        """)).mappings().first()
        if sub:
            for k, v in sub.items():
                print(f"  {k}: {v}")

if __name__ == "__main__":
    main()
