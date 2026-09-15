from backend.app.core.database import DestSessionLocal
from backend.app.models.models import MapeoSubcategoria, Company
from backend.app.api.endpoints.mapeo import migrate_to_final
from sqlalchemy import text

# Subcategorías de entidades (cbdmauxi → cg_entitrib)
entidades_subcats = [55, 56, 57, 58, 125]

# Empresas con sus IDs (basado en categorías de subcategorías de entidades)
empresas = {
    '002': 1,  # Botica Magistral (subcats 56, 58)
    '004': 7,  # GRUPO YLV (subcat 125)
    '005': 3,  # INDUSTRIAS
    '007': 4,  # YELAVE NATURE (subcats 55, 57)
}

def re_migrate_entidades_por_empresa(company_id, codcia):
    """Re-migra entidades para una empresa específica con validación UTF-8."""
    db = DestSessionLocal()
    
    try:
        print(f"\n=== Re-migrando entidades para empresa {codcia} (company_id: {company_id}) ===")
        
        # Obtener subcategorías de entidades
        subcats = db.query(MapeoSubcategoria).filter(
            MapeoSubcategoria.id.in_(entidades_subcats),
            MapeoSubcategoria.is_active == True
        ).all()
        
        print(f"Subcategorías encontradas: {len(subcats)}")
        
        for sub in subcats:
            print(f"\nProcesando subcategoría: {sub.nombre} (ID: {sub.id})")
            print(f"  Tabla origen: {sub.tabla_origen}")
            print(f"  Tabla destino: {sub.tabla_destino_detalle}")
            print(f"  Filtros: {sub.filter_rules}")
            
            # Verificar si esta subcategoría aplica para esta empresa
            if sub.filter_rules:
                applies = False
                for rule in sub.filter_rules:
                    if rule.get('column') == 'codcia' and rule.get('value') == codcia:
                        applies = True
                        break
                    elif rule.get('column') == 'T_filtro' and rule.get('value') == '2':
                        applies = True
                
                if not applies:
                    print(f"  → Omitido: filtros no aplican para empresa {codcia}")
                    continue
            
            # Ejecutar migración final con allow_overwrite=True
            try:
                result = migrate_to_final(
                    company_id=company_id,
                    subcategoria_id=sub.id,
                    allow_overwrite=True,
                    db=db
                )
                print(f"  → Resultado: {result}")
            except Exception as e:
                print(f"  → Error: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"\n=== Re-migración completada para empresa {codcia} ===")
        
    except Exception as e:
        print(f"Error general: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("=== RE-MIGRACIÓN DE ENTIDADES CON VALIDACIÓN UTF-8 ===\n")
    
    # Preguntar qué empresa migrar
    print("Empresas disponibles:")
    for codcia, company_id in empresas.items():
        print(f"  {codcia}: company_id = {company_id}")
    
    # Migrar todas las empresas
    for codcia, company_id in empresas.items():
        re_migrate_entidades_por_empresa(company_id, codcia)
    
    print("\n=== RE-MIGRACIÓN COMPLETADA PARA TODAS LAS EMPRESAS ===")
