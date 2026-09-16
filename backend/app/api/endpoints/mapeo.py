"""
Endpoints para el módulo de Mapeo Contable:
- Categorías y Subcategorías de mapeo
- Líneas de asiento contable (parametrización)
- Generación de asientos
- Filtros de columna para ETL
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from backend.app.core.database import get_dest_db
from backend.app.models.models import (
    MapeoCategoria, MapeoSubcategoria, MapeoLineaAsiento,
    ColumnFilter, TableSelection, SourceConnection, MigrationControl,
    AsientoContableGenerado, ComputedColumnRule
)
from backend.app.core.io_monitor import track_io
from backend.app.core.encoding_fixer import fix_encoding
from pydantic import BaseModel
import re
import ast
import ast
from backend.app.schemas.company import (
    MapeoCategoriaCreate, MapeoCategoriaSchema,
    MapeoSubcategoriaCreate, MapeoSubcategoriaSchema, MapeoSubcategoriaUpdate,
    MapeoLineaAsientoCreate, MapeoLineaAsientoSchema,
    ColumnFilterBulkUpdate, ColumnFilterSchema,
    MigrationControlSchema,
)

router = APIRouter()


# ─── Categorías de Mapeo ──────────────────────────────────────────────────────

@router.get("/categorias", response_model=List[MapeoCategoriaSchema])
def list_categorias(company_id: Optional[int] = None, db: Session = Depends(get_dest_db)):
    try:
        query = db.query(MapeoCategoria).filter(MapeoCategoria.is_active == True)
        if company_id:
            query = query.filter(MapeoCategoria.company_id == company_id)
        res = query.order_by(MapeoCategoria.nombre).all()
        return res

    except Exception as e:
        import traceback
        print("LIST_CATEGORIAS CRASH:", e)
        print(traceback.format_exc())
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/categorias/{cat_id}", response_model=MapeoCategoriaSchema)
def get_categoria(cat_id: int, db: Session = Depends(get_dest_db)):
    cat = db.query(MapeoCategoria).filter(MapeoCategoria.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return cat

@router.post("/categorias", response_model=MapeoCategoriaSchema)
def create_categoria(item: MapeoCategoriaCreate, db: Session = Depends(get_dest_db)):
    db_item = MapeoCategoria(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.put("/categorias/{cat_id}", response_model=MapeoCategoriaSchema)
def update_categoria(cat_id: int, item: MapeoCategoriaCreate, db: Session = Depends(get_dest_db)):
    db_item = db.query(MapeoCategoria).filter(MapeoCategoria.id == cat_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    for k, v in item.model_dump().items():
        setattr(db_item, k, v)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.delete("/categorias/{cat_id}")
def delete_categoria(cat_id: int, db: Session = Depends(get_dest_db)):
    db_item = db.query(MapeoCategoria).filter(MapeoCategoria.id == cat_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    db_item.is_active = False
    db.commit()
    return {"message": "Eliminado"}


# ─── Subcategorías de Mapeo ───────────────────────────────────────────────────

@router.get("/subcategorias", response_model=List[MapeoSubcategoriaSchema])
def list_subcategorias(categoria_id: Optional[int] = None, db: Session = Depends(get_dest_db)):
    query = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.is_active == True)
    if categoria_id:
        query = query.filter(MapeoSubcategoria.categoria_id == categoria_id)
    return query.order_by(MapeoSubcategoria.nombre).all()

@router.get("/subcategorias/{sub_id}", response_model=MapeoSubcategoriaSchema)
def get_subcategoria(sub_id: int, db: Session = Depends(get_dest_db)):
    sub = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subcategoría no encontrada")
    return sub

@router.post("/subcategorias", response_model=MapeoSubcategoriaSchema)
def create_subcategoria(item: MapeoSubcategoriaCreate, db: Session = Depends(get_dest_db)):
    db_item = MapeoSubcategoria(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.put("/subcategorias/{sub_id}", response_model=MapeoSubcategoriaSchema)
def update_subcategoria(sub_id: int, item: MapeoSubcategoriaUpdate, db: Session = Depends(get_dest_db)):
    db_item = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.id == sub_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Subcategoría no encontrada")
    dumped_data = item.model_dump(exclude_unset=True)
    print(f"DEBUG update_subcategoria payload: {dumped_data}")
    import sys
    sys.stdout.flush()
    for k, v in dumped_data.items():
        setattr(db_item, k, v)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.delete("/subcategorias/{sub_id}")
def delete_subcategoria(sub_id: int, db: Session = Depends(get_dest_db)):
    db_item = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.id == sub_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Subcategoría no encontrada")
    db_item.is_active = False
    db.commit()
    return {"message": "Eliminado"}

@router.post("/subcategorias/{sub_id}/toggle")
def toggle_subcategoria(sub_id: int, db: Session = Depends(get_dest_db)):
    db_item = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.id == sub_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Subcategoría no encontrada")
    db_item.is_active = not db_item.is_active
    db.commit()
    return {"message": "Estado actualizado", "is_active": db_item.is_active}

@router.post("/subcategorias/{sub_id}/duplicate", response_model=MapeoSubcategoriaSchema)
def duplicate_subcategoria(sub_id: int, db: Session = Depends(get_dest_db)):
    """Duplica una subcategoría entera con sus líneas de asiento y todos sus mapeos."""
    original = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.id == sub_id).first()
    if not original:
        raise HTTPException(status_code=404, detail="Subcategoría no encontrada")

    # Clonar la subcategoría básica
    new_sub = MapeoSubcategoria(
        categoria_id=original.categoria_id,
        nombre=f"{original.nombre} (Copia)",
        descripcion=original.descripcion,
        tabla_origen=original.tabla_origen,
        codigo_origen=original.codigo_origen,
        schema_destino=original.schema_destino,
        tabla_destino_detalle=original.tabla_destino_detalle,
        tabla_destino_cabecera=original.tabla_destino_cabecera,
        clave_asiento=original.clave_asiento,
        col_destino_nasiento=original.col_destino_nasiento,
        col_destino_nidlin=original.col_destino_nidlin,
        asiento_inicial=original.asiento_inicial,
        generate_headers=original.generate_headers,
        generate_details=original.generate_details,
        col_origen_periodo=original.col_origen_periodo,
        col_origen_mes=original.col_origen_mes,
        mapeo_cabecera=original.mapeo_cabecera.copy() if original.mapeo_cabecera else None,
        filter_rules=original.filter_rules.copy() if original.filter_rules else None,
        is_active=True
    )
    db.add(new_sub)
    db.flush() # Para obtener el ID de new_sub antes de las líneas

    # Clonar las líneas de asiento
    lineas = db.query(MapeoLineaAsiento).filter(
        MapeoLineaAsiento.subcategoria_id == sub_id,
        MapeoLineaAsiento.is_active == True
    ).order_by(MapeoLineaAsiento.orden).all()

    for linea in lineas:
        new_linea = MapeoLineaAsiento(
            subcategoria_id=new_sub.id,
            orden=linea.orden,
            nivel=linea.nivel,
            condicion_aplicacion=linea.condicion_aplicacion,
            nombre_linea=linea.nombre_linea,
            mapeo_detalle=linea.mapeo_detalle.copy() if linea.mapeo_detalle else None,
            is_active=True
        )
        db.add(new_linea)

    db.commit()
    db.refresh(new_sub)
    return new_sub


class CopyFromOtherCompanyRequest(BaseModel):
    source_sub_id: int
    target_categoria_id: int


@router.post("/subcategorias/copy-from-other-company", response_model=MapeoSubcategoriaSchema)
def copy_subcategoria_from_other_company(body: CopyFromOtherCompanyRequest, db: Session = Depends(get_dest_db)):
    """Copia una subcategoría de otra empresa hacia una categoría de la empresa actual."""
    original = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.id == body.source_sub_id).first()
    if not original:
        raise HTTPException(status_code=404, detail="Subcategoría origen no encontrada")

    # Verificar que la categoría destino existe
    target_cat = db.query(MapeoCategoria).filter(MapeoCategoria.id == body.target_categoria_id).first()
    if not target_cat:
        raise HTTPException(status_code=404, detail="Categoría destino no encontrada")

    # Obtener nombre de la empresa origen para el nombre de la copia
    source_cat = db.query(MapeoCategoria).filter(MapeoCategoria.id == original.categoria_id).first()
    from backend.app.models.models import Company
    source_company = db.query(Company).filter(Company.id == source_cat.company_id).first() if source_cat else None
    source_label = source_company.name if source_company else "Otra empresa"

    # Clonar la subcategoría
    new_sub = MapeoSubcategoria(
        categoria_id=body.target_categoria_id,
        nombre=f"{original.nombre} (de {source_label})",
        descripcion=original.descripcion,
        tabla_origen=original.tabla_origen,
        codigo_origen=original.codigo_origen,
        schema_destino=original.schema_destino,
        tabla_destino_detalle=original.tabla_destino_detalle,
        tabla_destino_cabecera=original.tabla_destino_cabecera,
        clave_asiento=original.clave_asiento,
        col_destino_nasiento=original.col_destino_nasiento,
        col_destino_nidlin=original.col_destino_nidlin,
        col_destino_debe=original.col_destino_debe,
        col_destino_haber=original.col_destino_haber,
        pares_redondeo=original.pares_redondeo.copy() if original.pares_redondeo else None,
        asiento_inicial=original.asiento_inicial,
        generate_headers=original.generate_headers,
        generate_details=original.generate_details,
        mapeo_cabecera=original.mapeo_cabecera.copy() if original.mapeo_cabecera else None,
        filter_rules=original.filter_rules.copy() if original.filter_rules else None,
        control_column_origen=original.control_column_origen,
        is_active=True
    )
    db.add(new_sub)
    db.flush()

    # Clonar las líneas de asiento
    lineas = db.query(MapeoLineaAsiento).filter(
        MapeoLineaAsiento.subcategoria_id == body.source_sub_id,
        MapeoLineaAsiento.is_active == True
    ).order_by(MapeoLineaAsiento.orden).all()

    for linea in lineas:
        new_linea = MapeoLineaAsiento(
            subcategoria_id=new_sub.id,
            orden=linea.orden,
            nivel=linea.nivel,
            condicion_aplicacion=linea.condicion_aplicacion,
            nombre_linea=linea.nombre_linea,
            aplica_ajuste_redondeo=linea.aplica_ajuste_redondeo,
            mapeo_detalle=linea.mapeo_detalle.copy() if linea.mapeo_detalle else None,
            is_active=True
        )
        db.add(new_linea)

    db.commit()
    db.refresh(new_sub)
    return new_sub


@router.get("/subcategorias-by-company/{company_id}")
def list_subcategorias_by_company(company_id: int, db: Session = Depends(get_dest_db)):
    """Lista todas las subcategorías de una empresa (para copiar desde otra empresa)."""
    cats = db.query(MapeoCategoria).filter(
        MapeoCategoria.company_id == company_id,
        MapeoCategoria.is_active == True
    ).all()
    result = []
    for cat in cats:
        subs = db.query(MapeoSubcategoria).filter(
            MapeoSubcategoria.categoria_id == cat.id,
            MapeoSubcategoria.is_active == True
        ).order_by(MapeoSubcategoria.nombre).all()
        for sub in subs:
            lineas_count = db.query(MapeoLineaAsiento).filter(
                MapeoLineaAsiento.subcategoria_id == sub.id,
                MapeoLineaAsiento.is_active == True
            ).count()
            result.append({
                "id": sub.id,
                "nombre": sub.nombre,
                "categoria_nombre": cat.nombre,
                "tabla_origen": sub.tabla_origen,
                "codigo_origen": sub.codigo_origen,
                "lineas_count": lineas_count
            })
    return result


# ─── Líneas de Asiento ────────────────────────────────────────────────────────

@router.get("/subcategorias/{sub_id}/lineas", response_model=List[MapeoLineaAsientoSchema])
def list_lineas(sub_id: int, db: Session = Depends(get_dest_db)):
    return db.query(MapeoLineaAsiento).filter(
        MapeoLineaAsiento.subcategoria_id == sub_id,
        MapeoLineaAsiento.is_active == True
    ).order_by(MapeoLineaAsiento.orden).all()

@router.post("/lineas-asiento", response_model=MapeoLineaAsientoSchema)
def create_linea(item: MapeoLineaAsientoCreate, db: Session = Depends(get_dest_db)):
    db_item = MapeoLineaAsiento(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.put("/lineas-asiento/{linea_id}", response_model=MapeoLineaAsientoSchema)
def update_linea(linea_id: int, item: MapeoLineaAsientoCreate, db: Session = Depends(get_dest_db)):
    db_item = db.query(MapeoLineaAsiento).filter(MapeoLineaAsiento.id == linea_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Línea no encontrada")
    for k, v in item.model_dump().items():
        setattr(db_item, k, v)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.delete("/lineas-asiento/{linea_id}")
def delete_linea(linea_id: int, db: Session = Depends(get_dest_db)):
    db_item = db.query(MapeoLineaAsiento).filter(MapeoLineaAsiento.id == linea_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Línea no encontrada")
    db_item.is_active = False
    db.commit()
    return {"message": "Eliminado"}


@router.get("/subcategorias/{sub_id}/helper-data")
def get_helper_data(sub_id: int, db: Session = Depends(get_dest_db)):
    """Devuelve datos de ayuda para el mapeo dinámico (columnas de origen y company_id)."""
    sub = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subcategoría no encontrada")
    
    cat = db.query(MapeoCategoria).filter(MapeoCategoria.id == sub.categoria_id).first()
    company_id = cat.company_id if cat else None

    columns = []
    if sub.tabla_origen:
        try:
            from sqlalchemy import text
            result = db.execute(text(f"SELECT * FROM {sub.tabla_origen} LIMIT 0"))
            columns = list(result.keys())
        except Exception as e:
            pass # Ignoramos errores si la tabla no existe aún

    suggested_control_column = None
    log_path = "c:\\SistemaMigConta\\backend\\helper_data_hit.log"
    with open(log_path, "a") as f:
        f.write(f"--- ENDPOINT START {sub_id} --- table={sub.tabla_origen}, company={company_id}\n")
        
    if sub.tabla_origen and company_id:
        try:

            from backend.app.models.models import TableSelection
            ts_list = db.query(TableSelection).filter(TableSelection.company_id == company_id).all()
            with open(log_path, "a") as f: f.write(f"Found {len(ts_list)} table selections\n")
            
            for ts in ts_list:
                if ts.table_name and sub.tabla_origen:
                    if ts.table_name.lower() in sub.tabla_origen.lower() or sub.tabla_origen.lower() in ts.table_name.lower():
                        if ts.control_column:
                            suggested_control_column = ts.control_column
                            with open(log_path, "a") as f: f.write(f"MATCH FOUND: {ts.table_name} -> {ts.control_column}\n")
                            break
        except Exception as e:
            with open(log_path, "a") as f: f.write(f"G_HELPER_DATA ERROR: {e}\n")
            pass



    return {
        "company_id": company_id,
        "columns": columns,
        "suggested_control_column": suggested_control_column
    }



@router.get("/subcategorias/{sub_id}/dest-columns")
def get_dest_columns_for_sub(sub_id: int, nivel: str = "DETALLE", db: Session = Depends(get_dest_db)):
    """
    Retorna las columnas de la tabla destino en Contasis (según la tabla configurada en la subcategoría).
    nivel=DETALLE  → usa sub.tabla_destino_detalle
    nivel=CABECERA → usa sub.tabla_destino_cabecera
    """
    from backend.app.models.models import FinalDestConnection
    from backend.app.services.connection_manager import ConnectionManager
    from sqlalchemy import text

    sub = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subcategoría no encontrada")

    cat = db.query(MapeoCategoria).filter(MapeoCategoria.id == sub.categoria_id).first()
    company_id = cat.company_id if cat else None

    final_conn = db.query(FinalDestConnection).filter(
        FinalDestConnection.company_id == company_id,
        FinalDestConnection.is_active == True
    ).first()
    if not final_conn:
        return {"table": None, "columns": [], "error": "No hay conexión final configurada"}

    # Usar tablas configuradas en la subcategoría (o fallback a cf_diariol/cf_diario)
    if nivel.upper() == "CABECERA":
        table_name = sub.tabla_destino_cabecera or "cf_diario"
    else:
        table_name = sub.tabla_destino_detalle or "cf_diariol"

    schema_name = sub.schema_destino or "public"

    if not table_name:
        return {"table": None, "columns": [], "error": "Tabla destino no configurada en la subcategoría"}

    try:
        conn_data = {
            "host": final_conn.host,
            "port": final_conn.port,
            "database_name": final_conn.database_name,
            "username": final_conn.username,
            "password": final_conn.password,
        }
        engine = ConnectionManager.get_dest_engine(conn_data)
        with engine.connect() as conn:
            # Buscar columnas en el schema configurado primero, luego en todos
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = :tname
                  AND (table_schema = :schema OR table_schema NOT IN ('information_schema', 'pg_catalog'))
                ORDER BY table_schema = :schema DESC, ordinal_position
            """), {"tname": table_name, "schema": schema_name})
            rows = result.fetchall()
            # Deduplicar por nombre de columna (prioriza el schema correcto)
            seen = set()
            cols = []
            for row in rows:
                if row[0] not in seen:
                    seen.add(row[0])
                    cols.append({"column_name": row[0], "data_type": row[1], "is_nullable": row[2]})

            # Fallback: query directo a la tabla
            if not cols:
                try:
                    r2 = conn.execute(text(f'SELECT * FROM "{schema_name}"."{table_name}" LIMIT 0'))
                    cols = [{"column_name": k, "data_type": "unknown", "is_nullable": "YES"} for k in r2.keys()]
                except Exception as e2:
                    print(f"DEST COLUMNS FALLBACK ERROR: {e2}")

        return {"table": table_name, "schema": schema_name, "columns": cols, "total": len(cols)}
    except Exception as e:
        print(f"DEST COLUMNS ERROR: {e}")
        return {"table": table_name, "columns": [], "error": str(e)}


@router.get("/final-tables")
def get_final_tables(company_id: int, db: Session = Depends(get_dest_db)):
    """
    Retorna las tablas seleccionadas del destino final Contasis para la empresa.
    Estas son las tablas que aparecen en el Paso 4 (Destino Final).
    """
    from backend.app.models.models import FinalTableSelection
    tables = db.query(FinalTableSelection).filter(
        FinalTableSelection.company_id == company_id,
        FinalTableSelection.is_selected == True
    ).order_by(FinalTableSelection.table_name).all()
    return [
        {
            "id": t.id,
            "table_name": t.table_name,
            "table_schema": t.table_schema,
            "description": t.description
        }
        for t in tables
    ]


# ─── Filtros de Columna ───────────────────────────────────────────────────────

