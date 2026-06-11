"""
REPROCESAR: 200-Cancelacion Documentos -Cajas - Botica Magistral
Periodo: 2026-06

Este script:
1. Elimina de Contasis final (cf_diario + cf_diariol) para ccodori='200', periodo 2026-06
2. Resetea el staging local para que se pueda volver a generar y migrar
3. Resetea el correlativo para 2026-06
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from sqlalchemy import create_engine, text

LOCAL_DB = "postgresql://postgres:postgres@localhost:5434/migconta_db"
CONTASIS_DB = "postgresql://postgres:postgres@192.168.2.90:5432/contasis_003"

COMPANY_ID = 1
SUBCAT_ID = 43
CCODORI = '200'
CPER = '2026'
CMES = '06'

def main():
    local_engine = create_engine(LOCAL_DB)
    contasis_engine = create_engine(CONTASIS_DB)
    
    # === PASO 1: Limpiar Contasis final para 2026-06 ===
    print("=== PASO 1: Limpiando Contasis final (2026-06, ccodori=200) ===")
    with contasis_engine.begin() as conn:
        # Contar antes
        h_antes = conn.execute(text(
            "SELECT count(*) FROM cf_diario WHERE ccodori = :ori AND cper = :cper AND cmes = :cmes"
        ), {"ori": CCODORI, "cper": CPER, "cmes": CMES}).scalar()
        d_antes = conn.execute(text(
            "SELECT count(*) FROM cf_diariol WHERE ccodori = :ori AND cper = :cper AND cmes = :cmes"
        ), {"ori": CCODORI, "cper": CPER, "cmes": CMES}).scalar()
        print(f"  Antes - Cabeceras: {h_antes}, Detalles: {d_antes}")
        
        # Eliminar detalles primero
        del_d = conn.execute(text(
            "DELETE FROM cf_diariol WHERE ccodori = :ori AND cper = :cper AND cmes = :cmes"
        ), {"ori": CCODORI, "cper": CPER, "cmes": CMES})
        print(f"  Eliminados {del_d.rowcount} detalles de cf_diariol")
        
        # Eliminar cabeceras
        del_h = conn.execute(text(
            "DELETE FROM cf_diario WHERE ccodori = :ori AND cper = :cper AND cmes = :cmes"
        ), {"ori": CCODORI, "cper": CPER, "cmes": CMES})
        print(f"  Eliminados {del_h.rowcount} cabeceras de cf_diario")
        
        # Verificar
        h_desp = conn.execute(text(
            "SELECT count(*) FROM cf_diario WHERE ccodori = :ori AND cper = :cper AND cmes = :cmes"
        ), {"ori": CCODORI, "cper": CPER, "cmes": CMES}).scalar()
        d_desp = conn.execute(text(
            "SELECT count(*) FROM cf_diariol WHERE ccodori = :ori AND cper = :cper AND cmes = :cmes"
        ), {"ori": CCODORI, "cper": CPER, "cmes": CMES}).scalar()
        print(f"  Despues - Cabeceras: {h_desp}, Detalles: {d_desp}")
    
    # === PASO 2: Resetear staging local para 2026-06 ===
    print("\n=== PASO 2: Reseteando staging local (2026-06, subcat 43) ===")
    with local_engine.begin() as conn:
        # Contar antes
        h_loc = conn.execute(text("""
            SELECT count(*) FROM cf_diario 
            WHERE company_id = :cid AND subcategoria_id = :sid AND cper = :cper AND cmes = :cmes
        """), {"cid": COMPANY_ID, "sid": SUBCAT_ID, "cper": CPER, "cmes": CMES}).scalar()
        d_loc = conn.execute(text("""
            SELECT count(*) FROM cf_diariol 
            WHERE company_id = :cid AND subcategoria_id = :sid AND cper = :cper AND cmes = :cmes
        """), {"cid": COMPANY_ID, "sid": SUBCAT_ID, "cper": CPER, "cmes": CMES}).scalar()
        print(f"  Antes - Cabeceras local: {h_loc}, Detalles local: {d_loc}")
        
        # Eliminar detalles locales de 2026-06
        del_d_loc = conn.execute(text("""
            DELETE FROM cf_diariol 
            WHERE company_id = :cid AND subcategoria_id = :sid AND cper = :cper AND cmes = :cmes
        """), {"cid": COMPANY_ID, "sid": SUBCAT_ID, "cper": CPER, "cmes": CMES})
        print(f"  Eliminados {del_d_loc.rowcount} detalles locales")
        
        # Eliminar cabeceras locales de 2026-06
        del_h_loc = conn.execute(text("""
            DELETE FROM cf_diario 
            WHERE company_id = :cid AND subcategoria_id = :sid AND cper = :cper AND cmes = :cmes
        """), {"cid": COMPANY_ID, "sid": SUBCAT_ID, "cper": CPER, "cmes": CMES})
        print(f"  Eliminados {del_h_loc.rowcount} cabeceras locales")
    
    # === PASO 3: Resetear correlativo para 2026-06 ===
    print("\n=== PASO 3: Reseteando correlativo para 2026-06 ===")
    with local_engine.begin() as conn:
        corr = conn.execute(text("""
            SELECT id, asiento_inicial, asiento_actual 
            FROM asiento_correlativos
            WHERE company_id = :cid AND subcategoria_id = :sid AND periodo = :cper AND mes = :cmes
        """), {"cid": COMPANY_ID, "sid": SUBCAT_ID, "cper": CPER, "cmes": CMES}).mappings().first()
        
        if corr:
            print(f"  Correlativo actual: inicial={corr['asiento_inicial']}, actual={corr['asiento_actual']}")
            # Resetear asiento_actual al valor inicial - 1 para que empiece de nuevo
            conn.execute(text("""
                UPDATE asiento_correlativos 
                SET asiento_actual = asiento_inicial - 1
                WHERE id = :id
            """), {"id": corr['id']})
            print(f"  Reseteado a asiento_actual = {corr['asiento_inicial'] - 1}")
        else:
            print("  No se encontro correlativo para 2026-06 (se creara automaticamente)")
        
        # Tambien resetear el control incremental (last_generated_control_value)
        # para que vuelva a leer las filas de 2026-06
        conn.execute(text("""
            UPDATE mapeo_subcategorias SET last_generated_control_value = NULL WHERE id = :sid
        """), {"sid": SUBCAT_ID})
        print("  Reseteado last_generated_control_value = NULL")
    
    # === PASO 4: Verificacion final ===
    print("\n=== PASO 4: Verificacion final ===")
    with local_engine.connect() as conn:
        h_final = conn.execute(text("""
            SELECT count(*) FROM cf_diario 
            WHERE company_id = :cid AND subcategoria_id = :sid AND cper = :cper AND cmes = :cmes
        """), {"cid": COMPANY_ID, "sid": SUBCAT_ID, "cper": CPER, "cmes": CMES}).scalar()
        d_final = conn.execute(text("""
            SELECT count(*) FROM cf_diariol 
            WHERE company_id = :cid AND subcategoria_id = :sid AND cper = :cper AND cmes = :cmes
        """), {"cid": COMPANY_ID, "sid": SUBCAT_ID, "cper": CPER, "cmes": CMES}).scalar()
        print(f"  Local staging 2026-06: cabeceras={h_final}, detalles={d_final}")
    
    with contasis_engine.connect() as conn:
        h_cont = conn.execute(text(
            "SELECT count(*) FROM cf_diario WHERE ccodori = :ori AND cper = :cper AND cmes = :cmes"
        ), {"ori": CCODORI, "cper": CPER, "cmes": CMES}).scalar()
        d_cont = conn.execute(text(
            "SELECT count(*) FROM cf_diariol WHERE ccodori = :ori AND cper = :cper AND cmes = :cmes"
        ), {"ori": CCODORI, "cper": CPER, "cmes": CMES}).scalar()
        print(f"  Contasis 2026-06: cabeceras={h_cont}, detalles={d_cont}")

    print("\n=== LISTO! ===")
    print("Ahora puedes reprocesar desde la interfaz:")
    print("  1. Ir a http://localhost:8080/companies/1")
    print("  2. Paso 2: Generar Asientos -> Seleccionar subcategoria '200-Cancelacion'")
    print("  3. Paso 3: Migrar a Contasis")
    print("  O desde http://localhost:8080/etl-realtime (el ETL automatico lo hara solo)")

if __name__ == "__main__":
    main()
