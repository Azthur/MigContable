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
    ColumnFilter, TableSelection, MigrationControl,
    AsientoContableGenerado, ComputedColumnRule
)
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
    query = db.query(MapeoCategoria).filter(MapeoCategoria.is_active == True)
    if company_id:
        query = query.filter(MapeoCategoria.company_id == company_id)
    return query.order_by(MapeoCategoria.nombre).all()

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

    return {
        "company_id": company_id,
        "columns": columns
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
            formula_ast_str = re.sub(r'(?<![=<>!])=(?![=])', '==', formula_str)
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

            # Check NOT NULL (solo None es realmente NULL, strings con espacios son válidos)
            if constraints["required"] and value is None:
                err_dict = {
                    "field": field,
                    "row_index": idx,
                    "value": "NULL",
                    "error": f"Campo '{field}' es obligatorio (NOT NULL) pero tiene valor vacío/nulo",
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


def _generate_subcategoria_cf_diariol(
    sub: MapeoSubcategoria,
    db: Session,
    company_id: int,
    filters: list = [],
    global_lote_id: Optional[str] = None,
    counters_por_asiento: dict = None,
    generate_headers: bool = True,
    generate_details: bool = True
):
    from backend.app.models.models import CfDiariol, CfDiario, MapeoLineaAsiento, MapeoSubcategoria
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
        return 0, 0 # No configurado
    if not sub.tabla_origen:
        return 0, 0

    query_str = f'SELECT * FROM "{sub.tabla_origen.lower()}"'
    where_parts = []
    query_params = {}
    
    # 1. Apply subcategory-level filter_rules (configured in mapping editor)
    sub_filter_rules = sub.filter_rules or []
    for idx, rule in enumerate(sub_filter_rules):
        col = rule.get("column", "")
        op = rule.get("operator", "=").upper()
        val = rule.get("value", "")
        val2 = rule.get("value2", "")
        if not col:
            continue
        col_quoted = f'"{col}"'
        pkey = f"fr{idx}"

        if op == "IS NULL":
            where_parts.append(f"{col_quoted} IS NULL")
        elif op == "IS NOT NULL":
            where_parts.append(f"{col_quoted} IS NOT NULL")
        elif op == "BETWEEN" and val and val2:
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
            col_quoted = f'"{col}"'
            
            if op == "IS NULL": where_parts.append(f"{col_quoted} IS NULL")
            elif op == "IS NOT NULL": where_parts.append(f"{col_quoted} IS NOT NULL")
            elif op == "BETWEEN" and val and val2:
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
        return 0, 0

    if not rows:
        return 0, 0

    df = pd.DataFrame(rows, columns=columns)

    clave_str = sub.clave_asiento
    if not clave_str:
        clave_columns = [columns[0]] if columns else []
    else:
        cols_lower_map = {col.lower(): col for col in columns}
        clave_columns = [cols_lower_map[c.strip().lower()] for c in clave_str.split(",") if c.strip().lower() in cols_lower_map]
        if not clave_columns:
            clave_columns = [columns[0]] if columns else []

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

    # Asignar número de asiento
    # Use a unique key for the current company to track nasiento across subcategories
    nasiento_key = f"{company_id}-global"
    if nasiento_key not in counters_por_asiento:
        last_nasiento_in_db = 0
        if DetTable is not None:
            check_col_nasiento = sub.col_destino_nasiento or "nasiento"
            if check_col_nasiento in det_cols:
                stmt_nas = db.query(func.max(getattr(DetTable.c, check_col_nasiento))).filter(
                    DetTable.c.company_id == company_id,
                    DetTable.c.estado == "PENDIENTE"
                )
                last_nasiento_in_db = db.execute(stmt_nas).scalar() or 0
        
        counters_por_asiento[nasiento_key] = last_nasiento_in_db

    # Verificar si el usuario ha seteado un asiento inicial forzado en la subcategoría
    if getattr(sub, "asiento_inicial", None) is not None:
        # Se prioriza el asiento inicial si es mayor al de la DB para no sobreescribir. 
        # Restamos 1 porque la base le suma 1 después.
        counters_por_asiento[nasiento_key] = max(counters_por_asiento[nasiento_key], sub.asiento_inicial - 1)

    nasiento_base = counters_por_asiento[nasiento_key] + 1
    df['nasiento'] = df.groupby(clave_columns, dropna=False).ngroup() + nasiento_base
    
    # Update the global counter with the max nasiento generated in this subcategory
    counters_por_asiento[nasiento_key] = df['nasiento'].max() if not df.empty else counters_por_asiento[nasiento_key]


    # ─── OPTIMIZACIÓN: Evaluar Fórmulas Vectorizadas en todo el DF de una vez ───

    # 1. Cabeceras (CfDiario) - Solo necesitamos 1 por 'nasiento'
    header_df = df.drop_duplicates(subset=['nasiento']).copy()
    
    if sub.mapeo_cabecera:
        for field, formula in sub.mapeo_cabecera.items():
            header_df[f"_head_{field}"] = evaluate_formula_on_df(header_df, formula, db, company_id, default="")

    diario_entries = []
    
    def get_head_val(row, field: str, default: Any):
        if not sub.mapeo_cabecera or field not in sub.mapeo_cabecera: 
            return default
        val = row.get(f"_head_{field}")
        if pd.isna(val):
            return default
        if isinstance(val, str) and val.strip() == "" and val != " " and val != "":
            return default 
        return val

    if generate_headers and HeadTable is not None:
        for _, h_row in header_df.iterrows():
            row_dict = {
                "company_id": company_id,
                "subcategoria_id": sub.id,
                "lote_id": global_lote_id,
                "estado": "1",
                "nasiento": h_row["nasiento"]
            }
            
            if sub.col_destino_nasiento and sub.col_destino_nasiento in head_cols:
                row_dict[sub.col_destino_nasiento] = h_row["nasiento"]
                
            if sub.mapeo_cabecera:
                for field in sub.mapeo_cabecera.keys():
                    val = get_head_val(h_row, field, None)
                    if val is not None and field in head_cols:
                        row_dict[field] = str(val)[:500] if field == "cglosa" else val
                        
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
        "ndebes", "nhabers", "ndebed", "nhaberd", "ntot", "ntots", "ntotd"
    }
    for linea in sub.lineas_asiento:
        if linea.mapeo_detalle:
            for f in linea.mapeo_detalle.keys():
                if f in det_cols: all_possible_keys.add(f)
    if sub.col_destino_nasiento: all_possible_keys.add(sub.col_destino_nasiento)
    if sub.col_destino_nidlin: all_possible_keys.add(sub.col_destino_nidlin)

    counters_por_asiento = {}

    for linea in lineas:
        if not linea.mapeo_detalle: continue
        
        # Extraer data de tabla origen para esta línea (aplicando filtros y condiciones)
        temp_df = df.copy()

        # Condición de aplicación
        if getattr(linea, "condicion_aplicacion", None):
            try:
                mask = evaluate_formula_on_df(temp_df, linea.condicion_aplicacion, db, company_id, default=False)
                mask = pd.to_numeric(mask, errors='coerce').fillna(0).astype(bool) | (mask.astype(str).str.strip().str.upper() == 'TRUE')
                temp_df = temp_df[mask]
            except Exception as e:
                print(f"Error eval cond: {e}")
                continue
        
        if temp_df.empty:
            continue

        # Evaluar todas las fórmulas de detalle sobre el df de la línea
        for db_field, formula in linea.mapeo_detalle.items():
            temp_df[f"_calc_{db_field}"] = evaluate_formula_on_df(temp_df, formula, db, company_id, default="")

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
                
                # If truly empty string (length 0 or stripped is empty), handle accordingly
                val_str = str(val).strip()
                if val_str == "":
                    # Special handling for user's request: allow " " for strings only.
                    if type_cast is str and isinstance(val, str) and len(val) > 0:
                        return str(val)
                    
                    if type_cast in [float, int]:
                        return type_cast(0)
                    return default
                
                if type_cast is str:
                    # Clean account codes or codes that might come as floats (e.g. "701101.0")
                    s_val = str(val)
                    if s_val.endswith(".0"):
                        s_val = s_val[:-2]
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
                "nidlin": curr_nidlin
            })

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

    rows_inserted = 0
    if generate_details and diariol_entries and DetTable is not None:
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
    if generate_headers and diario_entries and HeadTable is not None:
        for entry in diario_entries:
            if entry.get("nasiento") in error_nasientos:
                entry["estado"] = "0"
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

    return rows_inserted, len(header_df) if generate_headers else 0, all_validation_errors