@router.get("/table-selections/{selection_id}/filters", response_model=List[ColumnFilterSchema])
def get_column_filters(selection_id: int, db: Session = Depends(get_dest_db)):
    return db.query(ColumnFilter).filter(
        ColumnFilter.table_selection_id == selection_id,
        ColumnFilter.is_active == True
    ).all()

@router.post("/table-selections/{selection_id}/filters")
def save_column_filters(selection_id: int, bulk: ColumnFilterBulkUpdate, db: Session = Depends(get_dest_db)):
    """Guarda todos los filtros de una tabla (reemplaza los existentes)"""
    # Desactivar filtros anteriores
    db.query(ColumnFilter).filter(
        ColumnFilter.table_selection_id == selection_id
    ).update({"is_active": False})

    # Crear nuevos filtros activos
    for f in bulk.filters:
        if f.filter_value or f.operator in ("IS NULL", "IS NOT NULL"):
            db_filter = ColumnFilter(
                table_selection_id=selection_id,
                column_name=f.column_name,
                operator=f.operator,
                filter_value=f.filter_value,
                filter_value2=f.filter_value2,
                is_active=True
            )
            db.add(db_filter)

    db.commit()
    return {"message": "Filtros guardados correctamente"}

@router.post("/table-selections/{selection_id}/control-column")
def save_control_column(selection_id: int, body: dict, db: Session = Depends(get_dest_db)):
    """Guarda la columna de control incremental de una tabla"""
    sel = db.query(TableSelection).filter(TableSelection.id == selection_id).first()
    if not sel:
        raise HTTPException(status_code=404, detail="Selección no encontrada")
    old_col = sel.control_column
    new_col = body.get("control_column")
    
    sel.control_column = new_col
    sel.control_column_type = body.get("control_column_type", "DATE")
    
    # Si cambia la columna de control, resetear el control de migración
    if old_col != new_col:
        control = db.query(MigrationControl).filter(
            MigrationControl.company_id == sel.company_id,
            MigrationControl.source_table == sel.table_name
        ).first()
        if control:
            control.control_column = new_col
            control.last_migrated_value = None
            # control.total_migrated = 0  # Opcional: mantener histórico total o resetear
            
    db.commit()
    return {"message": "Columna de control guardada (y reiniciado incremental si cambió)"}


# ─── Columnas Calculadas (Condicionales) ──────────────────────────────────────

@router.get("/table-selections/by-company-and-table/computed-columns")
def get_computed_columns_by_company_and_table(company_id: int, table_name: str, db: Session = Depends(get_dest_db)):
    """Obtiene las reglas de columnas calculadas de una tabla espec\u00edfica en otra empresa"""
    sel = db.query(TableSelection).filter(
        TableSelection.company_id == company_id,
        TableSelection.table_name == table_name
    ).first()
    
    if not sel:
        return []
        
    rules = db.query(ComputedColumnRule).filter(
        ComputedColumnRule.table_selection_id == sel.id
    ).order_by(ComputedColumnRule.priority).all()
    
    return [{"id": None, "new_column_name": r.new_column_name,
             "source_column": r.source_column, "condition_value": r.condition_value,
             "result_value": r.result_value, "default_value": r.default_value,
             "priority": r.priority, "is_active": r.is_active} for r in rules]


@router.get("/table-selections/{selection_id}/computed-columns")
def get_computed_columns(selection_id: int, db: Session = Depends(get_dest_db)):
    """Obtiene las reglas de columnas calculadas de una tabla"""
    rules = db.query(ComputedColumnRule).filter(
        ComputedColumnRule.table_selection_id == selection_id
    ).order_by(ComputedColumnRule.priority).all()
    return [{"id": r.id, "new_column_name": r.new_column_name,
             "source_column": r.source_column, "condition_value": r.condition_value,
             "result_value": r.result_value, "default_value": r.default_value,
             "priority": r.priority, "is_active": r.is_active} for r in rules]
@router.post("/table-selections/{selection_id}/computed-columns")
def save_computed_columns(selection_id: int, body: dict, db: Session = Depends(get_dest_db)):
    """Guarda reglas de columnas calculadas (reemplaza todas las existentes)"""
    sel = db.query(TableSelection).filter(TableSelection.id == selection_id).first()
    if not sel:
        raise HTTPException(status_code=404, detail="Selección no encontrada")
    
    # Eliminar reglas existentes
    db.query(ComputedColumnRule).filter(
        ComputedColumnRule.table_selection_id == selection_id
    ).delete()
    
    # Crear nuevas reglas
    rules = body.get("rules", [])
    
    # 1. Validar la sintaxis de todas las reglas antes de afectarlas en DB
    for r in rules:
        cond = r.get("condition_value", "").strip()
        new_col = r.get("new_column_name", "").strip()
        if cond:
            # Preprocesamiento idéntico al que hace etl.py para AST
            formula_str = re.sub(r'["\']([^"\']+)["\'][\'"]+', r"'\1'", cond)
            formula_str = re.sub(r'[\'"]+([^"\']+)["\']', r"'\1'", formula_str)
            # Safe replacement of single '=' with '==' only outside string literals
            pattern = r"'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"|(?<![=<>!])=(?![=])"
            def repl(match):
                val = match.group(0)
                if val == '=':
                    return '=='
                return val
            formula_ast_str = re.sub(pattern, repl, formula_str)
            formula_ast_str = formula_ast_str.replace('<>', '!=')
            formula_ast_str = formula_ast_str.replace("SI.CONJUNTO", "SI_CONJUNTO")
            try:
                ast.parse(formula_ast_str, mode='eval')
            except SyntaxError as e:
                raise HTTPException(status_code=400, detail=f"Sintaxis inválida en la regla '{new_col}', revisa comas o paréntesis. Detalles: {e.msg}")
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error en la regla '{new_col}': {str(e)}")

    for i, r in enumerate(rules):
        new_rule = ComputedColumnRule(
            table_selection_id=selection_id,
            new_column_name=r.get("new_column_name", "").strip(),
            source_column=r.get("source_column", "").strip(),
            condition_value=r.get("condition_value", "").strip(),
            result_value=r.get("result_value", "").strip(),
            default_value=r.get("default_value", "").strip() if r.get("default_value") else None,
            priority=i,
            is_active=True
        )
        db.add(new_rule)
    
    db.commit()
    return {"message": f"{len(rules)} reglas guardadas correctamente"}



@router.get("/migration-controls", response_model=List[MigrationControlSchema])
def list_migration_controls(company_id: int, db: Session = Depends(get_dest_db)):
    return db.query(MigrationControl).filter(
        MigrationControl.company_id == company_id
    ).order_by(MigrationControl.source_table).all()

@router.delete("/migration-controls/{control_id}")
def reset_migration_control(control_id: int, db: Session = Depends(get_dest_db)):
    """Resetea el control de migración para volver a migrar desde el inicio"""
    ctrl = db.query(MigrationControl).filter(MigrationControl.id == control_id).first()
    if not ctrl:
        raise HTTPException(status_code=404, detail="Control no encontrado")
    ctrl.last_migrated_value = None
    ctrl.total_migrated = 0
    ctrl.last_run_status = None
    ctrl.last_run_message = None
    db.commit()
    return {"message": "Control reseteado — la próxima migración comenzará desde el inicio"}


# ─── Asientos Generados ───────────────────────────────────────────────────────

@router.delete("/delete-subcategoria-asientos/{company_id}/{subcategoria_id}")
def delete_subcategoria_asientos(company_id: int, subcategoria_id: int, db: Session = Depends(get_dest_db)):
    """Elimina asientos NO migrados (estado 0 o 1) de una subcategoría específica."""
    from sqlalchemy import Table, MetaData
    from backend.app.core.database import dest_engine as engine, get_dest_db
    import decimal
    import datetime as dt_module

    # Obtener sesión de base de datos si no se proporcionó
    if db is None:
        db = next(get_dest_db())
        should_close_db = True
    else:
        should_close_db = False

    sub = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.id == subcategoria_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subcategoría no encontrada")

    metadata = MetaData()
    deleted_det = 0
    deleted_head = 0

    tabla_det_name = sub.tabla_destino_detalle or "cf_diariol"
    tabla_head_name = sub.tabla_destino_cabecera or "cf_diario"

    try:
        DetTable = Table(tabla_det_name, metadata, autoload_with=engine)
    except:
        DetTable = None
    try:
        HeadTable = Table(tabla_head_name, metadata, autoload_with=engine)
    except:
        HeadTable = None

    # Collect nasiento values to delete from headers too
    asientos_to_delete = []
    if DetTable is not None:
        check_col = sub.col_destino_nasiento or "nasiento"
        if check_col in [c.name for c in DetTable.columns]:
            stmt_sel = db.query(getattr(DetTable.c, check_col)).filter(
                DetTable.c.company_id == company_id,
                DetTable.c.estado.in_(["0", "1", "PENDIENTE"]),
                DetTable.c.subcategoria_id == subcategoria_id
            ).distinct()
            asientos_to_delete = [a[0] for a in db.execute(stmt_sel).fetchall() if a[0]]

        stmt_del = DetTable.delete().where(
            DetTable.c.company_id == company_id,
            DetTable.c.estado.in_(["0", "1", "PENDIENTE"]),
            DetTable.c.subcategoria_id == subcategoria_id
        )
        result = db.execute(stmt_del)
        deleted_det = result.rowcount

    if HeadTable is not None and asientos_to_delete:
        check_col_head = sub.col_destino_nasiento or "nasiento"
        if check_col_head in [c.name for c in HeadTable.columns]:
            stmt_del_h = HeadTable.delete().where(
                HeadTable.c.company_id == company_id,
                HeadTable.c.estado.in_(["0", "1", "PENDIENTE"]),
                getattr(HeadTable.c, check_col_head).in_(asientos_to_delete)
            )
            result_h = db.execute(stmt_del_h)
            deleted_head = result_h.rowcount

    # Resetear el control incremental de generación para permitir que se vuelva a procesar toda la extracción
    sub.last_generated_control_value = None
    
    # Reset seat correlativos based on actual migrated seats in staging
    try:
        from backend.app.models.models import AsientoCorrelativo
        from sqlalchemy import select, func
        corrs = db.query(AsientoCorrelativo).filter(
            AsientoCorrelativo.company_id == company_id,
            AsientoCorrelativo.subcategoria_id == sub.id
        ).all()
        for corr in corrs:
            if DetTable is not None:
                check_col_nasiento = sub.col_destino_nasiento or "nasiento"
                if check_col_nasiento in [c.name for c in DetTable.columns]:
                    is_global = (corr.periodo == "GLOBAL" and corr.mes == "00") or ("cper" not in [c.name for c in DetTable.columns] or "cmes" not in [c.name for c in DetTable.columns])
                    if is_global:
                        stmt_max_mig = select(func.max(getattr(DetTable.c, check_col_nasiento))).where(
                            DetTable.c.company_id == company_id,
                            DetTable.c.subcategoria_id == sub.id,
                            DetTable.c.estado == "MIGRADO"
                        )
                    else:
                        stmt_max_mig = select(func.max(getattr(DetTable.c, check_col_nasiento))).where(
                            DetTable.c.company_id == company_id,
                            DetTable.c.subcategoria_id == sub.id,
                            DetTable.c.cper == corr.periodo,
                            DetTable.c.cmes == corr.mes,
                            DetTable.c.estado == "MIGRADO"
                        )
                    max_mig = db.execute(stmt_max_mig).scalar()
                    if max_mig is not None:
                        corr.asiento_actual = int(max_mig)
                    else:
                        corr.asiento_actual = corr.asiento_inicial - 1
                else:
                    if getattr(corr, "asiento_actual", None) is None:
                        corr.asiento_actual = corr.asiento_inicial - 1
            else:
                if getattr(corr, "asiento_actual", None) is None:
                    corr.asiento_actual = corr.asiento_inicial - 1
    except Exception as ex_corr:
        print(f"Error resetting correlativos in delete_subcategoria_asientos: {ex_corr}")
    
    db.commit()
    return {
        "message": f"Eliminados {deleted_det} líneas y {deleted_head} cabeceras pendientes para subcategoría {sub.nombre}",
        "deleted_detail": deleted_det,
        "deleted_header": deleted_head
    }


@router.get("/asientos-generados")
def list_asientos(company_id: int, subcategoria_id: Optional[int] = None,
                  estado: Optional[str] = None, lote_id: Optional[str] = None,
                  skip: int = 0, limit: int = 100, db: Session = Depends(get_dest_db)):
    query = db.query(AsientoContableGenerado).filter(
        AsientoContableGenerado.company_id == company_id
    )
    if subcategoria_id:
        query = query.filter(AsientoContableGenerado.subcategoria_id == subcategoria_id)
    if estado:
        query = query.filter(AsientoContableGenerado.estado == estado)
    if lote_id:
        query = query.filter(AsientoContableGenerado.lote_id == lote_id)
    total = query.count()
    items = query.order_by(AsientoContableGenerado.nasiento, AsientoContableGenerado.nidlin)\
                 .offset(skip).limit(limit).all()
    return {"total": total, "items": [_asiento_to_dict(a) for a in items]}

def _asiento_to_dict(a: AsientoContableGenerado) -> dict:
    return {
        "id": a.id, "cper": a.cper, "cmes": a.cmes, "ccodori": a.ccodori,
        "nasiento": a.nasiento, "nidlin": a.nidlin, "ntc": float(a.ntc or 0),
        "ccodcue": a.ccodcue, "ndebe": float(a.ndebe or 0), "nhaber": float(a.nhaber or 0),
        "cglosa": a.cglosa, "ccoddoc": a.ccoddoc, "cserie": a.cserie, "cnumero": a.cnumero,
        "ffechadoc": a.ffechadoc, "ccodruc": a.ccodruc, "ccodenti": a.ccodenti,
        "nbase1": float(a.nbase1 or 0), "nigv1": float(a.nigv1 or 0), "ntot": float(a.ntot or 0),
        "ccodcos": a.ccodcos, "ccodpresu": a.ccodpresu, "ccodmon": a.ccodmon,
        "estado": a.estado, "lote_id": a.lote_id, "created_at": str(a.created_at)
    }

def _get_dest_constraints_from_final(company_id: int, table_name: str, schema_name: str, db: Session):
    """
    Conecta a la BD destino final (Contasis) y obtiene las restricciones reales
    de columnas (NOT NULL, max_length) para la tabla indicada.
    Retorna dict: {col_name: {"required": bool, "max_length": int|None, "type": str}}
    """
    from backend.app.models.models import FinalDestConnection
    from backend.app.services.connection_manager import ConnectionManager
    from sqlalchemy import Table, MetaData

    final_conn = db.query(FinalDestConnection).filter(
        FinalDestConnection.company_id == company_id,
        FinalDestConnection.is_active == True
    ).first()
    if not final_conn:
        return None  # No hay conexión final, no se puede validar

    try:
        conn_data = {
            "host": final_conn.host, "port": final_conn.port,
            "database_name": final_conn.database_name,
            "username": final_conn.username, "password": final_conn.password
        }
        final_engine = ConnectionManager.get_dest_engine(conn_data)
        meta = MetaData()
        tbl = Table(table_name, meta, schema=schema_name, autoload_with=final_engine)

        constraints = {}
        for col in tbl.columns:
            max_len = None
            if hasattr(col.type, 'length') and col.type.length:
                max_len = col.type.length
            # Para validación de migración, consideramos obligatorio si:
            # - La columna es NOT NULL (col.nullable=False)
            # - No es primary key (esos se manejan automáticamente)
            # NOTA: No excluimos columnas con server_default porque queremos
            # alertar al usuario que la columna requiere un valor, aunque la BD
            # tenga un default (el default puede no ser el valor correcto).
            is_required = (not col.nullable) and (not col.primary_key)
            constraints[col.name] = {
                "required": is_required,
                "max_length": max_len,
                "nullable": col.nullable,
                "type": str(col.type)
            }
        return constraints
    except Exception as e:
        print(f"WARN: No se pudo obtener restricciones del destino final para {schema_name}.{table_name}: {e}")
        return None


def _validate_records_against_schema(records: list, table_obj, table_label: str, sub_id: int, dest_constraints: dict = None):
    """
    Valida los registros contra las restricciones de esquema de la tabla destino:
    - Longitud Máxima para columnas de texto (VARCHAR/CHAR)
    - Campos obligatorios (NOT NULL sin default)
    Si dest_constraints se proporciona (desde la BD destino final), se usa para
    validar NOT NULL y max_length; si no, se usa el esquema de table_obj (staging).
    Retorna una lista de errores encontrados. Cada error es un dict con:
    {"field", "row_index", "value", "error", "max_length"}
    """
    from sqlalchemy import String, Text
    errors = []
    if not records or table_obj is None:
        return errors

    # Build constraints from staging table first
    col_constraints = {}
    for col in table_obj.columns:
        max_len = None
        if hasattr(col.type, 'length') and col.type.length:
            max_len = col.type.length
        is_required = (not col.nullable) and col.default is None and col.server_default is None and not col.primary_key
        col_constraints[col.name] = {
            "max_length": max_len,
            "required": is_required
        }

    # Override with real destination constraints if available
    if dest_constraints:
        for col_name, dest_info in dest_constraints.items():
            if col_name in col_constraints:
                col_constraints[col_name]["required"] = dest_info.get("required", False)
                if dest_info.get("max_length"):
                    col_constraints[col_name]["max_length"] = dest_info["max_length"]
            else:
                # Column exists in destination but not in staging record keys — skip
                pass

    for idx, record in enumerate(records):
        # Extract row context for better error reporting
        row_context = {
            "nasiento": record.get("nasiento", "-"),
            "nidlin": record.get("nidlin", "-"),
            "cper": record.get("cper", ""),
            "cmes": record.get("cmes", ""),
            "ccodori": record.get("ccodori", ""),
            "ccoddoc": record.get("ccoddoc", ""),
            "cserie": record.get("cserie", ""),
            "cnumero": record.get("cnumero", "")
        }

        for field, value in record.items():
            if field not in col_constraints:
                continue
            constraints = col_constraints[field]

            # Check NOT NULL / Required (Only flag None or empty string of length 0)
            # If the user put a space " ", it counts as a value per their instruction.
            is_truly_empty = (value is None) or (isinstance(value, str) and len(value) == 0)
            if constraints["required"] and is_truly_empty:
                err_dict = {
                    "field": field,
                    "row_index": idx,
                    "value": "NULL" if value is None else "''",
                    "error": f"Campo '{field}' es obligatorio (NOT NULL) pero está vacío/nulo",
                    "table": table_label,
                    "subcategoria_id": sub_id
                }
                err_dict.update(row_context)
                errors.append(err_dict)

            # Check MAX LENGTH
            if constraints["max_length"] and value is not None and isinstance(value, str):
                if len(value) > constraints["max_length"]:
                    err_dict = {
                        "field": field,
                        "row_index": idx,
                        "value": repr(value[:50]) + ("..." if len(value) > 50 else ""),
                        "error": f"Campo '{field}' excede longitud máxima ({len(value)}/{constraints['max_length']})",
                        "max_length": constraints["max_length"],
                        "actual_length": len(value),
                        "table": table_label,
                        "subcategoria_id": sub_id
                    }
                    err_dict.update(row_context)
                    errors.append(err_dict)

    # Also check for required columns that are MISSING entirely from the records
    if dest_constraints and records:
        record_keys = set(records[0].keys())
        # Exclude internal/system columns from the missing check
        system_cols = {"company_id", "subcategoria_id", "lote_id", "estado", "id", "created_at", "updated_at"}
        for col_name, dest_info in dest_constraints.items():
            if dest_info.get("required") and col_name not in record_keys and col_name not in system_cols:
                errors.append({
                    "field": col_name,
                    "row_index": 0,
                    "value": "(columna no mapeada)",
                    "error": f"Campo '{col_name}' es obligatorio (NOT NULL) en destino pero no está mapeado",
                    "table": table_label,
                    "subcategoria_id": sub_id
                })

    return errors


