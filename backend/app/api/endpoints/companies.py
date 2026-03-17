from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from backend.app.core.database import get_dest_db
from backend.app.models.models import (
    Company, SourceConnection, DestinationConnection, TableSelection,
    FinalDestConnection, FinalTableSelection,
    ColumnFilter, ComputedColumnRule,
    MapeoCategoria, MapeoSubcategoria, MapeoLineaAsiento,
    AccountMapping, DocumentTypeMapping,
    UserCatalog, UserCatalogItem
)
from backend.app.schemas.company import (
    CompanyCreate, CompanySchema,
    SourceConnectionCreate, SourceConnectionSchema,
    DestConnectionCreate, DestConnectionSchema,
    TableSelectionCreate, TableSelectionSchema, TableSelectionBulkUpdate,
    FinalDestConnectionCreate, FinalDestConnectionSchema, FinalTableSelectionBulkUpdate
)
from backend.app.services.connection_manager import ConnectionManager
from datetime import datetime

router = APIRouter()

# ─── COMPANIES CRUD ──────────────────────────────────────────────────────────

@router.post("/", response_model=CompanySchema)
def create_company(company: CompanyCreate, db: Session = Depends(get_dest_db)):
    db_company = Company(**company.model_dump())
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company

@router.get("/", response_model=List[CompanySchema])
def read_companies(skip: int = 0, limit: int = 100, db: Session = Depends(get_dest_db)):
    return db.query(Company).offset(skip).limit(limit).all()