@router.post("/generate-to-cf-diariol")
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
                            DetTable.c.estado.in_(["0", "1", "PENDIENTE"]),
                            DetTable.c.subcategoria_id == sub.id
                        )
                        db.execute(stmt_del_l)
    
                    if sub.generate_headers is not False:
                        try: HeadTable = Table(tabla_head_name, metadata, autoload_with=engine)
                        except: HeadTable = None
                        
                        if HeadTable is not None and asientos_to_delete:
                            check_col_head = sub.col_destino_nasiento or "nasiento"
                            if check_col_head in [c.name for c in HeadTable.columns]:
                                stmt_del_c = HeadTable.delete().where(
                                    HeadTable.c.company_id == company_id,
                                    HeadTable.c.estado.in_(["0", "1", "PENDIENTE"]),
                                    getattr(HeadTable.c, check_col_head).in_(asientos_to_delete)
                                )
                                db.execute(stmt_del_c)
    
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
                    generate_details=(sub.generate_details is not False)
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



@router.post("/migrate-to-final/{company_id}")
def migrate_to_final(
    company_id: int,
    lote_id: Optional[str] = None,
    db: Session = Depends(get_dest_db)
):
    """
    Migra registros PENDIENTE de cf_diariol (staging en migconta_db) al destino final de Contasis.
    Conecta a la BD de Contasis usando FinalDestConnection y hace INSERT bulk en cf_diariol.
    """
    from backend.app.models.models import FinalDestConnection, MapeoCategoria, MapeoSubcategoria
    from backend.app.services.connection_manager import ConnectionManager
    from sqlalchemy import Table, MetaData, text
    from backend.app.core.database import dest_engine as local_engine

    # Obtener conexión destino final
    final_conn = db.query(FinalDestConnection).filter(
        FinalDestConnection.company_id == company_id,
        FinalDestConnection.is_active == True
    ).first()
    if not final_conn:
        raise HTTPException(status_code=404, detail="No hay conexión destino final configurada para esta empresa")

    subcategorias = db.query(MapeoSubcategoria).join(MapeoCategoria).filter(
        MapeoCategoria.company_id == company_id,
        MapeoSubcategoria.is_active == True
    ).all()
    
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

                # Fetch Headers
                if LocalHeadTable is not None and FinalHeadTable is not None:
                    stmt_c = LocalHeadTable.select().where(
                        LocalHeadTable.c.company_id == company_id,
                        LocalHeadTable.c.estado == "1",
                        LocalHeadTable.c.subcategoria_id == sub.id
                    )
                    if lote_id: stmt_c = stmt_c.where(LocalHeadTable.c.lote_id == lote_id)
                    cabeceras_rows = db.execute(stmt_c).fetchall()
                    
                    if cabeceras_rows:
                        # Find primary matching columns
                        delete_keys = set()
                        nasiento_col = sub.col_destino_nasiento or "nasiento"
                        
                        has_cper = "cper" in FinalHeadTable.columns
                        has_cmes = "cmes" in FinalHeadTable.columns
                        has_ccodori = "ccodori" in FinalHeadTable.columns
                        has_nasiento = nasiento_col in FinalHeadTable.columns

                        for row in cabeceras_rows:
                            r_d = row._mapping
                            cper = r_d.get('cper') if has_cper else None
                            cmes = r_d.get('cmes') if has_cmes else None
                            ccodori = r_d.get('ccodori') if has_ccodori else None
                            nasiento = r_d.get(nasiento_col) if has_nasiento else None 
                            
                            # Only delete combinations if all 4 core keys are present locally and remotely
                            if has_cper and has_cmes and has_ccodori and has_nasiento and cper and cmes and ccodori and nasiento is not None:
                                delete_keys.add((cper, cmes, ccodori, nasiento))
                                
                        for (p, m, o, n) in delete_keys:
                            final_db.execute(FinalHeadTable.delete().where(
                                FinalHeadTable.c.cper == p,
                                FinalHeadTable.c.cmes == m,
                                FinalHeadTable.c.ccodori == o,
                                getattr(FinalHeadTable.c, nasiento_col) == n
                            ))
                            if FinalDetTable is not None:
                                final_db.execute(FinalDetTable.delete().where(
                                    FinalDetTable.c.cper == p,
                                    FinalDetTable.c.cmes == m,
                                    FinalDetTable.c.ccodori == o,
                                    getattr(FinalDetTable.c, nasiento_col) == n
                                ))

                        # Build insertion mapping matching final remote table definition
                        remote_head_cols = [c.name for c in FinalHeadTable.columns]
                        insert_list = []
                        for row in cabeceras_rows:
                            r_d = row._mapping
                            insert_item = {k: v for k, v in r_d.items() if k in remote_head_cols}
                            insert_list.append(insert_item)
                            
                        if insert_list:
                            try:
                                final_db.execute(FinalHeadTable.insert(), insert_list)
                                migrated_cabeceras += len(insert_list)
                                db.execute(LocalHeadTable.update().where(
                                    LocalHeadTable.c.company_id == company_id,
                                    LocalHeadTable.c.estado == "1",
                                    LocalHeadTable.c.subcategoria_id == sub.id
                                ).values(estado="MIGRADO"))
                            except Exception as e:
                                print(f"Error bulk inserting headers: {e}")

                # Fetch details
                if LocalDetTable is not None and FinalDetTable is not None:
                    stmt_l = LocalDetTable.select().where(
                        LocalDetTable.c.company_id == company_id,
                        LocalDetTable.c.estado == "1",
                        LocalDetTable.c.subcategoria_id == sub.id
                    )
                    if lote_id: stmt_l = stmt_l.where(LocalDetTable.c.lote_id == lote_id)
                    detalle_rows = db.execute(stmt_l).fetchall()
                    
                    if detalle_rows:
                        remote_det_cols = [c.name for c in FinalDetTable.columns]
                        insert_list = []
                        for row in detalle_rows:
                            r_d = row._mapping
                            insert_item = {}
                            for k, v in r_d.items():
                                if k in remote_det_cols:
                                    # Safe type cast fallback since mapping raw tables
                                    if v is not None and hasattr(v, '__float__') and not isinstance(v, str) and str(FinalDetTable.columns[k].type) in ['NUMERIC', 'FLOAT', 'INTEGER']:
                                        try: insert_item[k] = float(v)
                                        except: insert_item[k] = None
                                    else:
                                        insert_item[k] = v
                            insert_list.append(insert_item)
                            
                        if insert_list:
                            try:
                                final_db.execute(FinalDetTable.insert(), insert_list)
                                migrated_lineas += len(insert_list)
                                db.execute(LocalDetTable.update().where(
                                    LocalDetTable.c.company_id == company_id,
                                    LocalDetTable.c.estado == "PENDIENTE",
                                    LocalDetTable.c.subcategoria_id == sub.id
                                ).values(estado="MIGRADO"))
                            except Exception as e:
                                print(f"Error bulk inserting details: {e}")

        db.commit()

        return {
            "message": f"Migración exitosa: {migrated_lineas} líneas y {migrated_cabeceras} cabeceras",
            "migrated_lineas": migrated_lineas,
            "migrated_cabeceras": migrated_cabeceras,
            "lote_id": lote_id
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error en migración al destino final: {str(e)}")


@router.get("/cf-diariol")
def list_cf_diariol(
    company_id: int,
    subcategoria_id: Optional[int] = None,
    lote_id: Optional[str] = None,
    estado: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_dest_db)
):
    """Lista registros de cf_diariol (staging)"""
    from backend.app.models.models import CfDiariol
    query = db.query(CfDiariol).filter(CfDiariol.company_id == company_id)
    if subcategoria_id:
        query = query.filter(CfDiariol.subcategoria_id == subcategoria_id)
    if lote_id:
        query = query.filter(CfDiariol.lote_id == lote_id)
    if estado:
        query = query.filter(CfDiariol.estado == estado)
    total = query.count()
    items = query.order_by(CfDiariol.nasiento, CfDiariol.nidlin).offset(skip).limit(limit).all()
    return {
        "total": total,
        "items": [{
            "id": r.id, "cper": r.cper, "cmes": r.cmes, "ccodori": r.ccodori,
            "nasiento": r.nasiento, "nidlin": r.nidlin, "ccodcue": r.ccodcue,
            "ndebe": float(r.ndebe or 0), "nhaber": float(r.nhaber or 0),
            "cglosa": r.cglosa, "estado": r.estado, "lote_id": r.lote_id
        } for r in items]
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

    results = []
    inspector = inspect(dest_engine)

    # Solo queremos una vista por tabla origen única para no duplicar si varias subcats usan la misma
    vistas = {}

    for sub in subcats:
        if not sub.tabla_origen:
            continue
        
        # El ETL formatra el nombre así: "mitabla origen" -> "mitabla_origen"
        table_name = sub.tabla_origen.lower().replace(" ", "_")
        
        if table_name in vistas:
            continue
            
        try:
            if not inspector.has_table(table_name):
                vistas[table_name] = {"table_name": table_name, "total": 0, "items": [], "error": f"Tabla '{table_name}' no existe aún en la base intermedia. Ejecute el Paso 1 primero."}
                continue

            # Obtener todas las columnas
            cols = [c['name'] for c in inspector.get_columns(table_name)]
            has_company = 'company_id' in cols
            
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
                
            total_sql = text(f'SELECT count(*) FROM "{table_name}" {where_sql}')
            data_sql = text(f'SELECT * FROM "{table_name}" {where_sql} LIMIT :limit OFFSET :skip')
            
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


@router.get("/validate-staging")
def validate_staging_data(
    company_id: int,
    subcategoria_id: Optional[int] = None,
    db: Session = Depends(get_dest_db)
):
    """
    Valida los datos ya generados en staging (cf_diario, cf_diariol) contra las restricciones
    de la tabla destino: NOT NULL y Longitud Máxima.
    Retorna un reporte detallado de violaciones para corregir antes de migrar.
    """
    from sqlalchemy import Table, MetaData
    from backend.app.core.database import dest_engine as engine
    import decimal
    import datetime as dt_module

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

            # Leer datos de staging para esta subcategoría
            where_sql = "company_id = :company_id AND subcategoria_id = :sub_id"
            params = {"company_id": company_id, "sub_id": sub.id}

            try:
                count = db.execute(
                    text(f"SELECT count(*) FROM {schema}.{table_name} WHERE {where_sql}"),
                    params
                ).scalar()
            except Exception:
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

            if violations:
                table_info = {
                    "table": table_label_str,
                    "type": table_type,
                    "subcategoria": sub_label,
                    "total_records": count,
                    "violations": violations
                }
                tables_checked.append(table_info)

    total_violations = sum(len(t["violations"]) for t in tables_checked)

    return {
        "company_id": company_id,
        "total_violations": total_violations,
        "tables": tables_checked,
        "status": "OK" if total_violations == 0 else "TIENE_ERRORES"
    }

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