def _extract_period_month(sub_filter_rules, adhoc_filters, sub=None, df=None):
    periodo = None
    mes = None
    import pandas as pd
    
    # Custom configured columns in subcategory mapping
    custom_period_col = getattr(sub, "col_origen_periodo", None)
    custom_mes_col = getattr(sub, "col_origen_mes", None)
    
    # helper lists
    period_cols = ["cper", "cperiodo", "c_periodo", "anos", "anio", "ano", "periodo", "c_per", "fecha"]
    mes_cols = ["cmes", "c_mes", "mes", "c_mes_c"]
    
    # Check adhoc first as they are run-time overrides
    for f in (adhoc_filters or []):
        col = str(f.get("column") or "").strip().lower()
        if custom_period_col and col == custom_period_col.strip().lower():
            periodo = str(f.get("value") or "").strip()
        elif custom_mes_col and col == custom_mes_col.strip().lower():
            mes = str(f.get("value") or "").strip()
            if len(mes) == 1 and mes.isdigit():
                mes = f"0{mes}"
                
        # fallback to standard names
        if not periodo and col in period_cols:
            val = str(f.get("value") or "").strip()
            # If it's a date column, extract the year
            if col == "fecha" and val:
                # Extract year from date formats like "2026-06-01" or "2026/06/01"
                import re
                year_match = re.search(r'(\d{4})', val)
                if year_match:
                    periodo = year_match.group(1)
                else:
                    periodo = val
            else:
                periodo = val
        # Also check value2 for date columns (for BETWEEN operators)
        if not periodo and col in period_cols:
            val2 = str(f.get("value2") or "").strip()
            if col == "fecha" and val2:
                import re
                year_match = re.search(r'(\d{4})', val2)
                if year_match:
                    periodo = year_match.group(1)
        if not mes and col in mes_cols:
            mes = str(f.get("value") or "").strip()
            if len(mes) == 1 and mes.isdigit():
                mes = f"0{mes}"
                
    # If not found, check sub filter rules
    for f in (sub_filter_rules or []):
        col = str(f.get("column") or "").strip().lower()
        if custom_period_col and col == custom_period_col.strip().lower() and not periodo:
            periodo = str(f.get("value") or "").strip()
        elif custom_mes_col and col == custom_mes_col.strip().lower() and not mes:
            mes = str(f.get("value") or "").strip()
            if len(mes) == 1 and mes.isdigit():
                mes = f"0{mes}"
                
        if not periodo and col in period_cols:
            val = str(f.get("value") or "").strip()
            # If it's a date column, extract the year
            if col == "fecha" and val:
                # Extract year from date formats like "2026-06-01" or "2026/06/01"
                import re
                year_match = re.search(r'(\d{4})', val)
                if year_match:
                    periodo = year_match.group(1)
                else:
                    periodo = val
            else:
                periodo = val
        if not mes and col in mes_cols:
            mes = str(f.get("value") or "").strip()
            if len(mes) == 1 and mes.isdigit():
                mes = f"0{mes}"

    # If still not found, check columns in the loaded dataframe
    if df is not None and not df.empty:
        df_cols_lower = {col_name.lower(): col_name for col_name in df.columns}
        
        # Check custom period column
        if not periodo and custom_period_col:
            c_col_p = custom_period_col.strip().lower()
            if c_col_p in df_cols_lower:
                val = df.iloc[0][df_cols_lower[c_col_p]]
                if pd.notna(val):
                    periodo = str(val).strip()
                    
        # Check custom mes column
        if not mes and custom_mes_col:
            c_col_m = custom_mes_col.strip().lower()
            if c_col_m in df_cols_lower:
                val = df.iloc[0][df_cols_lower[c_col_m]]
                if pd.notna(val):
                    mes = str(val).strip()
                    if len(mes) == 1 and mes.isdigit():
                        mes = f"0{mes}"
                        
        # Fallback to standard columns in dataframe if still not found
        if not periodo:
            for col in period_cols:
                if col in df_cols_lower:
                    val = df.iloc[0][df_cols_lower[col]]
                    if pd.notna(val):
                        val_str = str(val).strip()
                        # If it's a date column, extract the year
                        if col == "fecha" and val_str:
                            # Extract year from date formats like "2026-06-01" or "2026/06/01"
                            import re
                            year_match = re.search(r'(\d{4})', val_str)
                            if year_match:
                                periodo = year_match.group(1)
                            else:
                                periodo = val_str
                        else:
                            periodo = val_str
                        break
                        
        if not mes:
            for col in mes_cols:
                if col in df_cols_lower:
                    val = df.iloc[0][df_cols_lower[col]]
                    if pd.notna(val):
                        mes = str(val).strip()
                        if len(mes) == 1 and mes.isdigit():
                            mes = f"0{mes}"
                        break
                
    # Defaults if not found
    from datetime import datetime
    if not periodo:
        periodo = str(datetime.now().year)
    if not mes:
        mes = f"{datetime.now().month:02d}"
        
    return periodo, mes


def _get_df_period_month_cols(df, sub):
    if df is None or df.empty:
        return None, None
    df_cols_lower = {col_name.lower(): col_name for col_name in df.columns}
    
    custom_period_col = getattr(sub, "col_origen_periodo", None)
    period_col_in_df = None
    if custom_period_col:
        c_col_p = custom_period_col.strip().lower()
        if c_col_p in df_cols_lower:
            period_col_in_df = df_cols_lower[c_col_p]
            
    if not period_col_in_df:
        # Check for exact "fecha" match first (case-insensitive)
        if "fecha" in df_cols_lower:
            period_col_in_df = df_cols_lower["fecha"]
        else:
            # Fallback to other period columns
            period_cols = ["cper", "cperiodo", "c_periodo", "anos", "anio", "ano", "periodo", "c_per"]
            for col in period_cols:
                if col in df_cols_lower:
                    period_col_in_df = df_cols_lower[col]
                    break

    custom_mes_col = getattr(sub, "col_origen_mes", None)
    mes_col_in_df = None
    if custom_mes_col:
        c_col_m = custom_mes_col.strip().lower()
        if c_col_m in df_cols_lower:
            mes_col_in_df = df_cols_lower[c_col_m]
            
    if not mes_col_in_df:
        mes_cols = ["cmes", "c_mes", "mes", "c_mes_c"]
        for col in mes_cols:
            if col in df_cols_lower:
                mes_col_in_df = df_cols_lower[col]
                break
                
    return period_col_in_df, mes_col_in_df


