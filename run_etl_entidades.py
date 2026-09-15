from backend.app.core.database import DestSessionLocal
from backend.app.api.endpoints.etl import run_incremental_etl
from backend.app.api.endpoints.mapeo import generate_to_cf_diariol, migrate_to_final
from backend.app.models.models import TableSelection, MapeoSubcategoria, MapeoCategoria

# Empresas con sus IDs
empresas = {
    '002': 1,  # Botica Magistral
    '004': 7,  # GRUPO YLV
    '005': 3,  # INDUSTRIAS
    '007': 4,  # YELAVE NATURE
}

# Subcategorías de entidades
entidades_subcats = [55, 56, 57, 58, 125]

def run_etl_for_entidades(company_id, codcia):
    """Ejecuta ETL completo para entidades de una empresa."""
    print(f"\n=== ETL COMPLETO PARA ENTIDADES - Empresa {codcia} (company_id: {company_id}) ===")
    
    db = DestSessionLocal()
    
    try:
        # Paso 1: Ejecutar ETL incremental para tablas origen (cbdmauxi)
        print("Paso 1: Extracción de SQL Server → migconta_db")
        
        # Obtener selecciones de tabla para cbdmauxi
        selections = db.query(TableSelection).filter(
            TableSelection.company_id == company_id,
            TableSelection.table_name.ilike('%auxi%'),
            TableSelection.is_selected == True
        ).all()
        
        if not selections:
            print(f"  ✗ No hay tablas seleccionadas para entidades en empresa {codcia}")
            return False
        
        print(f"  Tablas seleccionadas: {len(selections)}")
        for sel in selections:
            print(f"    - {sel.table_name}")
            
            # Ejecutar ETL incremental con full_refresh para re-extracción con encoding UTF-8
            result = run_incremental_etl(company_id, sel.id, db, start_date=None, end_date=None, full_refresh=True)
            print(f"    Resultado: {result.get('message', 'OK')}")
        
        # Paso 2: Generar en staging (cg_entitrib con estado='1')
        print("\nPaso 2: Generación en staging")
        
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
        
        # Paso 3: Migrar a Contasis final
        print("\nPaso 3: Migración a Contasis final")
        
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
    print("=== ETL COMPLETO PARA ENTIDADES CON VALIDACIÓN UTF-8 ===\n")
    
    # Ejecutar para cada empresa
    for codcia, company_id in empresas.items():
        success = run_etl_for_entidades(company_id, codcia)
        if success:
            print(f"\n✓ Empresa {codcia} procesada exitosamente")
        else:
            print(f"\n✗ Empresa {codcia} falló")
    
    print("\n=== ETL COMPLETO FINALIZADO ===")
