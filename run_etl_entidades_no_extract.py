from backend.app.core.database import DestSessionLocal
from backend.app.api.endpoints.mapeo import generate_to_cf_diariol, migrate_to_final
from backend.app.models.models import MapeoSubcategoria, MapeoCategoria

# Empresas con sus IDs
empresas = {
    '002': 1,  # Botica Magistral
    '004': 7,  # GRUPO YLV
    '005': 3,  # INDUSTRIAS
    '007': 4,  # YELAVE NATURE
}

# Subcategorías de entidades
entidades_subcats = [55, 56, 57, 58, 125]

def run_etl_for_entidades_no_extract(company_id, codcia):
    """Ejecuta ETL sin re-extracción (usa datos corregidos en cbdmauxi)."""
    print(f"\n=== ETL SIN RE-EXTRACCIÓN - Empresa {codcia} (company_id: {company_id}) ===")
    
    db = DestSessionLocal()
    
    try:
        # Paso 1: Generar en staging (cg_entitrib con estado='1')
        print("Paso 1: Generación en staging")
        
        # Obtener subcategorías de entidades para esta empresa
        subcats = db.query(MapeoSubcategoria).filter(
            MapeoSubcategoria.id.in_(entidades_subcats),
            MapeoSubcategoria.is_active == True
        ).all()
        
        for sub in subcats:
            # Verificar si la categoría pertenece a esta empresa
            categoria = db.query(MapeoCategoria).filter(MapeoCategoria.id == sub.categoria_id).first()
            if not categoria or categoria.company_id != company_id:
                print(f"  Omitiendo {sub.nombre} (categoría no pertenece a empresa {codcia})")
                continue
            
            print(f"  Generando: {sub.nombre}")
            
            try:
                result = generate_to_cf_diariol(
                    company_id=company_id,
                    subcategoria_id=sub.id,
                    db=db
                )
                print(f"    Resultado: {result.get('message', 'OK')}")
            except Exception as e:
                print(f"    Error: {e}")
        
        # Paso 2: Migrar a Contasis final
        print("\nPaso 2: Migración a Contasis final")
        
        for sub in subcats:
            categoria = db.query(MapeoCategoria).filter(MapeoCategoria.id == sub.categoria_id).first()
            if not categoria or categoria.company_id != company_id:
                continue
            
            print(f"  Migrando: {sub.nombre}")
            
            try:
                result = migrate_to_final(
                    company_id=company_id,
                    subcategoria_id=sub.id,
                    allow_overwrite=True,
                    db=db
                )
                print(f"    Resultado: {result.get('message', 'OK')}")
                print(f"    Migrados: {result.get('migrated_lineas', 0)} líneas, {result.get('migrated_cabeceras', 0)} cabeceras")
            except Exception as e:
                print(f"    Error: {e}")
        
        print(f"\n✓ ETL completado exitosamente para empresa {codcia}")
        return True
        
    except Exception as e:
        print(f"✗ Error en ETL: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("=== ETL SIN RE-EXTRACCIÓN - USA DATOS CORREGIDOS EN cbdmauxi ===\n")
    
    # Ejecutar para cada empresa
    for codcia, company_id in empresas.items():
        success = run_etl_for_entidades_no_extract(company_id, codcia)
        if success:
            print(f"\n✓ Empresa {codcia} procesada exitosamente")
        else:
            print(f"\n✗ Empresa {codcia} falló")
    
    print("\n=== ETL COMPLETO FINALIZADO ===")