def _generate_subcategoria_cf_diariol(
    sub: MapeoSubcategoria,
    db: Session,
    company_id: int,
    filters: list = [],
    global_lote_id: Optional[str] = None,
    counters_por_asiento: dict = None,
    generate_headers: bool = True,
    generate_details: bool = True,
    is_realtime: bool = False
):
    from backend.app.models.models import CfDiariol, CfDiario, MapeoLineaAsiento, MapeoSubcategoria, AsientoCorrelativo
    from backend.app.core.database import dest_engine
    from sqlalchemy import text
    import pandas as pd
    from backend.app.core.formula_parser import evaluate_formula_on_df
    from typing import Any, Optional

    if counters_por_asiento is None:
        counters_por_asiento = {}

    lineas = db.query(MapeoLineaAsiento).filter(
        MapeoLineaAsiento.subcategoria_id == sub.id,
        MapeoLineaAsiento.is_active == True
    ).order_by(MapeoLineaAsiento.orden).all()

    if not lineas:
        return 0, 0, [] # No configurado
    # Load DetTable early for duplicate lookups
    from sqlalchemy import Table, MetaData, select
    metadata = MetaData()
    engine = db.get_bind()
    tabla_det_name = sub.tabla_destino_detalle or "cf_diariol"
    try:
        DetTable = Table(tabla_det_name, metadata, autoload_with=engine)
    except Exception as e:
        print(f"Error loading DetTable {tabla_det_name}: {e}")
        DetTable = None

    # Fetch actual columns of the source table to match case-insensitively
    from sqlalchemy import inspect
    try:
        insp = inspect(db.bind if db else dest_engine)
        actual_cols = [c['name'] for c in insp.get_columns(sub.tabla_origen.lower().replace(" ", "_"))]
    except Exception as e:
        print(f"Error inspecting columns for table {sub.tabla_origen}: {e}")
        actual_cols = []
    cols_map = {c.lower(): c for c in actual_cols}

    query_str = f'SELECT * FROM "{sub.tabla_origen.lower()}"'
    where_parts = [f"company_id = {company_id}"]
    query_params = {}

    # --- SQL-level optimization: filter out already processed records ---
    has_idcontrol_in_source = "idcontrol" in cols_map
    if has_idcontrol_in_source and DetTable is not None and "idcontrol" in [c.name for c in DetTable.columns]:
        where_parts.append(f"""
            ("idcontrol" IS NULL OR "idcontrol" NOT IN (
                SELECT idcontrol FROM "{tabla_det_name}"
                WHERE company_id = {company_id}
                  AND subcategoria_id = {sub.id}
                  AND estado IN ('MIGRADO', 'PENDIENTE')
            ))
        """)

    # --- SQL-level optimization: single control column incremental filter ---
    ctrl_col = getattr(sub, 'control_column_origen', None)
    ctrl_val = getattr(sub, 'last_generated_control_value', None)
    if ctrl_col and ctrl_val and "," not in ctrl_col:
        ctrl_col_clean = ctrl_col.strip()
        col_actual = cols_map.get(ctrl_col_clean.lower())
        if col_actual:
            try:
                # If numeric, compare directly
                float(ctrl_val)
                where_parts.append(f'"{col_actual}" > {ctrl_val}')
            except ValueError:
                # If string/date, use parameter binding
                where_parts.append(f'"{col_actual}" > :ctrl_val_sql')
                query_params["ctrl_val_sql"] = ctrl_val
            print(f"SQL-LEVEL INCREMENTAL OPTIMIZATION: Filtering by {col_actual} > {ctrl_val}")

    
    # 1. Apply subcategory-level filter_rules (configured in mapping editor)
    sub_filter_rules = sub.filter_rules or []
    if is_realtime:
        from datetime import datetime
        current_year = str(datetime.now().year)
        current_month = f"{datetime.now().month:02d}"
        
        custom_period_col = getattr(sub, "col_origen_periodo", None)
        custom_mes_col = getattr(sub, "col_origen_mes", None)
        
        period_cols = ["cper", "cperiodo", "c_periodo", "anos", "anio", "ano", "periodo", "c_per"]
        mes_cols = ["cmes", "c_mes", "mes", "c_mes_c"]
        
        # Determine all configured months from AsientoCorrelativo for the current year
        # so we process ALL enabled periods, not just the current month.
        configured_months = []
        try:
            corr_records = db.query(AsientoCorrelativo).filter(
                AsientoCorrelativo.company_id == company_id,
                AsientoCorrelativo.subcategoria_id == sub.id,
                AsientoCorrelativo.periodo == current_year
            ).all()
            configured_months = sorted(set(c.mes for c in corr_records if c.mes and c.mes != "00"))
        except Exception as e:
            print(f"Error loading correlativos for realtime months: {e}")
        
        # Fallback: if no correlativos found, use current month only
        if not configured_months:
            configured_months = [current_month]
        
        new_rules = []
        for rule in sub_filter_rules:
            r_col = str(rule.get("column") or "").strip().lower()
            new_rule = dict(rule)
            
            # Check if this rule is for the period column
            if (custom_period_col and r_col == custom_period_col.strip().lower()) or (not custom_period_col and r_col in period_cols):
                new_rule["value"] = current_year
                print(f"Overriding filter rule for period column '{rule.get('column')}' from '{rule.get('value')}' to '{current_year}'")
            
            # Check if this rule is for the month column — use IN with all configured months
            elif (custom_mes_col and r_col == custom_mes_col.strip().lower()) or (not custom_mes_col and r_col in mes_cols):
                new_rule["operator"] = "IN"
                new_rule["value"] = ",".join(configured_months)
                print(f"Overriding filter rule for month column '{rule.get('column')}' from '{rule.get('value')}' to IN({new_rule['value']}) — {len(configured_months)} months configured")
                
            new_rules.append(new_rule)
        sub_filter_rules = new_rules

    for idx, rule in enumerate(sub_filter_rules):
        col = rule.get("column", "")
        op = rule.get("operator", "=").upper()
        val = rule.get("value", "")
        val2 = rule.get("value2", "")
        if not col:
            continue
        col_actual = cols_map.get(col.lower(), col)
        col_quoted = f'"{col_actual}"'
        pkey = f"fr{idx}"

        if op == "IS NULL":
            where_parts.append(f"{col_quoted} IS NULL")
        elif op == "IS NOT NULL":
            where_parts.append(f"{col_quoted} IS NOT NULL")
        elif op in ("BETWEEN", "RANGO_FECHAS") and val and val2:
            where_parts.append(f"{col_quoted} BETWEEN :{pkey}a AND :{pkey}b")
            query_params[f"{pkey}a"] = val
            query_params[f"{pkey}b"] = val2
        elif op == "IN" and val:
            vals = [v.strip() for v in val.split(",")]
            placeholders = ", ".join([f":{pkey}_{j}" for j in range(len(vals))])
            where_parts.append(f"{col_quoted} IN ({placeholders})")
            for j, v in enumerate(vals):
                query_params[f"{pkey}_{j}"] = v
        elif op == "LIKE" and val:
            where_parts.append(f"{col_quoted} LIKE :{pkey}")
            query_params[pkey] = val
        elif val:
            where_parts.append(f"{col_quoted} {op} :{pkey}")
            query_params[pkey] = val

    # 2. Apply ad-hoc filters from the ETL UI (runtime filters)
    if filters:
        for i, f in enumerate(filters):
            col = f.get("column", "")
            op = f.get("operator", "=").upper()
            val = f.get("value", "")
            val2 = f.get("value2", "")
            if not col: continue
            col_actual = cols_map.get(col.lower(), col)
            col_quoted = f'"{col_actual}"'
            
            if op == "IS NULL": where_parts.append(f"{col_quoted} IS NULL")
            elif op == "IS NOT NULL": where_parts.append(f"{col_quoted} IS NOT NULL")
            elif op in ("BETWEEN", "RANGO_FECHAS") and val and val2:
                where_parts.append(f"{col_quoted} BETWEEN :p{i}a AND :p{i}b")
                query_params[f"p{i}a"] = val
                query_params[f"p{i}b"] = val2
            elif op == "IN" and val:
                vals = [v.strip() for v in val.split(",")]
                placeholders = ", ".join([f":p{i}_{j}" for j in range(len(vals))])
                where_parts.append(f"{col_quoted} IN ({placeholders})")
                for j, v in enumerate(vals): query_params[f"p{i}_{j}"] = v
            elif op == "LIKE" and val:
                where_parts.append(f"{col_quoted} LIKE :p{i}")
                query_params[f"p{i}"] = val
            elif val:
                where_parts.append(f"{col_quoted} {op} :p{i}")
                query_params[f"p{i}"] = val
    
    if where_parts:
        query_str += " WHERE " + " AND ".join(where_parts)

    try:
        with dest_engine.connect() as conn:
            result = conn.execute(text(query_str), query_params)
            rows = result.fetchall()
            columns = list(result.keys())
    except Exception as e:
        print(f"DB READ ERROR for {sub.tabla_origen}: {e}")
        return 0, 0, []

    if not rows:
        return 0, 0, []

    df = pd.DataFrame(rows, columns=columns)

    clave_str = sub.clave_asiento
    if not clave_str:
        clave_columns = [columns[0]] if columns else []
    else:
        cols_lower_map = {col.lower(): col for col in columns}
        clave_columns = [cols_lower_map[c.strip().lower()] for c in clave_str.split(",") if c.strip().lower() in cols_lower_map]
        if not clave_columns:
            clave_columns = [columns[0]] if columns else []

    # ─── Control de Duplicados local (IDCONTROL) ───
    error_idcontrols = []
    if DetTable is not None and 'idcontrol' in DetTable.c:
        try:
            stmt_err = select(DetTable.c.idcontrol).where(
                DetTable.c.company_id == company_id,
                DetTable.c.subcategoria_id == sub.id,
                DetTable.c.estado.in_(["0", "ERROR", "PENDIENTE"])
            )
            error_idcontrols = [str(r[0]) for r in db.execute(stmt_err).fetchall() if r[0]]
        except Exception as e:
            print(f"Error fetching error_idcontrols: {e}")

    if 'idcontrol' in df.columns and not df.empty and DetTable is not None:
        try:
            # Cross-company check: We do NOT filter by company_id OR subcategoria_id here,
            # so if another company/subcategory already processed this idcontrol, we skip it.
            # Using IN clause for performance.
            idcontrols_in_df = df['idcontrol'].dropna().astype(str).unique().tolist()
            if not idcontrols_in_df:
                pass
            else:
                stmt_existing = select(DetTable.c.idcontrol).where(
                     DetTable.c.company_id == company_id,
                     DetTable.c.subcategoria_id == sub.id,
                     DetTable.c.estado.in_(["0", "1", "PENDIENTE", "MIGRADO"]),
                     DetTable.c.idcontrol.in_(idcontrols_in_df)
                )
            
            existing_records = db.execute(stmt_existing).fetchall()
            existing_ids = set()
            for r in existing_records:
                rid = str(r[0])
                # Skip the duplicate check if it's an error from our own subcategory!
                # This allows it to be re-processed.
                if rid not in error_idcontrols:
                    existing_ids.add(rid)
                    
            if existing_ids:
                before_count = len(df)
                df = df[~df['idcontrol'].astype(str).isin(existing_ids)]
                diff = before_count - len(df)
                if diff > 0:
                    print(f"IDCONTROL: Filtradas {diff} filas ya registradas para la compañía {company_id} y subcat {sub.id}.")
                if df.empty:
                    return 0, 0, []
            else:
                print(f"IDCONTROL: No se encontraron registros previos para subcat {sub.id}.")
        except Exception as e:
            print(f"Error aplicando filtro IDCONTROL cruzado: {e}")

    # ─── Control Incremental: excluir filas ya migradas ───
    ctrl_col = getattr(sub, 'control_column_origen', None)
    ctrl_val = getattr(sub, 'last_generated_control_value', None)
    
    if not ctrl_col and company_id:
        try:
            from backend.app.models.models import TableSelection
            ts_list = db.query(TableSelection).filter(TableSelection.company_id == company_id).all()
            for ts in ts_list:
                if ts.table_name.lower() in sub.tabla_origen.lower() or sub.tabla_origen.lower() in ts.table_name.lower():
                    if ts.control_column:
                        ctrl_col = ts.control_column
                        break
        except Exception: pass

    if ctrl_col and ctrl_val:
        cols_split = [c.strip() for c in ctrl_col.split(",")]
        actual_cols = []
        for c in cols_split:
            match = next((col for col in columns if col.lower() == c.lower()), None)
            if match: actual_cols.append(match)

        if len(actual_cols) == len(cols_split):
            # Composite Key incremental tracking
            before_count = len(df)
            try:
                # Build compound string index
                df['_incremental_key'] = df[actual_cols].astype(str).agg('-'.join, axis=1)
                
                if 'idcontrol' in df.columns and error_idcontrols:
                    df = df[(df['_incremental_key'] > str(ctrl_val)) | (df['idcontrol'].astype(str).isin(error_idcontrols))]
                else:
                    df = df[df['_incremental_key'] > str(ctrl_val)]
            except Exception as e:
                print(f"Error en filtro incremental compuesto: {e}")
            after_count = len(df)
            if before_count != after_count:
                print(f"CONTROL INCREMENTAL: Filtradas {before_count - after_count} filas ya migradas (cols={ctrl_col}, last_val={ctrl_val})")
            if df.empty:
                return 0, 0, []
        elif len(actual_cols) == 1:
            # Single key fallback
            actual_col = actual_cols[0]
            before_count = len(df)
            try:
                df_ctrl = pd.to_numeric(df[actual_col], errors='coerce')
                ctrl_numeric = pd.to_numeric(pd.Series([ctrl_val]), errors='coerce').iloc[0]
                
                has_ids = 'idcontrol' in df.columns and error_idcontrols
                
                if pd.notna(ctrl_numeric):
                    if has_ids:
                        df = df[(df_ctrl > ctrl_numeric) | (df['idcontrol'].astype(str).isin(error_idcontrols))]
                    else:
                        df = df[df_ctrl > ctrl_numeric]
                else:
                    if has_ids:
                        df = df[(df[actual_col].astype(str) > ctrl_val) | (df['idcontrol'].astype(str).isin(error_idcontrols))]
                    else:
                        df = df[df[actual_col].astype(str) > ctrl_val]
            except Exception:
                has_ids = 'idcontrol' in df.columns and error_idcontrols
                if has_ids:
                    df = df[(df[actual_col].astype(str) > ctrl_val) | (df['idcontrol'].astype(str).isin(error_idcontrols))]
                else:
                    df = df[df[actual_col].astype(str) > ctrl_val]
            after_count = len(df)
            if before_count != after_count:
                print(f"CONTROL INCREMENTAL: Filtradas {before_count - after_count} filas de fallback (col={actual_col}, last_val={ctrl_val})")
            if df.empty:
                return 0, 0, []

    # ─── Pre-filtrar df según las condiciones de aplicación de las líneas ───
    if not df.empty and lineas:
        survives_mask = pd.Series(False, index=df.index)
        has_any_condition = False
        
        for linea in lineas:
            if not linea.mapeo_detalle:
                continue
            
            # If a line does not have any condition_aplicacion, then all rows survive for this line
            if not getattr(linea, "condicion_aplicacion", None) or str(linea.condicion_aplicacion).strip() == "":
                survives_mask = pd.Series(True, index=df.index)
                has_any_condition = True
                break
            else:
                has_any_condition = True
                try:
                    # Evaluate condition_aplicacion on df
                    mask = evaluate_formula_on_df(df, linea.condicion_aplicacion, db, company_id, default=False, db_engine=db.bind)
                    # Convert to boolean mask safely
                    mask = pd.to_numeric(mask, errors='coerce').fillna(0).astype(bool) | (mask.astype(str).str.strip().str.upper() == 'TRUE')
                    survives_mask = survives_mask | mask
                except Exception as e_cond:
                    print(f"Error pre-evaluating line condition: {e_cond}")
                    # In case of evaluation error, play it safe and keep the rows
                    survives_mask = pd.Series(True, index=df.index)
                    break
        
        # If there are active lines and at least one has a condition
        if has_any_condition:
            before_count = len(df)
            df = df[survives_mask].copy()
            after_count = len(df)
            if before_count != after_count:
                print(f"FILTRO CONDICIONES LÍNEA: Conservadas {after_count} de {before_count} filas que cumplen alguna condición de línea")
            if df.empty:
                return 0, 0, []


    # Reflect destination tables
    from sqlalchemy import Table, MetaData, func
    from backend.app.core.database import dest_engine as engine  # migconta_db engine
    
    metadata = MetaData()
    tabla_head_name = sub.tabla_destino_cabecera or "cf_diario"
    tabla_det_name = sub.tabla_destino_detalle or "cf_diariol"
    
    HeadTable = None
    DetTable = None
    head_cols = []
    det_cols = []
    
    if generate_headers:
        try:
            HeadTable = Table(tabla_head_name, metadata, autoload_with=engine)
            head_cols = [c.name for c in HeadTable.columns]
        except Exception as e:
            print(f"Error cargando esquema cabecera staging ({tabla_head_name}): {e}")
            HeadTable = None

    if generate_details:
        try:
            DetTable = Table(tabla_det_name, metadata, autoload_with=engine)
            det_cols = [c.name for c in DetTable.columns]
        except Exception as e:
            print(f"Error cargando esquema detalle staging ({tabla_det_name}): {e}")
            DetTable = None

    # Before generating new entries, wipe out the old failed ones we are about to regenerate
    if error_idcontrols and not df.empty and 'idcontrol' in df.columns:
        processing_errors = [eid for eid in error_idcontrols if eid in df['idcontrol'].astype(str).values]
        if processing_errors:
            print(f"Borrando {len(processing_errors)} registros fallidos antes de re-generar...")
            if DetTable is not None:
                try:
                    db.execute(DetTable.delete().where(
                        DetTable.c.company_id == company_id,
                        DetTable.c.subcategoria_id == sub.id,
                        DetTable.c.estado.in_(["0", "ERROR", "PENDIENTE"]),
                        DetTable.c.idcontrol.in_(processing_errors)
                    ))
                except Exception as e: print(f"Error borrando re-generados detalle: {e}")
            if HeadTable is not None and 'idcontrol' in head_cols:
                try:
                    db.execute(HeadTable.delete().where(
                        HeadTable.c.company_id == company_id,
                        HeadTable.c.subcategoria_id == sub.id,
                        HeadTable.c.estado.in_(["0", "ERROR", "PENDIENTE"]),
                        HeadTable.c.idcontrol.in_(processing_errors)
                    ))
                except Exception as e: print(f"Error borrando re-generados cabecera: {e}")
            db.commit()

    # Asignar número de asiento
    # Use a unique key for the current company to track nasiento across subcategories
    nasiento_key = f"{company_id}-global"
    conn_data = None
    if nasiento_key not in counters_por_asiento:
        last_nasiento_in_db = 0
        from backend.app.models.models import FinalDestConnection
        from backend.app.services.connection_manager import ConnectionManager
        from sqlalchemy import select
        
        # Connect to Target Database to get continuous numbering
        final_conn = db.query(FinalDestConnection).filter(FinalDestConnection.company_id == company_id, FinalDestConnection.is_active == True).first()
        if final_conn and DetTable is not None:
            try:
                conn_data = {"host": final_conn.host, "port": final_conn.port, "database_name": final_conn.database_name, "username": final_conn.username, "password": final_conn.password}
                final_engine = ConnectionManager.get_dest_engine(conn_data)
                check_col_nasiento = sub.col_destino_nasiento or "nasiento"
                
                with final_engine.connect() as f_conn:
                    remote_metadata = MetaData()
                    RemoteDetTable = Table(tabla_det_name, remote_metadata, autoload_with=final_engine)
                    # Query Max
                    r_stmt = select(func.max(getattr(RemoteDetTable.c, check_col_nasiento)))
                    last_nasiento_in_db = f_conn.execute(r_stmt).scalar() or 0
            except Exception as e:
                print(f"Error fetching remote max nasiento: {e}")

        # Fallback to local staging if remote max is 0
        if last_nasiento_in_db == 0 and DetTable is not None:
            check_col_nasiento = sub.col_destino_nasiento or "nasiento"
            if check_col_nasiento in det_cols:
                stmt_nas = db.query(func.max(getattr(DetTable.c, check_col_nasiento))).filter(
                    DetTable.c.company_id == company_id,
                    DetTable.c.estado.in_(["PENDIENTE", "1", "MIGRADO"])
                )
                last_nasiento_in_db = db.execute(stmt_nas).scalar() or 0
        
        counters_por_asiento[nasiento_key] = last_nasiento_in_db
    else:
        # If the key is in counters, we might have connection data populated in a previous step
        final_conn = db.query(FinalDestConnection).filter(FinalDestConnection.company_id == company_id, FinalDestConnection.is_active == True).first()
        if final_conn:
            conn_data = {"host": final_conn.host, "port": final_conn.port, "database_name": final_conn.database_name, "username": final_conn.username, "password": final_conn.password}

    # ─── Control de correlativos por periodo/mes (AsientoCorrelativo) ───
    period_col, mes_col = _get_df_period_month_cols(df, sub)
    default_period, default_mes = _extract_period_month(sub.filter_rules, filters, sub=sub, df=df)

    is_global_correlative = (period_col is None and mes_col is None and not default_period and not default_mes)

    if is_global_correlative:
        df['_row_periodo'] = "GLOBAL"
        df['_row_mes'] = "00"
    else:
        if period_col:
            df['_row_periodo'] = df[period_col].astype(str).str.strip()
            # If it's a date column, extract the year
            if period_col.lower() == "fecha":
                import re
                df['_row_periodo'] = df['_row_periodo'].apply(lambda x: re.search(r'(\d{4})', str(x)).group(1) if re.search(r'(\d{4})', str(x)) else x)
            # If it's a calculated column like C_periodo, use default_period if values are invalid
            elif period_col.lower().startswith("c_") and default_period:
                # Replace nan/None values with default_period from filters
                df['_row_periodo'] = df['_row_periodo'].apply(lambda x: default_period if str(x).strip() in ['nan', 'None', ''] else str(x).strip())
        else:
            df['_row_periodo'] = default_period or ""

        if mes_col:
            df['_row_mes'] = df[mes_col].astype(str).str.strip().apply(lambda x: x.zfill(2) if x.isdigit() else x)
        else:
            df['_row_mes'] = default_mes or ""

        df['_row_periodo'] = df['_row_periodo'].replace('nan', default_period or '').replace('None', default_period or '')
        df['_row_mes'] = df['_row_mes'].replace('nan', default_mes or '').replace('None', default_mes or '')
        df['_row_periodo'] = df['_row_periodo'].apply(lambda x: x if x else (default_period or ''))
        df['_row_mes'] = df['_row_mes'].apply(lambda x: x if x else (default_mes or ''))

        from datetime import datetime
        now_year = str(datetime.now().year)
        now_month = str(datetime.now().month).zfill(2)
        df['_row_periodo'] = df['_row_periodo'].apply(lambda x: x if x else now_year)
        df['_row_mes'] = df['_row_mes'].apply(lambda x: x if x else now_month)

    df['nasiento'] = 0

    for (gp_periodo, gp_mes), gp_df in df.groupby(['_row_periodo', '_row_mes'], dropna=False):
        gp_periodo_str = str(gp_periodo).strip()
        gp_mes_str = str(gp_mes).strip()
        
        correlativo_rec = db.query(AsientoCorrelativo).filter(
            AsientoCorrelativo.company_id == company_id,
            AsientoCorrelativo.subcategoria_id == sub.id,
            AsientoCorrelativo.periodo == gp_periodo_str,
            AsientoCorrelativo.mes == gp_mes_str
        ).first()
        
        if correlativo_rec:
            nasiento_base = max(correlativo_rec.asiento_inicial, correlativo_rec.asiento_actual + 1)
        else:
            remote_max = 0
            if conn_data:
                try:
                    final_engine = ConnectionManager.get_dest_engine(conn_data)
                    check_col_nasiento = sub.col_destino_nasiento or "nasiento"
                    with final_engine.connect() as f_conn:
                        remote_metadata = MetaData()
                        RemoteDetTable = Table(tabla_det_name, remote_metadata, autoload_with=final_engine)
                        if check_col_nasiento in [c.name for c in RemoteDetTable.columns]:
                            if not is_global_correlative and "cper" in [c.name for c in RemoteDetTable.columns] and "cmes" in [c.name for c in RemoteDetTable.columns]:
                                r_stmt = select(func.max(getattr(RemoteDetTable.c, check_col_nasiento))).where(
                                    RemoteDetTable.c.cper == gp_periodo_str,
                                    RemoteDetTable.c.cmes == gp_mes_str
                                )
                            else:
                                r_stmt = select(func.max(getattr(RemoteDetTable.c, check_col_nasiento)))
                            remote_max = f_conn.execute(r_stmt).scalar() or 0
                except Exception as e:
                    print(f"Error fetching remote max nasiento for {gp_periodo_str}-{gp_mes_str}: {e}")
                    
            local_max = 0
            if DetTable is not None:
                check_col_nasiento = sub.col_destino_nasiento or "nasiento"
                if check_col_nasiento in det_cols:
                    if not is_global_correlative and "cper" in det_cols and "cmes" in det_cols:
                        stmt_nas = db.query(func.max(getattr(DetTable.c, check_col_nasiento))).filter(
                            DetTable.c.company_id == company_id,
                            DetTable.c.subcategoria_id == sub.id,
                            DetTable.c.cper == gp_periodo_str,
                            DetTable.c.cmes == gp_mes_str,
                            DetTable.c.estado == "MIGRADO"
                        )
                    else:
                        stmt_nas = db.query(func.max(getattr(DetTable.c, check_col_nasiento))).filter(
                            DetTable.c.company_id == company_id,
                            DetTable.c.subcategoria_id == sub.id,
                            DetTable.c.estado == "MIGRADO"
                        )
                    local_max = db.execute(stmt_nas).scalar() or 0
                    
            if getattr(sub, "asiento_inicial", None) is not None:
                asiento_ini_val = int(sub.asiento_inicial)
            else:
                asiento_ini_val = max(remote_max, local_max) + 1
                
            new_corr = AsientoCorrelativo(
                company_id=company_id,
                subcategoria_id=sub.id,
                periodo=gp_periodo_str,
                mes=gp_mes_str,
                asiento_inicial=asiento_ini_val,
                asiento_actual=asiento_ini_val - 1
            )
            db.add(new_corr)
            db.flush()
            nasiento_base = asiento_ini_val
            
        df.loc[gp_df.index, 'nasiento'] = gp_df.groupby(clave_columns, dropna=False).ngroup() + nasiento_base
    
    # Update the global counter with the max nasiento generated in this subcategory
    counters_por_asiento[nasiento_key] = df['nasiento'].max() if not df.empty else counters_por_asiento[nasiento_key]


    # ─── OPTIMIZACIÓN: Evaluar Fórmulas Vectorizadas en todo el DF de una vez ───

    # 1. Cabeceras (CfDiario) - Solo necesitamos 1 por 'nasiento'
    header_df = df.drop_duplicates(subset=['nasiento']).copy()
    
    if sub.mapeo_cabecera:
        for field, formula in sub.mapeo_cabecera.items():
            header_df[f"_head_{field}"] = evaluate_formula_on_df(header_df, formula, db, company_id, default="", db_engine=db.bind)

    diario_entries = []
    
    def get_head_val(row, field: str, default: Any):
        if not sub.mapeo_cabecera or field not in sub.mapeo_cabecera: 
            return default
        val = row.get(f"_head_{field}")
        if pd.isna(val):
            return default
        if isinstance(val, str):
            if val.strip() == "" and len(val) > 0:
                # Previene borrar " " intencionales del usuario
                return val
            val = val.strip()
            if val == "":
                return default 
        return val

    if generate_headers and HeadTable is not None:
        for _, h_row in header_df.iterrows():
            row_dict = {
                "company_id": company_id,
                "subcategoria_id": sub.id,
                "lote_id": global_lote_id,
                "estado": "1",
                "nasiento": h_row["nasiento"],
                "idcontrol": str(h_row["idcontrol"]) if "idcontrol" in header_df.columns else None
            }
            
            if sub.col_destino_nasiento and sub.col_destino_nasiento in head_cols:
                row_dict[sub.col_destino_nasiento] = h_row["nasiento"]
                
            if sub.mapeo_cabecera:
                for field in sub.mapeo_cabecera.keys():
                    val = get_head_val(h_row, field, None)
                    if val is not None and field in head_cols:
                        row_dict[field] = str(val)[:500] if field == "cglosa" else val

            # Auto-populate period and month if not explicitly mapped by the user
            if "cper" in head_cols and ("cper" not in row_dict or row_dict["cper"] is None or str(row_dict["cper"]).strip() == ""):
                row_dict["cper"] = str(h_row["_row_periodo"])
            if "cmes" in head_cols and ("cmes" not in row_dict or row_dict["cmes"] is None or str(row_dict["cmes"]).strip() == ""):
                row_dict["cmes"] = str(h_row["_row_mes"])
                        
            diario_entries.append(row_dict)
            
        all_validation_errors = []
        if diario_entries:
            try:
                # Obtener restricciones reales del destino final para validar
                head_dest_constraints = _get_dest_constraints_from_final(
                    company_id, tabla_head_name,
                    sub.schema_destino or "public", db
                )
                
                # Validar registros de cabecera
                validation_errors = _validate_records_against_schema(
                    diario_entries, HeadTable,
                    sub.tabla_destino_cabecera or "cf_diario", sub.id,
                    dest_constraints=head_dest_constraints
                )
                if validation_errors:
                    all_validation_errors.extend(validation_errors)
            except Exception as e:
                print(f"Error parseando reglas de validación en cabecera: {e}")

    # 2. Detalles (CfDiariol) - Por Línea
    diariol_entries = []
    
    # Pre-identify all possible keys across ALL lines of this subcategory (Unified Schema)
    # SQLAlchemy bulk insert requires all dictionaries in the batch to have exactly the same keys.
    all_possible_keys = {
        "company_id", "subcategoria_id", "lote_id", "estado", "nasiento", "nidlin",
        "ndebes", "nhabers", "ndebed", "nhaberd", "ntot", "ntots", "ntotd", "idcontrol"
    }
    for linea in sub.lineas_asiento:
        if linea.mapeo_detalle:
            for f in linea.mapeo_detalle.keys():
                if f in det_cols: all_possible_keys.add(f)
    if sub.col_destino_nasiento: all_possible_keys.add(sub.col_destino_nasiento)
    if sub.col_destino_nidlin: all_possible_keys.add(sub.col_destino_nidlin)
    if "cper" in det_cols: all_possible_keys.add("cper")
    if "cmes" in det_cols: all_possible_keys.add("cmes")

    counters_por_asiento = {}

    for linea in lineas:
        if not linea.mapeo_detalle: continue
        
        # Extraer data de tabla origen para esta línea (aplicando filtros y condiciones)
        temp_df = df.copy()

        # Condición de aplicación
        if getattr(linea, "condicion_aplicacion", None):
            try:
                mask = evaluate_formula_on_df(temp_df, linea.condicion_aplicacion, db, company_id, default=False, db_engine=db.bind)
                mask = pd.to_numeric(mask, errors='coerce').fillna(0).astype(bool) | (mask.astype(str).str.strip().str.upper() == 'TRUE')
                temp_df = temp_df[mask]
            except Exception as e:
                print(f"Error eval cond: {e}")
                continue
        
        if temp_df.empty:
            continue

        # Evaluar todas las fórmulas de detalle sobre el df de la línea
        for db_field, formula in linea.mapeo_detalle.items():
            temp_df[f"_calc_{db_field}"] = evaluate_formula_on_df(temp_df, formula, db, company_id, default="", db_engine=db.bind)

        # Si el nivel es CABECERA, conservamos solo una fila por nasiento
        if linea.nivel == "CABECERA":
            temp_df = temp_df.drop_duplicates(subset=['nasiento'])

        # Iterar sobre DataFrame procesado
        for _, row_calc in temp_df.iterrows():
            def get_det_val(field: str, default: Any = None, type_cast=str):
                col = f"_calc_{field}"
                if col not in row_calc: return default
                val = row_calc[col]
                if pd.isna(val): return default
                
                val_str = str(val).strip()
                if val_str == "":
                    # Special handling for user's request: allow " " for strings only.
                    if type_cast is str and isinstance(val, str) and len(val) > 0:
                        return str(val)
                    
                    if type_cast in [float, int]:
                        return type_cast(0)
                    return default
                
                if type_cast is str:
                    s_val = str(val).strip()
                    if s_val.endswith(".0"):
                        s_val = s_val[:-2].strip()
                    return s_val
                
                # Numeric cast
                try:
                    return type_cast(val)
                except:
                    return default

            # Lógica cronológica de Línea por asiento leyendo de DB
            curr_nasiento = row_calc['nasiento']
            
            # Use a unique key for the current nasiento to track nidlin
            nidlin_key = f"nidlin-{curr_nasiento}"
            if nidlin_key not in counters_por_asiento:
                max_in_db = 0
                if DetTable is not None:
                    check_col_name = sub.col_destino_nidlin or "nidlin"
                    if check_col_name in det_cols:
                        stmt = db.query(func.max(getattr(DetTable.c, check_col_name))).filter(
                            DetTable.c.company_id == company_id,
                            DetTable.c.estado == "PENDIENTE"
                        )
                        if "nasiento" in det_cols:
                            stmt = stmt.filter(DetTable.c.nasiento == curr_nasiento)
                        elif sub.col_destino_nasiento and sub.col_destino_nasiento in det_cols:
                            stmt = stmt.filter(getattr(DetTable.c, sub.col_destino_nasiento) == curr_nasiento)
                        
                        max_in_db = db.execute(stmt).scalar() or 0
                counters_por_asiento[nidlin_key] = max_in_db
                
            counters_por_asiento[nidlin_key] += 1
            curr_nidlin = counters_por_asiento[nidlin_key]

            # 2. Initialize dictionary with all possible keys as None (Unified Schema)
            row_dict = {k: None for k in all_possible_keys}
            row_dict.update({
                "company_id": company_id,
                "subcategoria_id": sub.id,
                "lote_id": global_lote_id,
                "estado": "1",
                "nasiento": curr_nasiento,
                "nidlin": curr_nidlin,
                "idcontrol": str(row_calc['idcontrol']) if 'idcontrol' in row_calc else None
            })
            
            # Default period and month fallbacks
            if "cper" in det_cols:
                row_dict["cper"] = str(row_calc["_row_periodo"])
            if "cmes" in det_cols:
                row_dict["cmes"] = str(row_calc["_row_mes"])
            
            # Auto-populate clecvper and cledmcper with cper if not explicitly mapped
            if "clecvper" in det_cols and ("clecvper" not in row_dict or row_dict["clecvper"] is None):
                row_dict["clecvper"] = str(row_calc["_row_periodo"])
            if "cledmcper" in det_cols and ("cledmcper" not in row_dict or row_dict["cledmcper"] is None):
                row_dict["cledmcper"] = str(row_calc["_row_periodo"])
            
            row_dict["_aplica_ajuste_redondeo"] = getattr(linea, "aplica_ajuste_redondeo", False)

            # 3. Dynamic Mapping: Process ALL fields defined in the mapping
            # This satisfies the user's request to generate ALL columns correctly
            for db_field in linea.mapeo_detalle.keys():
                if db_field not in det_cols: continue
                
                # Determine type from SQLAlchemy column if possible
                target_col = DetTable.c.get(db_field)
                type_cast = str
                is_date = False
                if target_col is not None:
                    from sqlalchemy import Numeric, Integer, Float, Date
                    if isinstance(target_col.type, (Numeric, Float)):
                        type_cast = float
                    elif isinstance(target_col.type, Integer):
                        type_cast = int
                    elif isinstance(target_col.type, Date):
                        is_date = True
                
                # Special date casting logic
                if is_date:
                    def safe_date_cast(v):
                        if v is None: return None
                        v_str = str(v).strip()
                        if v_str == "": return None
                        # If it already looks like a date (contains - or /), keep it for DB to parse
                        if "-" in v_str or "/" in v_str: return v_str
                        return None # Not a valid date string
                    
                    val = get_det_val(db_field, None, str)
                    val = safe_date_cast(val)
                else:
                    val = get_det_val(db_field, None, type_cast)
                
                if val is not None:
                    # Truncate strings if necessary (like cglosa)
                    if type_cast is str and db_field in ["cglosa", "cglosa2"]:
                        row_dict[db_field] = str(val)[:500]
                    else:
                        row_dict[db_field] = val

            # 4. Automatic Calculations (Debe/Haber Soles/Dólares)
            # Only calculate if the user DID NOT explicitly map these columns
            if "ndebe" in row_dict or "nhaber" in row_dict:
                ndebe = float(row_dict.get("ndebe", 0.0) or 0.0)
                nhaber = float(row_dict.get("nhaber", 0.0) or 0.0)
                ntc = float(row_dict.get("ntc", 1.0) or 1.0)
                ccodmon = str(row_dict.get("ccodmon", "S") or "S")

                # Default Calculations logic
                auto_vals = {
                    "ndebes": ndebe if ccodmon == "S" else round(ndebe * ntc, 4),
                    "nhabers": nhaber if ccodmon == "S" else round(nhaber * ntc, 4),
                    "ndebed": ndebe if ccodmon == "D" else round((ndebe / ntc if ntc else 0), 4),
                    "nhaberd": nhaber if ccodmon == "D" else round((nhaber / ntc if ntc else 0), 4),
                    "ntot": round(ndebe + nhaber, 4)
                }
                auto_vals["ntots"] = round(auto_vals["ndebes"] + auto_vals["nhabers"], 4)
                auto_vals["ntotd"] = round(auto_vals["ndebed"] + auto_vals["nhaberd"], 4)
                
                # Only apply auto formulas if the user hasn't explicitly mapped them
                updates = {}
                for k, v in auto_vals.items():
                    # explicitly disable auto-update if mapped and value is not None
                    user_val = row_dict.get(k)
                    if k not in linea.mapeo_detalle or user_val is None:
                        updates[k] = v
                    elif curr_nasiento == 1:
                        print(f"DEBUG: Preserving user {k} = {user_val} (mapped: {linea.mapeo_detalle.get(k)})")
                
                row_dict.update(updates)

            # 5. Global Correlative Column Overrides
            if sub.col_destino_nasiento and sub.col_destino_nasiento in det_cols:
                row_dict[sub.col_destino_nasiento] = curr_nasiento
                
            if sub.col_destino_nidlin and sub.col_destino_nidlin in det_cols:
                row_dict[sub.col_destino_nidlin] = curr_nidlin

            diariol_entries.append(row_dict)

    # ─── Filtrado de Ceros y Cuadre de Redondeo (Ajustes Automáticos) ───
    if generate_details and diariol_entries:
        pares_redondeo = getattr(sub, 'pares_redondeo', []) or []
        
        # 1. (Funcionalidad de omitir ceros requerida eliminar según pedido del usuario)
        
        # 2. Cuadre de Redondeo (agrupando por nasiento)
        if pares_redondeo:
            import itertools
            diariol_entries.sort(key=lambda x: str(x.get("nasiento", "")))
            
            for nasiento, group_iter in itertools.groupby(diariol_entries, key=lambda x: str(x.get("nasiento", ""))):
                group = list(group_iter)
                if not group: continue
                
                adj_line = next((r for r in group if r.get("_aplica_ajuste_redondeo", False) == True), None)
                if not adj_line: continue
                
                for par in pares_redondeo:
                    col_debe = par.get("debe")
                    col_haber = par.get("haber")
                    if not col_debe or not col_haber: continue

                    sum_debe = round(sum(float(r.get(col_debe) or 0.0) for r in group), 4)
                    sum_haber = round(sum(float(r.get(col_haber) or 0.0) for r in group), 4)
                    diff = round(sum_debe - sum_haber, 4)
                    
                    if abs(diff) > 0.0001:
                        v_debe = float(adj_line.get(col_debe) or 0.0)
                        v_haber = float(adj_line.get(col_haber) or 0.0)
                        
                        if diff > 0: # DEBE > HABER (Diferencia Positiva)
                            if v_haber > 0: adj_line[col_haber] = round(v_haber + diff, 4)
                            elif v_debe > 0: adj_line[col_debe] = round(max(0, v_debe - diff), 4)
                            else: adj_line[col_haber] = round(diff, 4)
                        else: # HABER > DEBE (Diferencia Negativa)
                            diff_abs = abs(diff)
                            if v_debe > 0: adj_line[col_debe] = round(v_debe + diff_abs, 4)
                            elif v_haber > 0: adj_line[col_haber] = round(max(0, v_haber - diff_abs), 4)
                            else: adj_line[col_debe] = round(diff_abs, 4)

        # 3. Limpiar marca temporal
        for entry in diariol_entries:
            entry.pop("_aplica_ajuste_redondeo", None)

    rows_inserted = 0
    if generate_details and diariol_entries and DetTable is not None:
        # Validar registros de detalle antes de insertar
        det_dest_constraints = _get_dest_constraints_from_final(
            company_id, tabla_det_name,
            sub.schema_destino or "public", db
        )
        
        # Validar registros de detalle antes de insertar
        det_dest_constraints = _get_dest_constraints_from_final(
            company_id, tabla_det_name,
            sub.schema_destino or "public", db
        )
        
        validation_errors = _validate_records_against_schema(
            diariol_entries, DetTable,
            sub.tabla_destino_detalle or "cf_diariol", sub.id,
            dest_constraints=det_dest_constraints
        )
        if validation_errors:
            # En lugar de fallar, recolectar los errores para mandarlos de vuelta
            if 'all_validation_errors' in locals():
                all_validation_errors.extend(validation_errors)
            else:
                all_validation_errors = validation_errors

    # Ahora marcamos errores y guardamos todo
    if 'all_validation_errors' not in locals():
        all_validation_errors = []
        
    error_nasientos = set(err.get("nasiento") for err in all_validation_errors if err.get("nasiento"))
    
    # Update status for Headers and Insert
    # IMPORTANT: Filter out orphan headers (headers without any matching detail lines).
    # This happens when ALL lineas_asiento have condicion_aplicacion that excludes certain
    # source rows. Those rows still get headers generated, but no details.
    if generate_headers and diario_entries and HeadTable is not None:
        if generate_details:
            nasientos_con_detalle = set(e.get("nasiento") for e in diariol_entries if e.get("nasiento") is not None)
            orphan_count = sum(1 for e in diario_entries if e.get("nasiento") not in nasientos_con_detalle)
            if orphan_count > 0:
                print(f"FILTRO CABECERAS: Eliminando {orphan_count} cabeceras huérfanas (sin detalles) de {len(diario_entries)} totales")
                diario_entries = [e for e in diario_entries if e.get("nasiento") in nasientos_con_detalle]
        
        for entry in diario_entries:
            if entry.get("nasiento") in error_nasientos:
                entry["estado"] = "0"
        if diario_entries:
            try:
                db.execute(HeadTable.insert(), diario_entries)
            except Exception as e:
                print(f"Error insertando registros cabecera dinámicos: {e}")

    # Update status for Details and Insert
    if generate_details and diariol_entries and DetTable is not None:
        for entry in diariol_entries:
            if entry.get("nasiento") in error_nasientos:
                entry["estado"] = "0"
        try:
            db.execute(DetTable.insert(), diariol_entries)
            rows_inserted = len(diariol_entries)
        except Exception as e:
            db.rollback()
            print(f"CRITICAL Error inserting detail records for subcat {sub.id}: {e}")
            return 0, 0, all_validation_errors

    # ─── Actualizar Control Incremental y Asiento Inicial ───
    try:
        def _get_nas_safe(e):
            try: return int(e.get("nasiento", 0))
            except: return 0

        max_nasiento = 0
        if diariol_entries:
            max_nasiento = max((_get_nas_safe(e) for e in diariol_entries), default=0)
        elif diario_entries:
            max_nasiento = max((_get_nas_safe(e) for e in diario_entries), default=0)

        # No actualizamos sub.asiento_inicial ni asiento_actual en este paso de staging.
        # El correlativo de asiento inicial solo se actualiza de los asientos migrados a Contasis final.
        pass

        if 'ctrl_col' in locals() and ctrl_col and not df.empty:
            cols_split = [c.strip() for c in ctrl_col.split(",")]
            actual_cols = []
            for c in cols_split:
                match = next((col for col in df.columns if col.lower() == c.lower()), None)
                if match: actual_cols.append(match)

            if len(actual_cols) > 0:
                valid_entries = [e for e in diariol_entries if e.get("estado") != "0"]
                if valid_entries or not error_nasientos:
                    max_val = None
                    if len(actual_cols) > 1 and '_incremental_key' in df.columns:
                        max_val = df['_incremental_key'].max()
                    elif len(actual_cols) == 1:
                        max_val = df[actual_cols[0]].max()

                    if max_val is not None and str(max_val).strip() != "":
                        print(f"GUARDANDO CONTROL INCREMENTAL [subcat={sub.id}]: {max_val}")
                        db.execute(
                            text("UPDATE mapeo_subcategorias SET last_generated_control_value = :val WHERE id = :id"),
                            {"val": str(max_val), "id": sub.id}
                        )
                        db.commit()
    except Exception as e:
        print(f"Error actualizando control incremental o asiento inicial: {e}")

    return rows_inserted, len(diario_entries) if generate_headers else 0, all_validation_errors