@router.get("/{company_id}", response_model=CompanySchema)
def read_company(company_id: int, db: Session = Depends(get_dest_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company

@router.put("/{company_id}", response_model=CompanySchema)
def update_company(company_id: int, company_in: CompanyCreate, db: Session = Depends(get_dest_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    for key, value in company_in.model_dump().items():
        setattr(company, key, value)
    db.commit()
    db.refresh(company)
    return company

@router.delete("/{company_id}")
def delete_company(company_id: int, db: Session = Depends(get_dest_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    db.delete(company)
    db.commit()
    return {"message": "Company deleted successfully"}


@router.post("/{source_id}/clone", response_model=CompanySchema)
def clone_company(
    source_id: int,
    company_in: CompanyCreate,
    db: Session = Depends(get_dest_db)
):
    """Crea una nueva empresa copiando todas las configuraciones de una empresa existente."""
    source = db.query(Company).filter(Company.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source company not found")

    # 1. Crear la nueva empresa
    new_company = Company(**company_in.model_dump())
    db.add(new_company)
    db.flush()  # Para obtener el ID antes del commit

    # Mapas de old_id → new_id para las FK internas
    src_conn_map = {}    # old source_connection.id → new id
    final_conn_map = {}  # old final_dest_connection.id → new id

    # 2. Copiar SourceConnection
    for sc in db.query(SourceConnection).filter(SourceConnection.company_id == source_id).all():
        new_sc = SourceConnection(
            company_id=new_company.id,
            db_type=sc.db_type, host=sc.host, port=sc.port,
            database_name=sc.database_name, username=sc.username,
            password="",  # No copiar contraseñas
            driver=sc.driver, extra_params=sc.extra_params,
            is_active=sc.is_active
        )
        db.add(new_sc)
        db.flush()
        src_conn_map[sc.id] = new_sc.id

    # 3. Copiar TableSelection con ColumnFilter y ComputedColumnRule
    for ts in db.query(TableSelection).filter(TableSelection.company_id == source_id).all():
        new_conn_id = src_conn_map.get(ts.source_connection_id)
        if not new_conn_id:
            continue
        new_ts = TableSelection(
            company_id=new_company.id, source_connection_id=new_conn_id,
            table_schema=ts.table_schema, table_name=ts.table_name,
            is_selected=ts.is_selected, extraction_order=ts.extraction_order,
            custom_query=ts.custom_query, date_column=ts.date_column,
            control_column=ts.control_column, control_column_type=ts.control_column_type,
            description=ts.description
        )
        db.add(new_ts)
        db.flush()

        # Filtros de columna
        for cf in db.query(ColumnFilter).filter(ColumnFilter.table_selection_id == ts.id).all():
            db.add(ColumnFilter(
                table_selection_id=new_ts.id,
                column_name=cf.column_name, operator=cf.operator,
                filter_value=cf.filter_value, filter_value2=cf.filter_value2,
                is_active=cf.is_active
            ))

        # Columnas calculadas
        for cr in db.query(ComputedColumnRule).filter(ComputedColumnRule.table_selection_id == ts.id).all():
            db.add(ComputedColumnRule(
                table_selection_id=new_ts.id,
                new_column_name=cr.new_column_name, source_column=cr.source_column,
                condition_value=cr.condition_value, result_value=cr.result_value,
                default_value=cr.default_value, priority=cr.priority,
                is_active=cr.is_active
            ))

    # 4. Copiar DestinationConnection
    for dc in db.query(DestinationConnection).filter(DestinationConnection.company_id == source_id).all():
        db.add(DestinationConnection(
            company_id=new_company.id,
            host=dc.host, port=dc.port, database_name=dc.database_name,
            username=dc.username, password="",
            is_active=dc.is_active
        ))

    # 5. Copiar FinalDestConnection
    for fc in db.query(FinalDestConnection).filter(FinalDestConnection.company_id == source_id).all():
        new_fc = FinalDestConnection(
            company_id=new_company.id,
            db_type=fc.db_type, host=fc.host, port=fc.port,
            database_name=fc.database_name, username=fc.username, password="",
            target_table=fc.target_table, target_schema=fc.target_schema,
            is_active=fc.is_active
        )
        db.add(new_fc)
        db.flush()
        final_conn_map[fc.id] = new_fc.id

    # 6. Copiar FinalTableSelection
    for fts in db.query(FinalTableSelection).filter(FinalTableSelection.company_id == source_id).all():
        new_fc_id = final_conn_map.get(fts.final_dest_connection_id)
        if not new_fc_id:
            continue
        db.add(FinalTableSelection(
            company_id=new_company.id, final_dest_connection_id=new_fc_id,
            table_schema=fts.table_schema, table_name=fts.table_name,
            is_selected=fts.is_selected, description=fts.description
        ))

    # 7. Copiar MapeoCategoria → MapeoSubcategoria → MapeoLineaAsiento
    for cat in db.query(MapeoCategoria).filter(MapeoCategoria.company_id == source_id).all():
        new_cat = MapeoCategoria(
            company_id=new_company.id,
            nombre=cat.nombre, descripcion=cat.descripcion,
            is_active=cat.is_active
        )
        db.add(new_cat)
        db.flush()

        for sub in db.query(MapeoSubcategoria).filter(MapeoSubcategoria.categoria_id == cat.id).all():
            new_sub = MapeoSubcategoria(
                categoria_id=new_cat.id,
                nombre=sub.nombre, descripcion=sub.descripcion,
                tabla_origen=sub.tabla_origen, codigo_origen=sub.codigo_origen,
                clave_asiento=sub.clave_asiento, mapeo_cabecera=sub.mapeo_cabecera,
                tabla_destino_detalle=sub.tabla_destino_detalle,
                tabla_destino_cabecera=sub.tabla_destino_cabecera,
                col_destino_nasiento=sub.col_destino_nasiento,
                col_destino_nidlin=sub.col_destino_nidlin,
                schema_destino=sub.schema_destino,
                generate_headers=sub.generate_headers,
                generate_details=sub.generate_details,
                asiento_inicial=sub.asiento_inicial,
                filter_rules=sub.filter_rules,
                is_active=sub.is_active
            )
            db.add(new_sub)
            db.flush()

            for linea in db.query(MapeoLineaAsiento).filter(MapeoLineaAsiento.subcategoria_id == sub.id).all():
                db.add(MapeoLineaAsiento(
                    subcategoria_id=new_sub.id,
                    orden=linea.orden, nombre_linea=linea.nombre_linea,
                    mapeo_detalle=linea.mapeo_detalle,
                    condicion_aplicacion=linea.condicion_aplicacion,
                    nivel=linea.nivel, is_active=linea.is_active
                ))

    # 8. Copiar AccountMapping
    for am in db.query(AccountMapping).filter(AccountMapping.company_id == source_id).all():
        db.add(AccountMapping(
            company_id=new_company.id,
            source_account_code=am.source_account_code,
            source_account_name=am.source_account_name,
            dest_account_code=am.dest_account_code,
            dest_cost_center=am.dest_cost_center,
            is_active=am.is_active
        ))

    # 9. Copiar DocumentTypeMapping
    for dm in db.query(DocumentTypeMapping).filter(DocumentTypeMapping.company_id == source_id).all():
        db.add(DocumentTypeMapping(
            company_id=new_company.id,
            source_doc_type=dm.source_doc_type,
            dest_doc_type=dm.dest_doc_type,
            description=dm.description,
            is_active=dm.is_active
        ))

    # 10. Copiar UserCatalog → UserCatalogItem
    for uc in db.query(UserCatalog).filter(UserCatalog.company_id == source_id).all():
        new_uc = UserCatalog(
            company_id=new_company.id,
            name=uc.name, description=uc.description,
            columns=uc.columns
        )
        db.add(new_uc)
        db.flush()

        for item in db.query(UserCatalogItem).filter(UserCatalogItem.catalog_id == uc.id).all():
            db.add(UserCatalogItem(
                catalog_id=new_uc.id,
                data=item.data
            ))

    db.commit()
    db.refresh(new_company)
    return new_company


# ─── SOURCE CONNECTION ───────────────────────────────────────────────────────

@router.get("/{company_id}/source-connection", response_model=SourceConnectionSchema)
def get_source_connection(company_id: int, db: Session = Depends(get_dest_db)):
    conn = db.query(SourceConnection).filter(SourceConnection.company_id == company_id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Source connection not found")
    return conn

@router.post("/{company_id}/source-connection", response_model=SourceConnectionSchema)
def create_or_update_source_connection(
    company_id: int,
    connection_in: SourceConnectionCreate,
    db: Session = Depends(get_dest_db)
):
    conn = db.query(SourceConnection).filter(SourceConnection.company_id == company_id).first()
    if conn:
        for key, value in connection_in.model_dump().items():
            setattr(conn, key, value)
    else:
        conn = SourceConnection(company_id=company_id, **connection_in.model_dump())
        db.add(conn)
    db.commit()
    db.refresh(conn)
    return conn

@router.post("/{company_id}/test-source")
def test_source_connection_endpoint(company_id: int, db: Session = Depends(get_dest_db)):
    conn = db.query(SourceConnection).filter(SourceConnection.company_id == company_id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Source connection not configured")
    conn_data = {
        "host": conn.host, "port": conn.port, "database_name": conn.database_name,
        "username": conn.username, "password": conn.password,
        "driver": conn.driver, "db_type": conn.db_type
    }
    result = ConnectionManager.test_source_connection(conn_data)
    conn.last_tested_at = datetime.now()
    conn.last_test_status = result["status"]
    conn.last_test_message = result["message"]
    db.commit()
    return result


# ─── DESTINATION CONNECTION (BD Intermedia) ──────────────────────────────────

@router.get("/{company_id}/dest-connection", response_model=DestConnectionSchema)
def get_dest_connection(company_id: int, db: Session = Depends(get_dest_db)):
    conn = db.query(DestinationConnection).filter(DestinationConnection.company_id == company_id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Destination connection not found")
    return conn

@router.post("/{company_id}/dest-connection", response_model=DestConnectionSchema)
def create_or_update_dest_connection(
    company_id: int,
    connection_in: DestConnectionCreate,
    db: Session = Depends(get_dest_db)
):
    conn = db.query(DestinationConnection).filter(DestinationConnection.company_id == company_id).first()
    if conn:
        for key, value in connection_in.model_dump().items():
            setattr(conn, key, value)
    else:
        conn = DestinationConnection(company_id=company_id, **connection_in.model_dump())
        db.add(conn)
    db.commit()
    db.refresh(conn)
    return conn

@router.post("/{company_id}/test-dest")
def test_dest_connection_endpoint(company_id: int, db: Session = Depends(get_dest_db)):
    conn = db.query(DestinationConnection).filter(DestinationConnection.company_id == company_id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Destination connection not configured")
    conn_data = {
        "host": conn.host, "port": conn.port, "database_name": conn.database_name,
        "username": conn.username, "password": conn.password
    }
    result = ConnectionManager.test_dest_connection(conn_data)
    conn.last_tested_at = datetime.now()
    conn.last_test_status = result["status"]
    conn.last_test_message = result["message"]
    db.commit()
    return result


# ─── SOURCE TABLE SELECTION ──────────────────────────────────────────────────

@router.get("/{company_id}/tables")
def list_available_tables(company_id: int, db: Session = Depends(get_dest_db)):
    """Lista las tablas disponibles en la base de datos fuente."""
    conn = db.query(SourceConnection).filter(SourceConnection.company_id == company_id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Source connection not configured")
    conn_data = {
        "host": conn.host, "port": conn.port, "database_name": conn.database_name,
        "username": conn.username, "password": conn.password,
        "driver": conn.driver, "db_type": conn.db_type
    }
    try:
        tables = ConnectionManager.list_tables(conn_data)
        selected = db.query(TableSelection).filter(
            TableSelection.company_id == company_id,
            TableSelection.source_connection_id == conn.id
        ).all()
        selected_map = {f"{t.table_schema}.{t.table_name}": t for t in selected}
        for t in tables:
            key = f"{t['table_schema']}.{t['table_name']}"
            if key in selected_map:
                sel = selected_map[key]
                t["is_selected"] = sel.is_selected
                t["selection_id"] = sel.id
                t["control_column"] = sel.control_column
                t["control_column_type"] = sel.control_column_type
                t["extraction_order"] = sel.extraction_order
            else:
                t["is_selected"] = False
                t["selection_id"] = None
                t["control_column"] = None
                t["control_column_type"] = "DATE"
                t["extraction_order"] = 0
        return tables
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{company_id}/table-selections")
def update_table_selections(
    company_id: int,
    bulk_update: TableSelectionBulkUpdate,
    db: Session = Depends(get_dest_db)
):
    conn = db.query(SourceConnection).filter(SourceConnection.company_id == company_id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Source connection not configured")
    for item in bulk_update.selections:
        selection = db.query(TableSelection).filter(
            TableSelection.company_id == company_id,
            TableSelection.source_connection_id == conn.id,
            TableSelection.table_schema == item['table_schema'],
            TableSelection.table_name == item['table_name']
        ).first()
        if selection:
            selection.is_selected = item['is_selected']
            if 'custom_query' in item: selection.custom_query = item['custom_query']
            if 'date_column' in item: selection.date_column = item['date_column']
            if 'extraction_order' in item: selection.extraction_order = item['extraction_order']
        else:
            if item['is_selected']:
                new_selection = TableSelection(
                    company_id=company_id, source_connection_id=conn.id,
                    table_schema=item['table_schema'], table_name=item['table_name'],
                    is_selected=item['is_selected'],
                    custom_query=item.get('custom_query'), date_column=item.get('date_column'),
                    extraction_order=item.get('extraction_order', 0)
                )
                db.add(new_selection)
    db.commit()
    return {"message": "Selections updated successfully"}


# ─── FINAL DESTINATION (Contabilidad) ────────────────────────────────────────

@router.get("/{company_id}/final-dest-connection", response_model=FinalDestConnectionSchema)
def get_final_dest_connection(company_id: int, db: Session = Depends(get_dest_db)):
    conn = db.query(FinalDestConnection).filter(FinalDestConnection.company_id == company_id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Final destination connection not found")
    return conn

@router.post("/{company_id}/final-dest-connection", response_model=FinalDestConnectionSchema)
def create_or_update_final_dest_connection(
    company_id: int,
    connection_in: FinalDestConnectionCreate,
    db: Session = Depends(get_dest_db)
):
    conn = db.query(FinalDestConnection).filter(FinalDestConnection.company_id == company_id).first()
    if conn:
        for key, value in connection_in.model_dump().items():
            setattr(conn, key, value)
    else:
        conn = FinalDestConnection(company_id=company_id, **connection_in.model_dump())
        db.add(conn)
    db.commit()
    db.refresh(conn)
    return conn

@router.post("/{company_id}/test-final-dest")
def test_final_dest_connection_endpoint(company_id: int, db: Session = Depends(get_dest_db)):
    """Prueba la conexión al destino final de contabilidad."""
    conn = db.query(FinalDestConnection).filter(FinalDestConnection.company_id == company_id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Final destination connection not configured")
    conn_data = {
        "host": conn.host, "port": conn.port, "database_name": conn.database_name,
        "username": conn.username, "password": conn.password
    }
    result = ConnectionManager.test_dest_connection(conn_data)
    conn.last_tested_at = datetime.now()
    conn.last_test_status = result["status"]
    conn.last_test_message = result["message"]
    db.commit()
    return result

@router.get("/{company_id}/final-dest-tables")
def list_final_dest_tables(company_id: int, db: Session = Depends(get_dest_db)):
    """Lista las tablas disponibles en la base de datos destino final de contabilidad."""
    conn = db.query(FinalDestConnection).filter(FinalDestConnection.company_id == company_id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Final destination connection not configured")
    conn_data = {
        "host": conn.host, "port": conn.port, "database_name": conn.database_name,
        "username": conn.username, "password": conn.password
    }
    try:
        tables = ConnectionManager.list_postgres_tables(conn_data)
        # Marcar tablas ya seleccionadas
        selected = db.query(FinalTableSelection).filter(
            FinalTableSelection.company_id == company_id,
            FinalTableSelection.final_dest_connection_id == conn.id
        ).all()
        selected_map = {f"{t.table_schema}.{t.table_name}": t for t in selected}
        for t in tables:
            key = f"{t['table_schema']}.{t['table_name']}"
            t["is_selected"] = selected_map[key].is_selected if key in selected_map else False
            t["selection_id"] = selected_map[key].id if key in selected_map else None
        return tables
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{company_id}/final-table-selections")
def update_final_table_selections(
    company_id: int,
    bulk_update: FinalTableSelectionBulkUpdate,
    db: Session = Depends(get_dest_db)
):
    """Actualiza las tablas destino seleccionadas en la BD de contabilidad."""
    conn = db.query(FinalDestConnection).filter(FinalDestConnection.company_id == company_id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Final destination connection not configured")
    for item in bulk_update.selections:
        selection = db.query(FinalTableSelection).filter(
            FinalTableSelection.company_id == company_id,
            FinalTableSelection.final_dest_connection_id == conn.id,
            FinalTableSelection.table_schema == item['table_schema'],
            FinalTableSelection.table_name == item['table_name']
        ).first()
        if selection:
            selection.is_selected = item['is_selected']
        else:
            if item['is_selected']:
                new_sel = FinalTableSelection(
                    company_id=company_id, final_dest_connection_id=conn.id,
                    table_schema=item['table_schema'], table_name=item['table_name'],
                    is_selected=True
                )
                db.add(new_sel)
    db.commit()
    return {"message": "Final table selections updated successfully"}

@router.get("/{company_id}/source-table-columns")
def get_source_table_columns(
    company_id: int, table_name: str, table_schema: str = "dbo",
    db: Session = Depends(get_dest_db)
):
    """Obtiene las columnas de una tabla en la BD ORIGEN (SQL Server)."""
    conn = db.query(SourceConnection).filter(SourceConnection.company_id == company_id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Source connection not configured")
    
    conn_data = {
        "host": conn.host, "port": conn.port,
        "database_name": conn.database_name,
        "username": conn.username, "password": conn.password,
        "driver": conn.driver, "db_type": conn.db_type
    }
    
    try:
        columns = ConnectionManager.get_table_columns(conn_data, table_schema, table_name)
        return columns
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{company_id}/dest-table-columns")
def get_dest_table_columns(
    company_id: int, table_name: str = "",
    db: Session = Depends(get_dest_db)
):
    """Obtiene las columnas de una tabla en la BD intermedia (migconta_db)."""
    from backend.app.core.database import dest_engine
    from sqlalchemy import text as sql_text
    try:
        with dest_engine.connect() as conn:
            result = conn.execute(sql_text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = :tname ORDER BY ordinal_position"
            ), {"tname": table_name.lower()})
            columns = [row[0] for row in result.fetchall()]
        return {"columns": columns}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{company_id}/final-dest-table-columns")
def get_final_dest_table_columns(
    company_id: int, table_schema: str = "public", table_name: str = "",
    db: Session = Depends(get_dest_db)
):
    """Obtiene las columnas de una tabla en la BD destino final."""
    conn = db.query(FinalDestConnection).filter(FinalDestConnection.company_id == company_id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Final destination connection not configured")
    conn_data = {
        "host": conn.host, "port": conn.port, "database_name": conn.database_name,
        "username": conn.username, "password": conn.password
    }
    try:
        columns = ConnectionManager.get_postgres_table_columns(conn_data, table_schema, table_name)
        return columns
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{company_id}/intermediate-tables")
def list_intermediate_tables(company_id: int, db: Session = Depends(get_dest_db)):
    """Lista las tablas en la BD intermedia (migconta_db)."""
    from backend.app.core.database import dest_engine
    from sqlalchemy import text as sql_text
    try:
        with dest_engine.connect() as conn:
            # Listar tablas base del schema public, excluyendo las del sistema (alembic, etc)
            query = sql_text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                  AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            result = conn.execute(query)
            tables = [row[0] for row in result.fetchall()]
            
            # Filtrar tablas internas del sistema si se desea, 
            # pero mejor mostrar todas para depuración/flexibilidad exceptuando alembic
            tables = [t for t in tables if t != 'alembic_version']
            
        return tables
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def _map_pg_column_type(col: dict) -> str:
    """
    Mapea la metadata de information_schema.columns a un tipo SQL válido para CREATE TABLE.
    Maneja correctamente: VARCHAR(n), CHAR(n), NUMERIC(p,s), INTEGER, SMALLINT, BIGINT,
    DATE, BOOLEAN, TEXT, REAL, DOUBLE PRECISION, TIMESTAMP, etc.
    """
    ctype = col['data_type']
    max_len = col.get('max_length')
    precision = col.get('numeric_precision')
    scale = col.get('numeric_scale')

    if ctype == 'character varying':
        return f"VARCHAR({max_len})" if max_len else "VARCHAR"
    elif ctype == 'character':
        return f"CHAR({max_len})" if max_len else "CHAR(1)"
    elif ctype == 'numeric':
        if precision is not None and scale is not None:
            return f"NUMERIC({precision},{scale})"
        elif precision is not None:
            return f"NUMERIC({precision})"
        return "NUMERIC"
    elif ctype == 'integer':
        return "INTEGER"
    elif ctype == 'smallint':
        return "SMALLINT"
    elif ctype == 'bigint':
        return "BIGINT"
    elif ctype == 'real':
        return "REAL"
    elif ctype == 'double precision':
        return "DOUBLE PRECISION"
    elif ctype == 'boolean':
        return "BOOLEAN"
    elif ctype == 'date':
        return "DATE"
    elif ctype == 'text':
        return "TEXT"
    elif ctype == 'timestamp without time zone':
        return "TIMESTAMP"
    elif ctype == 'timestamp with time zone':
        return "TIMESTAMP WITH TIME ZONE"
    elif ctype == 'time without time zone':
        return "TIME"
    elif ctype == 'time with time zone':
        return "TIME WITH TIME ZONE"
    elif ctype == 'bytea':
        return "BYTEA"
    elif ctype == 'uuid':
        return "UUID"
    elif ctype == 'json':
        return "JSON"
    elif ctype == 'jsonb':
        return "JSONB"
    else:
        # Fallback: use as-is (covers USER-DEFINED types, etc.)
        return ctype.upper()


def _build_col_definition(col: dict, for_staging: bool = True) -> str:
    """
    Construye la definición de columna completa: nombre, tipo, nullable, default.
    Si for_staging=True, fuerza NULL para flexibilidad de staging.
    """
    cname = col['column_name']
    ctype = _map_pg_column_type(col)
    
    parts = [f'"{cname}"', ctype]
    
    # Preservar defaults (excluyendo secuencias como nextval)
    col_default = col.get('column_default')
    if col_default and 'nextval' not in str(col_default):
        parts.append(f"DEFAULT {col_default}")
    
    if for_staging:
        parts.append("NULL")
    else:
        nullable = col.get('is_nullable', 'YES')
        if nullable == 'NO':
            parts.append("NOT NULL")
    
    return " ".join(parts)


@router.post("/{company_id}/clone-final-table")
def clone_final_table(
    company_id: int, 
    body: dict, 
    db: Session = Depends(get_dest_db)
):
    table_name = body.get("table_name")
    table_schema = body.get("table_schema", "public")
    if not table_name:
        raise HTTPException(status_code=400, detail="Missing table_name")
    
    conn = db.query(FinalDestConnection).filter(FinalDestConnection.company_id == company_id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Final connection not found")
        
    conn_data = {
        "host": conn.host, "port": conn.port, "database_name": conn.database_name,
        "username": conn.username, "password": conn.password
    }
    
    try:
        columns = ConnectionManager.get_postgres_table_columns(conn_data, table_schema, table_name)
        if not columns:
            raise HTTPException(status_code=404, detail="Table not found or has no columns in final destination")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading source columns: {e}")
        
    # Build column definitions
    col_defs = []
    # Add internal columns first
    col_defs.append("id SERIAL PRIMARY KEY")
    col_defs.append("company_id INTEGER")
    col_defs.append("subcategoria_id INTEGER")
    col_defs.append("lote_id VARCHAR(50)")
    col_defs.append("estado VARCHAR(20) DEFAULT 'PENDIENTE'")
    col_defs.append("created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP")
    
    # Add cloned columns with correct types
    for col in columns:
        col_defs.append(_build_col_definition(col, for_staging=True))
        
    create_stmt = f'CREATE TABLE IF NOT EXISTS public."{table_name}" (\n    ' + ",\n    ".join(col_defs) + '\n);'
    drop_stmt = f'DROP TABLE IF EXISTS public."{table_name}" CASCADE;'
    
    from backend.app.core.database import dest_engine
    from sqlalchemy import text
    try:
        with dest_engine.begin() as local_conn:
            local_conn.execute(text(drop_stmt))
            local_conn.execute(text(create_stmt))
            
            # Create indexes
            local_conn.execute(text(f'CREATE INDEX IF NOT EXISTS "ix_{table_name}_company_id" ON "{table_name}" (company_id);'))
            local_conn.execute(text(f'CREATE INDEX IF NOT EXISTS "ix_{table_name}_estado" ON "{table_name}" (estado);'))
            local_conn.execute(text(f'CREATE INDEX IF NOT EXISTS "ix_{table_name}_lote_id" ON "{table_name}" (lote_id);'))
            
        return {"message": f"Tabla '{table_name}' clonada a base de datos intermedia exitosamente.", "table_name": table_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating staging table: {e}")


@router.post("/{company_id}/sync-final-table-columns")
def sync_final_table_columns(
    company_id: int,
    body: dict,
    db: Session = Depends(get_dest_db)
):
    """
    Compara columnas de la tabla en destino final vs la tabla clonada en migconta_db.
    Si hay columnas nuevas en destino final que no existen localmente, las agrega via ALTER TABLE.
    No elimina datos existentes.
    """
    table_name = body.get("table_name")
    table_schema = body.get("table_schema", "public")
    if not table_name:
        raise HTTPException(status_code=400, detail="Missing table_name")

    conn = db.query(FinalDestConnection).filter(FinalDestConnection.company_id == company_id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Final connection not found")

    conn_data = {
        "host": conn.host, "port": conn.port, "database_name": conn.database_name,
        "username": conn.username, "password": conn.password
    }

    # 1. Leer columnas del destino final (remoto)
    try:
        remote_columns = ConnectionManager.get_postgres_table_columns(conn_data, table_schema, table_name)
        if not remote_columns:
            raise HTTPException(status_code=404, detail="Tabla no encontrada en destino final")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error leyendo columnas remotas: {e}")

    # 2. Leer columnas de la tabla local en migconta_db
    from backend.app.core.database import dest_engine
    from sqlalchemy import text, inspect as sa_inspect

    try:
        inspector = sa_inspect(dest_engine)
        if table_name not in inspector.get_table_names(schema="public"):
            raise HTTPException(
                status_code=404,
                detail=f"La tabla '{table_name}' no existe localmente. Use 'Clonar Estructura' primero."
            )
        local_columns_info = inspector.get_columns(table_name, schema="public")
        local_col_names = {col['name'].lower() for col in local_columns_info}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error leyendo columnas locales: {e}")

    # 3. Comparar y encontrar columnas faltantes
    # Columnas internas de MigConta que no vienen del destino final
    internal_cols = {"id", "company_id", "subcategoria_id", "lote_id", "estado", "created_at"}
    
    new_columns = []
    for col in remote_columns:
        cname = col['column_name']
        if cname.lower() not in local_col_names and cname.lower() not in internal_cols:
            ctype = _map_pg_column_type(col)
            new_columns.append({"name": cname, "type": ctype})

    if not new_columns:
        return {
            "message": f"La tabla '{table_name}' ya tiene todas las columnas del destino final. No hay columnas nuevas.",
            "table_name": table_name,
            "added_columns": [],
            "total_new": 0
        }

    # 4. Agregar columnas faltantes via ALTER TABLE
    added = []
    errors = []
    try:
        with dest_engine.begin() as local_conn:
            for col in new_columns:
                try:
                    alter_stmt = f'ALTER TABLE public."{table_name}" ADD COLUMN "{col["name"]}" {col["type"]} NULL;'
                    local_conn.execute(text(alter_stmt))
                    added.append(col["name"])
                except Exception as col_err:
                    errors.append(f"{col['name']}: {col_err}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error agregando columnas: {e}")

    msg = f"Se agregaron {len(added)} columna(s) nueva(s) a '{table_name}'."
    if errors:
        msg += f" {len(errors)} error(es): {'; '.join(errors)}"

    return {
        "message": msg,
        "table_name": table_name,
        "added_columns": added,
        "total_new": len(added),
        "errors": errors
    }