@router.post("/generate-to-cf-diariol")
@track_io("generate_cf_diariol")
def generate_to_cf_diariol(body: dict, db: Session = Depends(get_dest_db)):
    """
    Genera asientos contables directamente en la tabla cf_diariol (staging en migconta_db).
    Misma lógica que generate-asientos pero escribe en CfDiariol en lugar de AsientoContableGenerado.
    """
    from datetime import datetime
    import uuid
    from backend.app.models.models import CfDiariol, MapeoCategoria, MapeoSubcategoria, CfDiario

    company_id = body.get("company_id")
    raw_subcat = body.get("subcategoria_id")
    
    try:
        # Manejar subcategoria_id vacío, null o string vacío
        subcategoria_id = None
        if raw_subcat and str(raw_subcat).strip() != "" and str(raw_subcat) != "0":
            try:
                subcategoria_id = int(raw_subcat)
            except ValueError:
                subcategoria_id = None
    
        clear_previous = body.get("clear_previous", False)
        # Forzar auto-limpieza si se genera para UNA subcategoría para evitar duplicados
        if subcategoria_id is not None:
            clear_previous = True

        filters = body.get("filters", [])
    
        # _log(f"subcategoria_id={subcategoria_id} (raw={raw_subcat}), company_id={company_id}, clear={clear_previous}")
    
        subs_to_process = []
        if subcategoria_id is not None:
            sub = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.id == subcategoria_id).first()
            if not sub: raise HTTPException(status_code=404, detail="Subcategoría no encontrada")
            subs_to_process.append(sub)
            if not company_id: company_id = sub.categoria.company_id
        elif company_id:
            categorias = db.query(MapeoCategoria).filter(
                MapeoCategoria.company_id == company_id,
                MapeoCategoria.is_active == True
            ).all()
            for cat in categorias:
                for sub in cat.subcategorias:
                    if sub.is_active and sub.tabla_origen:
                        subs_to_process.append(sub)
            if not subs_to_process:
                raise HTTPException(status_code=400, detail="No hay subcategorías activas configuradas para esta empresa")
        else:
            raise HTTPException(status_code=400, detail="Debe proporcionar subcategoria_id o company_id")
    
        # _log(f"subs_to_process count = {len(subs_to_process)}: {[s.id for s in subs_to_process]}")
    # generate_headers / generate_details ahora se leen por subcategoría desde la BD

        if clear_previous:
            try:
                from sqlalchemy import Table, MetaData
                from backend.app.core.database import dest_engine as engine
                metadata = MetaData()
                
                for sub in subs_to_process:
                    tabla_head_name = sub.tabla_destino_cabecera or "cf_diario"
                    tabla_det_name = sub.tabla_destino_detalle or "cf_diariol"
                    
                    try: DetTable = Table(tabla_det_name, metadata, autoload_with=engine)
                    except: DetTable = None
                        
                    asientos_to_delete = []
                    
                    # We identify nasiento to delete primarily from DetTable mapping
                    if DetTable is not None:
                        check_col_nasiento = sub.col_destino_nasiento or "nasiento"
                        if check_col_nasiento in [c.name for c in DetTable.columns]:
                            stmt_sel = db.query(getattr(DetTable.c, check_col_nasiento)).filter(
                                DetTable.c.company_id == company_id,
                                DetTable.c.estado.in_(["0", "1", "PENDIENTE"]),
                                DetTable.c.subcategoria_id == sub.id
                            ).distinct()
                            asientos_to_delete = [a[0] for a in db.execute(stmt_sel).fetchall() if a[0]]
                    
                    if (sub.generate_details is not False) and DetTable is not None:
                        stmt_del_l = DetTable.delete().where(
                            DetTable.c.company_id == company_id,
                            DetTable.c.estado.in_(["0", "1", "PENDIENTE", "ERROR"]),
                            DetTable.c.subcategoria_id == sub.id
                        )
                        db.execute(stmt_del_l)
    
                    if sub.generate_headers is not False:
                        try: HeadTable = Table(tabla_head_name, metadata, autoload_with=engine)
                        except: HeadTable = None
                        
                        if HeadTable is not None:
                            check_col_head = sub.col_destino_nasiento or "nasiento"
                            if "subcategoria_id" in [c.name for c in HeadTable.columns]:
                                stmt_del_c = HeadTable.delete().where(
                                    HeadTable.c.company_id == company_id,
                                    HeadTable.c.estado.in_(["0", "1", "PENDIENTE", "SIN_DETALLE", "ERROR"]),
                                    HeadTable.c.subcategoria_id == sub.id
                                )
                                db.execute(stmt_del_c)
                            elif check_col_head in [c.name for c in HeadTable.columns] and asientos_to_delete:
                                stmt_del_c = HeadTable.delete().where(
                                    HeadTable.c.company_id == company_id,
                                    HeadTable.c.estado.in_(["0", "1", "PENDIENTE", "SIN_DETALLE", "ERROR"]),
                                    getattr(HeadTable.c, check_col_head).in_(asientos_to_delete)
                                )
                                db.execute(stmt_del_c)

                    # Reset subcategory control value to None so extraction restarts from scratch
                    sub.last_generated_control_value = None

                    # Reset the seat correlatives based on actual migrated seats in staging
                    try:
                        from backend.app.models.models import AsientoCorrelativo
                        from sqlalchemy import select, func
                        corrs = db.query(AsientoCorrelativo).filter(
                            AsientoCorrelativo.company_id == company_id,
                            AsientoCorrelativo.subcategoria_id == sub.id
                        ).all()
                        for corr in corrs:
                            if DetTable is not None:
                                check_col_nasiento = sub.col_destino_nasiento or "nasiento"
                                if check_col_nasiento in [c.name for c in DetTable.columns]:
                                    is_global = (corr.periodo == "GLOBAL" and corr.mes == "00") or ("cper" not in [c.name for c in DetTable.columns] or "cmes" not in [c.name for c in DetTable.columns])
                                    if is_global:
                                        stmt_max_mig = select(func.max(getattr(DetTable.c, check_col_nasiento))).where(
                                            DetTable.c.company_id == company_id,
                                            DetTable.c.subcategoria_id == sub.id,
                                            DetTable.c.estado == "MIGRADO"
                                        )
                                    else:
                                        stmt_max_mig = select(func.max(getattr(DetTable.c, check_col_nasiento))).where(
                                            DetTable.c.company_id == company_id,
                                            DetTable.c.subcategoria_id == sub.id,
                                            DetTable.c.cper == corr.periodo,
                                            DetTable.c.cmes == corr.mes,
                                            DetTable.c.estado == "MIGRADO"
                                        )
                                    max_mig = db.execute(stmt_max_mig).scalar()
                                    if max_mig is not None:
                                        corr.asiento_actual = int(max_mig)
                                    else:
                                        corr.asiento_actual = corr.asiento_inicial - 1
                                else:
                                    if getattr(corr, "asiento_actual", None) is None:
                                        corr.asiento_actual = corr.asiento_inicial - 1
                            else:
                                if getattr(corr, "asiento_actual", None) is None:
                                    corr.asiento_actual = corr.asiento_inicial - 1
                    except Exception as ex_corr:
                        print(f"Error resetting correlativos in generate_to_cf_diariol: {ex_corr}")
    
                db.commit()
            except Exception as e:
                db.rollback()
                import traceback
                # _log(f"Error al limpiar asientos previos: {e}\n{traceback.format_exc()}")
                raise HTTPException(status_code=500, detail=f"Error al limpiar asientos previos: {e}")
    
        lote_id = str(uuid.uuid4())[:8].upper()
        total_generated = 0
        total_asientos = 0
        all_validation_errors = []
        
        global_counters = {}
    
        for sub in subs_to_process:
            try:
                gen, asis, v_errors = _generate_subcategoria_cf_diariol(
                    sub, db, company_id, filters, lote_id, global_counters,
                    generate_headers=(sub.generate_headers is not False),
                    generate_details=(sub.generate_details is not False),
                    is_realtime=body.get("is_realtime", False) if isinstance(body, dict) else False
                )
                total_generated += gen
                total_asientos += asis
                if v_errors:
                    all_validation_errors.extend(v_errors)
                db.flush()
            except HTTPException:
                raise
            except Exception as e:
                db.rollback()
                import traceback
                # _log(f"ERROR generando subcategoría {sub.id}: {e}")
                # _log(traceback.format_exc())
                continue
    
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error al guardar asientos generados: {str(e)}")

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        err_msg = f"{e}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=err_msg)
        
    subcat_msg = "todas las subcategorías" if not subcategoria_id else f"la subcategoría {subcategoria_id}"
    return {
        "message": f"Se generaron {total_generated} líneas ({total_asientos} asientos) para {subcat_msg}",
        "lote_id": lote_id,
        "generated": total_generated,
        "asientos": total_asientos,
        "errors": all_validation_errors
    }


@router.post("/clear-local-staging/{company_id}")
def clear_local_staging(
    company_id: int, 
    subcategoria_id: Optional[int] = None, 
    db: Session = Depends(get_dest_db)
):
    """
    Vacía los asientos generados localmente (cabecera y detalle) en migconta_db para reiniciar pruebas.
    """
    from backend.app.models.models import MapeoSubcategoria
    from sqlalchemy import Table, MetaData
    
    try:
        from backend.app.models.models import MapeoCategoria
        
        query = db.query(MapeoSubcategoria).join(MapeoCategoria).filter(
            MapeoCategoria.company_id == company_id,
            MapeoSubcategoria.is_active == True
        )
        if subcategoria_id:
            query = query.filter(MapeoSubcategoria.id == subcategoria_id)
        subs = query.all()
        
        metadata = MetaData()
        engine = db.get_bind()
        
        for sub in subs:
            tabla_head = sub.tabla_destino_cabecera or "cf_diario"
            tabla_det = sub.tabla_destino_detalle or "cf_diariol"
            
            # Limpiar Detalles
            try: DetTable = Table(tabla_det, metadata, autoload_with=engine)
            except: DetTable = None
            if DetTable is not None:
                db.execute(DetTable.delete().where(
                    DetTable.c.company_id == company_id,
                    DetTable.c.subcategoria_id == sub.id
                ))
                
            # Limpiar Cabeceras
            try: HeadTable = Table(tabla_head, metadata, autoload_with=engine)
            except: HeadTable = None
            if HeadTable is not None:
                db.execute(HeadTable.delete().where(
                    HeadTable.c.company_id == company_id,
                    HeadTable.c.subcategoria_id == sub.id
                ))
            
            # Reset asiento inicial correlativo
            sub.last_generated_control_value = None
            
            # Reset seat correlativos for this subcategory to the configured start value
            try:
                from backend.app.models.models import AsientoCorrelativo
                corrs = db.query(AsientoCorrelativo).filter(
                    AsientoCorrelativo.company_id == company_id,
                    AsientoCorrelativo.subcategoria_id == sub.id
                ).all()
                for corr in corrs:
                    corr.asiento_actual = corr.asiento_inicial - 1
            except Exception as ex_corr:
                print(f"Error resetting correlativos in clear_local_staging: {ex_corr}")
            
        db.commit()
        return {"message": "Datos locales vaciados correctamente."}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al vaciar datos locales: {str(e)}")



def _migrate_to_final_internal(
    company_id: int,
    lote_id: Optional[str] = None,
    allow_overwrite: bool = False,
    subcategoria_id: Optional[int] = None,
    db: Optional[Session] = None
):
    """
    Migra registros PENDIENTE de cf_diariol (staging en migconta_db) al destino final de Contasis.
    Conecta a la BD de Contasis usando FinalDestConnection y hace INSERT bulk en cf_diariol.
    Si subcategoria_id se provee, solo migra esa subcategoría.
    Si allow_overwrite es True, eliminará los asientos coincidentes en Contasis antes de insertar para permitir modificaciones.
    """
    from backend.app.models.models import FinalDestConnection, MapeoCategoria, MapeoSubcategoria, AsientoCorrelativo
    from backend.app.services.connection_manager import ConnectionManager
    from sqlalchemy import Table, MetaData, text
    from backend.app.core.database import dest_engine as local_engine, get_dest_db

    # Obtener sesión de base de datos si no se proporcionó
    if db is None:
        db = next(get_dest_db())
        should_close_db = True
    else:
        should_close_db = False

    # Obtener conexión destino final
    final_conn = db.query(FinalDestConnection).filter(
        FinalDestConnection.company_id == company_id,
        FinalDestConnection.is_active == True
    ).first()
    if not final_conn:
        raise HTTPException(status_code=404, detail="No hay conexión destino final configurada para esta empresa")

    query = db.query(MapeoSubcategoria).join(MapeoCategoria).filter(
        MapeoCategoria.company_id == company_id,
        MapeoSubcategoria.is_active == True
    )
    if subcategoria_id:
        query = query.filter(MapeoSubcategoria.id == subcategoria_id)
    subcategorias = query.all()
    
    if not subcategorias:
        return {"message": "No hay subcategorías activas para migrar", "migrated_lineas": 0, "migrated_cabeceras": 0}

    try:
        conn_data = {
            "host": final_conn.host, "port": final_conn.port,
            "database_name": final_conn.database_name,
            "username": final_conn.username, "password": final_conn.password
        }
        final_engine = ConnectionManager.get_dest_engine(conn_data)

        migrated_lineas = 0
        migrated_cabeceras = 0
        failed_rows_raw = []
        metadata_local = MetaData()
        metadata_final = MetaData()

        with final_engine.begin() as final_db:
            for sub in subcategorias:
                head_table_name = sub.tabla_destino_cabecera or "cf_diario"
                det_table_name = sub.tabla_destino_detalle or "cf_diariol"

                # Reflect local staging tables
                try: LocalHeadTable = Table(head_table_name, metadata_local, autoload_with=local_engine)
                except: LocalHeadTable = None
                    
                try: LocalDetTable = Table(det_table_name, metadata_local, autoload_with=local_engine)
                except: LocalDetTable = None

                # Reflect target final tables
                try: FinalHeadTable = Table(head_table_name, metadata_final, autoload_with=final_engine)
                except: FinalHeadTable = None
                    
                try: FinalDetTable = Table(det_table_name, metadata_final, autoload_with=final_engine)
                except: FinalDetTable = None

                # Build unified target lists
                target_estado = "1"
                nasiento_col = sub.col_destino_nasiento or "nasiento"
                cabeceras_rows = []
                if LocalHeadTable is not None and FinalHeadTable is not None:
                    stmt_c = LocalHeadTable.select().where(
                        LocalHeadTable.c.company_id == company_id,
                        LocalHeadTable.c.estado == target_estado,
                        LocalHeadTable.c.subcategoria_id == sub.id
                    )
                    if lote_id: stmt_c = stmt_c.where(LocalHeadTable.c.lote_id == lote_id)
                    cabeceras_rows = db.execute(stmt_c).fetchall()

                detalle_rows = []
                if LocalDetTable is not None and FinalDetTable is not None:
                    stmt_l = LocalDetTable.select().where(
                        LocalDetTable.c.company_id == company_id,
                        LocalDetTable.c.estado == target_estado,
                        LocalDetTable.c.subcategoria_id == sub.id
                    )
                    if lote_id: stmt_l = stmt_l.where(LocalDetTable.c.lote_id == lote_id)
                    detalle_rows = db.execute(stmt_l).fetchall()

                # Detect migration mode based on subcategory configuration:
                # Mode A (seat-by-seat): generate_headers=True → standard accounting (cf_diario + cf_diariol)
                # Mode B (row-by-row):   generate_headers=False → single table direct insert (cg_entitrib, etc.)
                has_accounting_keys = bool(getattr(sub, 'generate_headers', True))

                remote_head_cols = [c.name for c in FinalHeadTable.columns] if FinalHeadTable is not None else []
                remote_det_cols = [c.name for c in FinalDetTable.columns] if FinalDetTable is not None else []

                if has_accounting_keys:
                    # ═══ MODE A: Seat-by-seat migration (standard cf_diario/cf_diariol) ═══
                    seats = {}
                    for row in cabeceras_rows:
                        r_d = row._mapping
                        ccodori_val = str(r_d.get('ccodori')).strip() if r_d.get('ccodori') is not None else None
                        seat_key = (r_d.get('cper'), r_d.get('cmes'), ccodori_val, r_d.get(nasiento_col))
                        seats[seat_key] = {'header': r_d, 'details': []}

                    for row in detalle_rows:
                        r_d = row._mapping
                        ccodori_val = str(r_d.get('ccodori')).strip() if r_d.get('ccodori') is not None else None
                        seat_key = (r_d.get('cper'), r_d.get('cmes'), ccodori_val, r_d.get(nasiento_col))
                        if seat_key not in seats:
                            seats[seat_key] = {'header': None, 'details': []}
                        seats[seat_key]['details'].append(r_d)

                    for seat_key, data in seats.items():
                        if any(x is None for x in seat_key):
                            failed_rows_raw.append({"seat": "Clave Incompleta", "error": "Llaves maestras (cper, cmes, ccodori o nasiento) vacías"})
                            continue

                        # Skip orphan headers: headers without any detail lines should NOT be migrated.
                        # This can happen when condicion_aplicacion on all lineas_asiento excludes certain source rows.
                        if data['header'] and not data['details']:
                            p, m, o, n = seat_key
                            print(f"MIGRATE SKIP: Cabecera huérfana {p}-{m}-{o}-{n} (sin detalles), marcando como ERROR localmente")
                            # Mark as ERROR locally so it doesn't keep trying to migrate
                            if LocalHeadTable is not None:
                                try:
                                    db.execute(LocalHeadTable.update().where(
                                        LocalHeadTable.c.company_id == company_id,
                                        LocalHeadTable.c.subcategoria_id == sub.id,
                                        LocalHeadTable.c.cper == p,
                                        LocalHeadTable.c.cmes == m,
                                        LocalHeadTable.c.ccodori == o,
                                        getattr(LocalHeadTable.c, nasiento_col) == n
                                    ).values(estado="SIN_DETALLE"))
                                except Exception: pass
                            continue

                        p, m, o, n = seat_key
                        
                        # Validate that details have a matching header (prevent ForeignKeyViolation)
                        if not data['header'] and data['details']:
                            header_exists = False
                            if FinalHeadTable is not None:
                                try:
                                    from sqlalchemy import select
                                    stmt_check = select(FinalHeadTable.c[nasiento_col]).where(
                                        FinalHeadTable.c.cper == p,
                                        FinalHeadTable.c.cmes == m,
                                        FinalHeadTable.c.ccodori == o,
                                        getattr(FinalHeadTable.c, nasiento_col) == n
                                    )
                                    header_exists = final_db.execute(stmt_check).first() is not None
                                except Exception as e_check:
                                    print(f"Error checking header existence in target for {p}-{m}-{o}-{n}: {e_check}")
                            
                            if not header_exists:
                                error_msg = f"Asiento huérfano: No posee cabecera en staging ni en la base de datos destino de Contasis."
                                print(f"MIGRATE SKIP: {error_msg} Key: {p}-{m}-{o}-{n}")
                                failed_rows_raw.append({"seat": f"{p}-{m}-{o}-{n}", "error": error_msg, "subcategoria_id": sub.id})
                                continue

                        try:
                            with final_db.begin_nested():
                                if allow_overwrite:
                                    if FinalDetTable is not None:
                                        final_db.execute(FinalDetTable.delete().where(
                                            FinalDetTable.c.cper == p,
                                            FinalDetTable.c.cmes == m,
                                            FinalDetTable.c.ccodori == o,
                                            getattr(FinalDetTable.c, nasiento_col) == n
                                        ))
                                    if FinalHeadTable is not None:
                                        final_db.execute(FinalHeadTable.delete().where(
                                            FinalHeadTable.c.cper == p,
                                            FinalHeadTable.c.cmes == m,
                                            FinalHeadTable.c.ccodori == o,
                                            getattr(FinalHeadTable.c, nasiento_col) == n
                                        ))

                                if data['header'] and FinalHeadTable is not None:
                                    h_dict = {k: v for k, v in data['header'].items() if k in remote_head_cols}
                                    # Aplicar corrección de encoding a campos de texto
                                    for k, v in h_dict.items():
                                        if isinstance(v, str):
                                            h_dict[k] = fix_encoding(v)
                                    final_db.execute(FinalHeadTable.insert(), [h_dict])

                                if data['details'] and FinalDetTable is not None:
                                    d_list = []
                                    for d in data['details']:
                                        insert_item = {}
                                        for k, v in d.items():
                                            if k in remote_det_cols:
                                                if v is not None and hasattr(v, '__float__') and not isinstance(v, str) and str(FinalDetTable.columns[k].type) in ['NUMERIC', 'FLOAT', 'INTEGER']:
                                                    try: insert_item[k] = float(v)
                                                    except: insert_item[k] = None
                                                else:
                                                    # Aplicar corrección de encoding a campos de texto
                                                    if isinstance(v, str):
                                                        insert_item[k] = fix_encoding(v)
                                                    else:
                                                        insert_item[k] = v
                                        d_list.append(insert_item)
                                    final_db.execute(FinalDetTable.insert(), d_list)

                            if data['header'] and LocalHeadTable is not None:
                                db.execute(LocalHeadTable.update().where(
                                    LocalHeadTable.c.company_id == company_id,
                                    LocalHeadTable.c.subcategoria_id == sub.id,
                                    LocalHeadTable.c.cper == p,
                                    LocalHeadTable.c.cmes == m,
                                    LocalHeadTable.c.ccodori == o,
                                    getattr(LocalHeadTable.c, nasiento_col) == n
                                ).values(estado="MIGRADO"))
                                migrated_cabeceras += 1

                            if data['details'] and LocalDetTable is not None:
                                db.execute(LocalDetTable.update().where(
                                    LocalDetTable.c.company_id == company_id,
                                    LocalDetTable.c.subcategoria_id == sub.id,
                                    LocalDetTable.c.cper == p,
                                    LocalDetTable.c.cmes == m,
                                    LocalDetTable.c.ccodori == o,
                                    getattr(LocalDetTable.c, nasiento_col) == n
                                ).values(estado="MIGRADO"))
                                migrated_lineas += len(data['details'])

                        except Exception as e:
                            failed_rows_raw.append({"seat": f"{p}-{m}-{o}-{n}", "error": str(e), "subcategoria_id": sub.id})

                else:
                    # ═══ MODE B: Direct row-by-row bulk insert (single table, no accounting keys) ═══
                    # Used for tables like cg_entitrib that don't follow the cf_diario pattern
                    all_rows = list(detalle_rows) + list(cabeceras_rows)
                    if not all_rows:
                        continue

                    # Determine which local and final tables to use
                    active_local = LocalDetTable if LocalDetTable is not None else LocalHeadTable
                    active_final = FinalDetTable if FinalDetTable is not None else FinalHeadTable
                    active_remote_cols = remote_det_cols if remote_det_cols else remote_head_cols

                    if active_local is None or active_final is None:
                        failed_rows_raw.append({"seat": "Config", "error": f"No se encontró tabla local/final para subcategoría {sub.nombre}", "subcategoria_id": sub.id})
                        continue

                    # Unique key for existence check: prefer remote PK, fallback a candidatos.
                    # Se evalúa SIEMPRE (no solo con allow_overwrite) para evitar
                    # UniqueViolation cuando el registro ya existe en Contasis.
                    remote_pk = [c.name for c in active_final.primary_key.columns]
                    pk_cols = remote_pk if remote_pk and all(c in active_local.columns for c in remote_pk) else []
                    if not pk_cols:
                        for candidate in ['idcontrol', 'codaux', 'rucaux', 'ccodruc']:
                            if candidate in active_final.columns and candidate in active_local.columns:
                                pk_cols = [candidate]
                                break

                    for row in all_rows:
                        r_d = row._mapping
                        row_label = str(r_d.get('idcontrol', r_d.get('codaux', '?')))[:30]
                        try:
                            with final_db.begin_nested():
                                insert_item = {}
                                for k, v in r_d.items():
                                    if k in active_remote_cols:
                                        if v is not None and hasattr(v, '__float__') and not isinstance(v, str) and str(active_final.columns[k].type) in ['NUMERIC', 'FLOAT', 'INTEGER']:
                                            try: insert_item[k] = float(v)
                                            except: insert_item[k] = None
                                        elif isinstance(v, str):
                                            # Aplicar corrección de encoding específica para caracteres corruptos UTF-8
                                            insert_item[k] = fix_encoding(v)
                                        else:
                                            insert_item[k] = v

                                # Chequeo de existencia por PK remota (siempre activo)
                                exists = False
                                if pk_cols and all(r_d.get(c) is not None for c in pk_cols):
                                    from sqlalchemy import select
                                    where_clause = None
                                    for c in pk_cols:
                                        cond = getattr(active_final.c, c) == r_d.get(c)
                                        where_clause = cond if where_clause is None else where_clause & cond
                                    if 'company_id' in active_final.columns and r_d.get('company_id') is not None:
                                        where_clause = where_clause & (active_final.c.company_id == r_d.get('company_id'))
                                    exists = final_db.execute(
                                        select(active_final.c[pk_cols[0]]).where(where_clause)
                                    ).first() is not None

                                if exists and allow_overwrite:
                                    where_clause = None
                                    for c in pk_cols:
                                        cond = getattr(active_final.c, c) == r_d.get(c)
                                        where_clause = cond if where_clause is None else where_clause & cond
                                    if 'company_id' in active_final.columns and r_d.get('company_id') is not None:
                                        where_clause = where_clause & (active_final.c.company_id == r_d.get('company_id'))
                                    final_db.execute(
                                        active_final.update().where(where_clause).values(**insert_item)
                                    )
                                elif not exists:
                                    final_db.execute(active_final.insert(), [insert_item])
                                # Si existe y no hay overwrite: skip insert, igual se marca MIGRADO (idempotente)

                            # Mark as migrated locally
                            db.execute(active_local.update().where(
                                active_local.c.company_id == company_id,
                                active_local.c.subcategoria_id == sub.id,
                                active_local.c.id == r_d.get('id')
                            ).values(estado="MIGRADO"))
                            migrated_lineas += 1

                        except Exception as e:
                            failed_rows_raw.append({"seat": row_label, "error": str(e), "subcategoria_id": sub.id})

                # Update subcategory tracking states
                try:
                    from sqlalchemy import func
                    # Resolve active table for sequence tracking (prefer LocalDetTable as it has subcategoria_id, otherwise HeadTable)
                    active_table = LocalDetTable if LocalDetTable is not None else LocalHeadTable
                    if active_table is not None:
                        if nasiento_col in active_table.c:
                            # Update AsientoCorrelativo for each distinct period and month migrated
                            has_period_mes = "cper" in active_table.c and "cmes" in active_table.c
                            if has_period_mes:
                                stmt_max_group = db.query(
                                    active_table.c.cper,
                                    active_table.c.cmes,
                                    func.max(getattr(active_table.c, nasiento_col))
                                ).filter(
                                    active_table.c.company_id == company_id,
                                    active_table.c.estado == "MIGRADO"
                                )
                                if "subcategoria_id" in active_table.c:
                                    stmt_max_group = stmt_max_group.filter(active_table.c.subcategoria_id == sub.id)
                                stmt_max_group = stmt_max_group.group_by(
                                    active_table.c.cper,
                                    active_table.c.cmes
                                )
                                max_results = db.execute(stmt_max_group).fetchall()
                            else:
                                stmt_max_global = db.query(
                                    func.max(getattr(active_table.c, nasiento_col))
                                ).filter(
                                    active_table.c.company_id == company_id,
                                    active_table.c.estado == "MIGRADO"
                                )
                                if "subcategoria_id" in active_table.c:
                                    stmt_max_global = stmt_max_global.filter(active_table.c.subcategoria_id == sub.id)
                                r_max = db.execute(stmt_max_global).scalar()
                                max_results = [("GLOBAL", "00", r_max)] if r_max is not None else []
                                
                            for r_cper, r_cmes, r_max in max_results:
                                if r_cper and r_cmes and r_max is not None:
                                    corr_rec = db.query(AsientoCorrelativo).filter(
                                        AsientoCorrelativo.company_id == company_id,
                                        AsientoCorrelativo.subcategoria_id == sub.id,
                                        AsientoCorrelativo.periodo == str(r_cper),
                                        AsientoCorrelativo.mes == str(r_cmes)
                                    ).first()
                                    if corr_rec:
                                        corr_rec.asiento_actual = int(r_max)
                                    else:
                                        # Fallback starting value from subcategory config
                                        asiento_ini_val = int(sub.asiento_inicial) if getattr(sub, "asiento_inicial", None) is not None else 1
                                        new_corr = AsientoCorrelativo(
                                            company_id=company_id,
                                            subcategoria_id=sub.id,
                                            periodo=str(r_cper),
                                            mes=str(r_cmes),
                                            asiento_inicial=asiento_ini_val,
                                            asiento_actual=int(r_max)
                                        )
                                        db.add(new_corr)
                        else:
                            # Mode B / No nasiento column: We update the global AsientoCorrelativo
                            # using the count of successfully migrated rows to let the sequence continue
                            corr_rec = db.query(AsientoCorrelativo).filter(
                                db.bind.dialect.name != "sqlite", # just database session query
                                AsientoCorrelativo.company_id == company_id,
                                AsientoCorrelativo.subcategoria_id == sub.id,
                                AsientoCorrelativo.periodo == "GLOBAL",
                                AsientoCorrelativo.mes == "00"
                            ).first()
                            if corr_rec and migrated_lineas > 0:
                                corr_rec.asiento_actual = max(corr_rec.asiento_actual, corr_rec.asiento_inicial - 1) + migrated_lineas
                            elif not corr_rec and migrated_lineas > 0:
                                asiento_ini_val = int(sub.asiento_inicial) if getattr(sub, "asiento_inicial", None) is not None else 1
                                new_corr = AsientoCorrelativo(
                                    company_id=company_id,
                                    subcategoria_id=sub.id,
                                    periodo="GLOBAL",
                                    mes="00",
                                    asiento_inicial=asiento_ini_val,
                                    asiento_actual=asiento_ini_val - 1 + migrated_lineas
                                )
                                db.add(new_corr)
                except Exception as e:
                    print(f"Error updating subcategory control fields for {sub.nombre}: {e}")

        # Commit everything successful (local states)
        db.commit()

        # Sanitize failed rows
        sanitized_rows = []
        if failed_rows_raw:
            import json
            from decimal import Decimal
            from datetime import datetime as _dt, date as _date

            def _sanitize_value(v):
                if v is None: return None
                if isinstance(v, Decimal): return float(v)
                if isinstance(v, (_dt, _date)): return str(v)
                if isinstance(v, bytes): return v.decode("utf-8", errors="replace")
                return v

            for row in failed_rows_raw:
                if isinstance(row, dict):
                    sanitized_rows.append({k: _sanitize_value(v) for k, v in row.items()})
                else:
                    sanitized_rows.append(str(row))

            raise HTTPException(
                status_code=500, 
                detail={
                    "message": f"Migración parcial: {migrated_lineas} líneas migradas y {migrated_cabeceras} cabeceras. Hubo errores en {len(failed_rows_raw)} asientos.",
                    "failed_rows": sanitized_rows
                }
            )

        result = {
            "message": f"Migración exitosa: {migrated_lineas} líneas y {migrated_cabeceras} cabeceras",
            "migrated_lineas": migrated_lineas,
            "migrated_cabeceras": migrated_cabeceras,
            "lote_id": lote_id
        }
        
        # Cerrar sesión si la creamos nosotros
        if should_close_db:
            db.close()
            
        return result

    except HTTPException:
        if should_close_db:
            db.close()
        raise
    except Exception as e:
        db.rollback()
        if should_close_db:
            db.close()
        raise HTTPException(status_code=500, detail={"message": f"Fallo catastrófico en migración: {str(e)}", "failed_rows": []})


@router.post("/migrate-to-final/{company_id}")
def migrate_to_final(
    company_id: int,
    lote_id: Optional[str] = None,
    allow_overwrite: bool = False,
    subcategoria_id: Optional[int] = None,
    db: Session = Depends(get_dest_db)
):
    """Wrapper API para migración a destino final"""
    return _migrate_to_final_internal(company_id, lote_id, allow_overwrite, subcategoria_id, db)


@router.get("/cf-diariol")
def list_cf_diariol(
    company_id: int,
    subcategoria_id: Optional[int] = None,
    lote_id: Optional[str] = None,
    estado: Optional[str] = None,
    periodo: Optional[str] = None,
    mes: Optional[str] = None,
    nasiento: Optional[int] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_dest_db)
):
    """Lista registros de la tabla de staging configurada (por defecto cf_diariol) con filtros potentes"""
    from backend.app.models.models import MapeoSubcategoria, CfDiariol
    from sqlalchemy import Table, MetaData, select, func, or_
    from backend.app.core.database import dest_engine as local_engine
    import decimal
    import datetime as dt_module

    # Si se especifica subcategoría, determinamos de qué tabla leer según su configuración
    sub = None
    table_name = "cf_diariol"
    if subcategoria_id:
        sub = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.id == subcategoria_id).first()
        if sub and sub.tabla_destino_detalle:
            table_name = sub.tabla_destino_detalle

    metadata_local = MetaData()
    try:
        local_table = Table(table_name, metadata_local, autoload_with=local_engine)
    except Exception as e:
        local_table = None

    # Si la tabla no se puede cargar, caemos en CfDiariol (ORM) como fallback seguro
    if local_table is None:
        query = db.query(CfDiariol, MapeoSubcategoria.nombre.label("subcategoria_nombre")).outerjoin(
            MapeoSubcategoria, CfDiariol.subcategoria_id == MapeoSubcategoria.id
        ).filter(CfDiariol.company_id == company_id)
        
        if subcategoria_id:
            query = query.filter(CfDiariol.subcategoria_id == subcategoria_id)
        if lote_id:
            query = query.filter(CfDiariol.lote_id == lote_id)
        if estado:
            query = query.filter(CfDiariol.estado == estado)
        if periodo:
            query = query.filter(CfDiariol.cper == periodo)
        if mes:
            query = query.filter(CfDiariol.cmes == mes)
        if nasiento:
            query = query.filter(CfDiariol.nasiento == nasiento)
        if search:
            search_like = f"%{search}%"
            query = query.filter(
                (CfDiariol.cglosa.ilike(search_like)) |
                (CfDiariol.ccodcue.ilike(search_like)) |
                (CfDiariol.cnumero.ilike(search_like)) |
                (CfDiariol.ccodruc.ilike(search_like))
            )
            
        total = query.count()
        items = query.order_by(CfDiariol.nasiento.desc(), CfDiariol.nidlin.asc()).offset(skip).limit(limit).all()
        
        return {
            "total": total,
            "items": [{
                **{
                    c.name: float(getattr(r[0], c.name)) if type(getattr(r[0], c.name)).__name__ == 'Decimal'
                    else getattr(r[0], c.name)
                    for c in r[0].__table__.columns if c.name != "extra_data"
                },
                "subcategoria_nombre": r[1] or f"Subcat {r[0].subcategoria_id}"
            } for r in items]
        }

    # Si la tabla se cargó con éxito, hacemos la consulta dinámica sobre el esquema de esa tabla
    clauses = []
    if "company_id" in local_table.c:
        clauses.append(local_table.c.company_id == company_id)
    if "subcategoria_id" in local_table.c:
        if subcategoria_id:
            clauses.append(local_table.c.subcategoria_id == subcategoria_id)
    if lote_id and "lote_id" in local_table.c:
        clauses.append(local_table.c.lote_id == lote_id)
    if estado and "estado" in local_table.c:
        clauses.append(local_table.c.estado == estado)
    if periodo and "cper" in local_table.c:
        clauses.append(local_table.c.cper == periodo)
    if mes and "cmes" in local_table.c:
        clauses.append(local_table.c.cmes == mes)
    if nasiento and "nasiento" in local_table.c:
        clauses.append(local_table.c.nasiento == nasiento)

    if search:
        search_like = f"%{search}%"
        search_clauses = []
        for col in local_table.columns:
            if str(col.type).upper().startswith(("VARCHAR", "TEXT", "CHAR", "STRING")):
                search_clauses.append(col.ilike(search_like))
        if search_clauses:
            clauses.append(or_(*search_clauses))

    # Obtener el total
    count_stmt = select(func.count()).select_from(local_table)
    if clauses:
        count_stmt = count_stmt.where(*clauses)
    total = db.execute(count_stmt).scalar()

    # Obtener registros paginados
    select_stmt = select(local_table)
    if clauses:
        select_stmt = select_stmt.where(*clauses)

    # Ordenar registros
    if "nasiento" in local_table.c and "nidlin" in local_table.c:
        select_stmt = select_stmt.order_by(local_table.c.nasiento.desc(), local_table.c.nidlin.asc())
    elif "id" in local_table.c:
        select_stmt = select_stmt.order_by(local_table.c.id.desc())
    elif "created_at" in local_table.c:
        select_stmt = select_stmt.order_by(local_table.c.created_at.desc())

    select_stmt = select_stmt.offset(skip).limit(limit)
    result_proxy = db.execute(select_stmt)
    keys = result_proxy.keys()

    items = []
    for row in result_proxy:
        row_dict = {}
        for k in keys:
            val = getattr(row, k)
            if isinstance(val, decimal.Decimal):
                val = float(val)
            elif isinstance(val, (dt_module.date, dt_module.datetime)):
                val = val.isoformat()
            row_dict[k] = val

        # Mapear campos estándar esperados por el frontend
        mapped = {}
        mapped["id"] = row_dict.get("id")
        mapped["company_id"] = row_dict.get("company_id")
        mapped["subcategoria_id"] = row_dict.get("subcategoria_id")
        mapped["lote_id"] = row_dict.get("lote_id")
        mapped["estado"] = row_dict.get("estado") or "PENDIENTE"

        mapped["cper"] = row_dict.get("cper") or "GLOBAL"
        mapped["cmes"] = row_dict.get("cmes") or "00"
        mapped["nasiento"] = str(row_dict.get("nasiento")) if row_dict.get("nasiento") is not None else "-"
        mapped["nidlin"] = str(row_dict.get("nidlin") or row_dict.get("id") or "-")

        # Buscar el ID Control más idóneo según las columnas disponibles
        idcontrol_val = "-"
        for candidate in ["idcontrol", "ccodruc", "codaux", "rucaux", "id"]:
            if row_dict.get(candidate) is not None:
                idcontrol_val = str(row_dict.get(candidate)).strip()
                break
        mapped["idcontrol"] = idcontrol_val

        # Cuenta
        mapped["ccodcue"] = str(row_dict.get("ccodcue")).strip() if row_dict.get("ccodcue") is not None else "-"

        # Debe y Haber
        mapped["ndebe"] = float(row_dict.get("ndebe")) if row_dict.get("ndebe") is not None else 0.0
        mapped["nhaber"] = float(row_dict.get("nhaber")) if row_dict.get("nhaber") is not None else 0.0

        # Glosa descriptiva: si la tabla tiene cglosa la usamos, sino usamos crazsoc, cdirec, etc.
        glosa_val = ""
        for candidate in ["cglosa", "crazsoc", "cdirec", "cemail"]:
            if row_dict.get(candidate) is not None:
                glosa_val = str(row_dict.get(candidate)).strip()
                break
        if not glosa_val:
            ruc = row_dict.get("ccodruc")
            raz = row_dict.get("crazsoc")
            if ruc and raz:
                glosa_val = f"RUC: {str(ruc).strip()} | {str(raz).strip()}"
            elif ruc:
                glosa_val = f"RUC: {str(ruc).strip()}"
            elif raz:
                glosa_val = str(raz).strip()
            else:
                glosa_val = f"Fila #{row_dict.get('id')}"
        mapped["cglosa"] = glosa_val

        # Copiar todas las propiedades originales para el visor de detalles (modal "Ver Fila")
        for k, v in row_dict.items():
            if k not in mapped:
                mapped[k] = v

        # Resolver nombre de subcategoría
        sub_nombre = "Subcategoría"
        if sub:
            sub_nombre = sub.nombre
        else:
            # Si se leyó de forma genérica pero no teníamos sub, lo resolvemos
            try:
                sub_res = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.id == row_dict.get("subcategoria_id")).first()
                if sub_res:
                    sub_nombre = sub_res.nombre
            except:
                pass
        mapped["subcategoria_nombre"] = sub_nombre

        items.append(mapped)

    return {
        "total": total,
        "items": items
    }


@router.get("/staging-preview")
def list_staging_preview(
    company_id: int,
    subcategoria_id: Optional[int] = None,
    lote_id: Optional[str] = None,
    estado: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_dest_db)
):
    """
    Lista registros de las tablas DESTINO (cabecera y detalle) por subcategoría.
    Muestra tanto cf_diario (cabeceras) como cf_diariol (detalles) para cada subcategoría.
    """
    import decimal
    import datetime as dt_module

    # Helper para serializar filas
    def _serialize_rows(result_proxy):
        keys = result_proxy.keys()
        items = []
        for row in result_proxy:
            row_dict = {}
            for k in keys:
                val = getattr(row, k)
                if isinstance(val, decimal.Decimal):
                    val = float(val)
                if isinstance(val, (dt_module.date, dt_module.datetime)):
                    val = val.isoformat()
                row_dict[k] = val
            items.append(row_dict)
        return items

    def _query_table(schema, table, sub_id, extra_where, extra_params):
        """Ejecuta count + select sobre una tabla destino."""
        if not re.match(r'^[a-zA-Z0-9_]+$', schema) or not re.match(r'^[a-zA-Z0-9_]+$', table):
            raise ValueError("Nombre de esquema o tabla inválido")

        where_clauses = ["company_id = :company_id"]
        params = {"company_id": company_id, "limit": limit, "skip": skip}

        if sub_id:
            where_clauses.append("subcategoria_id = :sub_id")
            params["sub_id"] = sub_id
        if lote_id:
            where_clauses.append("lote_id = :lote_id")
            params["lote_id"] = lote_id
        if estado:
            where_clauses.append("estado = :estado")
            params["estado"] = estado

        where_sql = " AND ".join(where_clauses)
        total = db.execute(text(f"SELECT count(*) FROM {schema}.{table} WHERE {where_sql}"), params).scalar()
        result = db.execute(text(f"SELECT * FROM {schema}.{table} WHERE {where_sql} LIMIT :limit OFFSET :skip"), params)
        items = _serialize_rows(result)
        return total, items

    # 1. Resolver subcategorías
    subcats = []
    if subcategoria_id:
        sub = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.id == subcategoria_id).first()
        if sub:
            subcats.append(sub)
    else:
        result = db.execute(text("""
            SELECT s.id
            FROM mapeo_subcategorias s
            JOIN mapeo_categorias c ON s.categoria_id = c.id
            WHERE c.company_id = :company_id
              AND s.is_active = true
        """), {"company_id": company_id})
        sub_ids = [row[0] for row in result.fetchall()]
        if sub_ids:
            subcats = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.id.in_(sub_ids)).all()

    # 2. Para cada subcategoría, mostrar cabecera y detalle
    results = []
    for sub in subcats:
        s = sub.schema_destino or "public"
        sub_label = sub.nombre or f"Subcat {sub.id}"

        # --- Tabla Cabecera ---
        if sub.generate_headers is not False:
            tabla_cab = sub.tabla_destino_cabecera or "cf_diario"
            display_cab = f"{s}.{tabla_cab} — Cabecera ({sub_label})"
            try:
                total, items = _query_table(s, tabla_cab, sub.id, None, None)
                if total > 0 or subcategoria_id:
                    results.append({"table_name": display_cab, "total": total, "items": items})
            except Exception as e:
                print(f"Error querying cabecera {tabla_cab}: {e}")
                results.append({"table_name": display_cab, "total": 0, "items": [], "error": str(e)})

        # --- Tabla Detalle ---
        if sub.generate_details is not False:
            tabla_det = sub.tabla_destino_detalle or "cf_diariol"
            display_det = f"{s}.{tabla_det} — Detalle ({sub_label})"
            try:
                total, items = _query_table(s, tabla_det, sub.id, None, None)
                if total > 0 or subcategoria_id:
                    results.append({"table_name": display_det, "total": total, "items": items})
            except Exception as e:
                print(f"Error querying detalle {tabla_det}: {e}")
                results.append({"table_name": display_det, "total": 0, "items": [], "error": str(e)})

    if not results:
        results.append({"table_name": "Staging (Vacío)", "total": 0, "items": []})

    return results


@router.get("/origen-preview")
def list_origen_preview(
    company_id: int,
    subcategoria_id: Optional[int] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_dest_db)
):
    """
    Lista registros de las tablas ORIGEN extraídas en el Paso 1 (migconta_db).
    Soporta búsqueda global en todas las columnas mediante el parámetro `search`.
    """
    import decimal
    import datetime as dt_module
    from sqlalchemy import inspect, text
    from backend.app.core.database import dest_engine

    def _serialize_rows(result_proxy):
        keys = result_proxy.keys()
        items = []
        for row in result_proxy:
            row_dict = {}
            for k in keys:
                val = getattr(row, k)
                if isinstance(val, decimal.Decimal):
                    val = float(val)
                if isinstance(val, (dt_module.date, dt_module.datetime)):
                    val = val.isoformat()
                row_dict[k] = val
            items.append(row_dict)
        return items

    tables_to_preview = set()
    
    if subcategoria_id:
        sub = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.id == subcategoria_id).first()
        if sub and sub.tabla_origen:
            tables_to_preview.add(sub.tabla_origen.lower().replace(" ", "_"))
    else:
        # Obtener todas las tablas seleccionadas en el Paso 1 para esta empresa
        selections = db.query(TableSelection).join(SourceConnection).filter(
            SourceConnection.company_id == company_id,
            TableSelection.is_selected == True
        ).all()
        for sel in selections:
            if sel.table_name:
                tables_to_preview.add(sel.table_name.lower().replace(" ", "_"))
        
        # También incluir las de mapeo_subcategorias por retrocompatibilidad/mapeos extra
        subcats_raw = db.execute(text("""
            SELECT s.tabla_origen
            FROM mapeo_subcategorias s
            JOIN mapeo_categorias c ON s.categoria_id = c.id
            WHERE c.company_id = :company_id AND s.is_active = true AND s.tabla_origen IS NOT NULL
        """), {"company_id": company_id}).fetchall()
        for row in subcats_raw:
            tables_to_preview.add(row[0].lower().replace(" ", "_"))

    results = []
    inspector = inspect(dest_engine)

    # Solo queremos una vista por tabla origen única para no duplicar si varias subcats usan la misma
    vistas = {}

    for raw_table in tables_to_preview:
        if not raw_table:
            continue
        
        # El ETL formatra el nombre así: "mitabla origen" -> "mitabla_origen"
        table_name = raw_table
        
        if table_name in vistas:
            continue
            
        try:
            if not inspector.has_table(table_name):
                vistas[table_name] = {"table_name": table_name, "total": 0, "items": [], "error": f"La tabla '{table_name}' aún no ha sido extraída a la base intermedia. Haga clic en 'Paso 1: Extraer Datos' para importarla desde el origen."}
                continue

            # Obtener todas las columnas
            cols = [c['name'] for c in inspector.get_columns(table_name)]
            has_company = 'company_id' in cols
            
            # Obtener orden de columnas calculadas por prioridad
            sel_db = db.query(TableSelection).filter(
                TableSelection.company_id == company_id,
                TableSelection.table_name.ilike(table_name)
            ).first()
            
            ordered_cols = []
            if sel_db:
                rules = db.query(ComputedColumnRule).filter(
                    ComputedColumnRule.table_selection_id == sel_db.id,
                    ComputedColumnRule.is_active == True
                ).order_by(ComputedColumnRule.priority).all()
                computed_names = [r.new_column_name for r in rules]
                computed_names_lower = [n.lower() for n in computed_names]
                
                # Base cols: columns in database that are NOT calculated columns
                base_cols = [col for col in cols if col.lower() not in computed_names_lower]
                
                # Computed cols in their sorted/priority order (only if they exist in the DB columns list)
                cols_map = {col.lower(): col for col in cols}
                sorted_computed_cols = []
                for comp_col in computed_names:
                    comp_col_lower = comp_col.lower()
                    if comp_col_lower in cols_map:
                        sorted_computed_cols.append(cols_map[comp_col_lower])
                
                ordered_cols = base_cols + sorted_computed_cols
            else:
                ordered_cols = cols

            if not ordered_cols:
                ordered_cols = cols

            where_clauses = []
            params = {"limit": limit, "skip": skip}
            
            if has_company:
                where_clauses.append("company_id = :company_id")
                params["company_id"] = company_id
                
            if search:
                search_terms = []
                for col in cols:
                    # Castear todo a TEXTO y usar ILIKE para Postgres (mayús/minús)
                    search_terms.append(f'CAST("{col}" AS TEXT) ILIKE :search')
                
                if search_terms:
                    where_clauses.append("(" + " OR ".join(search_terms) + ")")
                    # Postgres ILIKE es case-insensitive
                    params["search"] = f"%{search}%"
            
            where_sql = ""
            if where_clauses:
                where_sql = "WHERE " + " AND ".join(where_clauses)
                
            select_cols_str = ", ".join([f'"{col}"' for col in ordered_cols])
            total_sql = text(f'SELECT count(*) FROM "{table_name}" {where_sql}')
            data_sql = text(f'SELECT {select_cols_str} FROM "{table_name}" {where_sql} LIMIT :limit OFFSET :skip')
            
            total = db.execute(total_sql, params).scalar()
            result = db.execute(data_sql, params)
            items = _serialize_rows(result)
            
            vistas[table_name] = {"table_name": table_name, "total": total, "items": items}
            
        except Exception as e:
            print(f"Error querying origen {table_name}: {e}")
            vistas[table_name] = {"table_name": table_name, "total": 0, "items": [], "error": str(e)}

    results = list(vistas.values())
    
    if not results:
        results.append({"table_name": "Origen (Vacío)", "total": 0, "items": []})

    return results


def _validate_staging_data_internal(
    company_id: int,
    subcategoria_id: Optional[int] = None,
    db: Optional[Session] = None
):
    """
    Valida los datos ya generados en staging (cf_diario, cf_diariol) contra las restricciones
    de la tabla destino: NOT NULL y Longitud Máxima.
    Retorna un reporte detallado de violaciones para corregir antes de migrar.
    """
    from sqlalchemy import Table, MetaData
    from backend.app.core.database import dest_engine as engine, get_dest_db
    import decimal
    import datetime as dt_module

    # Obtener sesión de base de datos si no se proporcionó
    if db is None:
        db = next(get_dest_db())
        should_close_db = True
    else:
        should_close_db = False

    metadata = MetaData()

    # Resolver subcategorías
    subcats = []
    if subcategoria_id:
        sub = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.id == subcategoria_id).first()
        if sub:
            subcats.append(sub)
    else:
        result = db.execute(text("""
            SELECT s.id
            FROM mapeo_subcategorias s
            JOIN mapeo_categorias c ON s.categoria_id = c.id
            WHERE c.company_id = :company_id
              AND s.is_active = true
        """), {"company_id": company_id})
        sub_ids = [row[0] for row in result.fetchall()]
        if sub_ids:
            subcats = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.id.in_(sub_ids)).all()

    all_violations = []
    tables_checked = []

    for sub in subcats:
        schema = sub.schema_destino or "public"
        sub_label = sub.nombre or f"Subcat {sub.id}"

        tables_to_check = []
        if sub.generate_headers is not False:
            tables_to_check.append((sub.tabla_destino_cabecera or "cf_diario", "Cabecera"))
        if sub.generate_details is not False:
            tables_to_check.append((sub.tabla_destino_detalle or "cf_diariol", "Detalle"))

        for table_name, table_type in tables_to_check:
            try:
                tbl = Table(table_name, metadata, schema=schema, autoload_with=engine, extend_existing=True)
            except Exception as e:
                all_violations.append({
                    "table": f"{schema}.{table_name}",
                    "type": table_type,
                    "subcategoria": sub_label,
                    "error": f"No se pudo cargar la tabla: {e}",
                    "violations": []
                })
                continue

            # Obtener restricciones de columnas desde el DESTINO FINAL (Contasis)
            # para detectar violaciones NOT NULL reales (staging tiene todo nullable)
            dest_constraints = _get_dest_constraints_from_final(
                company_id, table_name, schema, db
            )
            if dest_constraints is None:
                raise HTTPException(status_code=500, detail=f"No se pudieron cargar las restricciones de {schema}.{table_name} desde el destino final")


            col_constraints = {}
            for col in tbl.columns:
                max_len = None
                if hasattr(col.type, 'length') and col.type.length:
                    max_len = col.type.length
                # Usar restricciones del destino final si están disponibles
                if dest_constraints and col.name in dest_constraints:
                    dc = dest_constraints[col.name]
                    is_required = dc.get("required", False)
                    if dc.get("max_length"):
                        max_len = dc["max_length"]
                    col_nullable = dc.get("nullable", True)
                    col_type = dc.get("type", str(col.type))
                else:
                    is_required = (not col.nullable) and col.default is None and col.server_default is None and not col.primary_key
                    col_nullable = col.nullable
                    col_type = str(col.type)
                col_constraints[col.name] = {
                    "max_length": max_len,
                    "nullable": col_nullable,
                    "required": is_required,
                    "type": col_type
                }

            # Leer datos de staging para esta subcategoría (0=Error, 1=Pendiente)
            where_sql = "company_id = :company_id AND subcategoria_id = :sub_id AND estado = '1'"
            params = {"company_id": company_id, "sub_id": sub.id}



            try:
                count_query = f"SELECT count(*) FROM {schema}.{table_name} WHERE {where_sql}"
                count = db.execute(text(count_query), params).scalar()
            except Exception as e:
                import traceback
                print(f"COUNT ERROR for {schema}.{table_name}:", e)
                print(traceback.format_exc())
                count = 0


            if count == 0:
                continue

            # Leer todos los registros (para validar completamente)
            try:
                result = db.execute(
                    text(f"SELECT * FROM {schema}.{table_name} WHERE {where_sql} LIMIT 5000"),
                    params
                )
                keys = list(result.keys())
                rows = result.fetchall()
            except Exception as e:
                all_violations.append({
                    "table": f"{schema}.{table_name}",
                    "type": table_type,
                    "subcategoria": sub_label,
                    "error": str(e),
                    "violations": []
                })
                continue

            records = [dict(zip(keys, r)) for r in rows]
            
            table_label_str = f"{schema}.{table_name} — {table_type} ({sub_label})"
            # Usa la validación centralizada (la misma del Paso 2)
            violations = _validate_records_against_schema(
                records=records,
                table_obj=tbl,
                table_label=table_label_str,
                sub_id=sub.id,
                dest_constraints=dest_constraints
            )

            print(f"[{schema}.{table_name}] RECORDS LOADED: {len(records)}, VIOLATIONS FOUND: {len(violations)}")
            
            # AUTO-CORRECTION: Si no hay violaciones, actualizar filas con estado='0' (Error) a estado='1' (Pendiente/Conforme)
            if len(violations) == 0 and len(records) > 0:
                print(f"[{schema}.{table_name}] Validado con éxito. Actualizando registros con estado '0' a '1'")
                update_sql = f"UPDATE {schema}.{table_name} SET estado = '1' WHERE company_id = :company_id AND subcategoria_id = :sub_id AND estado = '0'"
                db.execute(text(update_sql), {"company_id": company_id, "sub_id": sub.id})
                db.commit()
                
            if violations:
                table_info = {

                    "table": table_label_str,




                    "table": table_label_str,
                    "type": table_type,
                    "subcategoria": sub_label,
                    "total_records": count,
                    "violations": violations
                }
                tables_checked.append(table_info)

    total_violations = sum(len(t["violations"]) for t in tables_checked)

    result = {
        "company_id": company_id,
        "total_violations": total_violations,
        "tables": tables_checked,
        "status": "OK" if total_violations == 0 else "TIENE_ERRORES"
    }
    
    # Cerrar sesión si la creamos nosotros
    if should_close_db:
        db.close()
        
    return result


@router.get("/validate-staging")
def validate_staging_data(
    company_id: int,
    subcategoria_id: Optional[int] = None,
    db: Session = Depends(get_dest_db)
):
    """Wrapper API para validación de staging"""
    return _validate_staging_data_internal(company_id, subcategoria_id, db)

@router.get("/asientos-generados/export-csv")
def export_asientos_csv(company_id: int, lote_id: Optional[str] = None,
                        subcategoria_id: Optional[int] = None,
                        db: Session = Depends(get_dest_db)):
    """Exporta los asientos generados en formato CSV de Contasis"""
    from fastapi.responses import StreamingResponse
    import csv, io
    from datetime import datetime as dt

    query = db.query(AsientoContableGenerado).filter(
        AsientoContableGenerado.company_id == company_id,
        AsientoContableGenerado.estado == "PENDIENTE"
    )
    if lote_id:
        query = query.filter(AsientoContableGenerado.lote_id == lote_id)
    if subcategoria_id:
        query = query.filter(AsientoContableGenerado.subcategoria_id == subcategoria_id)

    asientos = query.order_by(AsientoContableGenerado.nasiento, AsientoContableGenerado.nidlin).all()

    # Campos del CSV de Contasis (en orden)
    CAMPOS = [
        "cper","cmes","ccodori","nasiento","nidlin","ntc","ccodcue","ndebe","nhaber","cglosa",
        "ndebes","nhabers","ndebed","nhaberd","cdes","cdestino","ndifauto","najusauto","cregis",
        "ncomp","ccoddoc","cserie","cnumero","cnumfin","ffechadoc","ccodruc","ccodenti","ffechaven",
        "nbase1","nigv1","nbase2","nigv2","nbase3","nigv3","nina","nexo","nisc","nivabase","nivaimp",
        "ntot","nbase1s","nigv1s","nbase2s","nigv2s","nbase3s","nigv3s","ninas","nexos","niscs",
        "nivabases","nivaimps","ntots","nbase1d","nigv1d","nbase2d","nigv2d","nbase3d","nigv3d",
        "ninad","nexod","niscd","nivabased","nivaimpd","ntotd","ccodclas","ccodflu","ccodpago",
        "ccodcos","ccodcos2","ccodpresu","ccodcam","ccodcam2"
    ]

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(CAMPOS)

    for a in asientos:
        row = []
        for campo in CAMPOS:
            val = getattr(a, campo, None)
            if val is None:
                row.append("")
            elif isinstance(val, float) or hasattr(val, '__float__'):
                try:
                    row.append(float(val))
                except:
                    row.append(val)
            else:
                row.append(val)
        writer.writerow(row)

    # Marcar como exportados
    for a in asientos:
        a.estado = "EXPORTADO"
    db.commit()

    output.seek(0)
    filename = f"asientos_{company_id}_{dt.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
