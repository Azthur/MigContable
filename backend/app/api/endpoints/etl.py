from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import date, datetime
from typing import Optional, List
import uuid
import pandas as pd
from backend.app.core.database import get_dest_db
from backend.app.models.models import (
    IntegLog, Company, SourceConnection, DestinationConnection,
    TableSelection, ColumnFilter, MigrationControl,
    MapeoSubcategoria, MapeoLineaAsiento, AsientoContableGenerado,
    ComputedColumnRule
)
from backend.app.services.connection_manager import ConnectionManager

router = APIRouter()


# ─── ETL Incremental con Filtros ─────────────────────────────────────────────

def build_where_clause(filters: List[ColumnFilter], control: MigrationControl = None, start_date: str = None, end_date: str = None, param_style='qmark') -> tuple:
    """Construye la cláusula WHERE con los filtros configurados y el control incremental"""
    
    # Force qmark style for PyODBC/MSSQL compatibility
    # params will be a list, placeholders will be ?
    conditions = []
    params = []
    
    def add_param(value):
        params.append(value)
        return "?"

    for i, f in enumerate(filters):
        if not f.is_active:
            continue
        col = f"[{f.column_name}]"
        op = f.operator.upper()

        if op == "IS NULL":
            conditions.append(f"{col} IS NULL")
        elif op == "IS NOT NULL":
            conditions.append(f"{col} IS NOT NULL")
        elif op == "BETWEEN" and f.filter_value and f.filter_value2:
            p_a = add_param(f.filter_value)
            p_b = add_param(f.filter_value2)
            conditions.append(f"{col} BETWEEN {p_a} AND {p_b}")
        elif op == "IN" and f.filter_value:
            vals = [v.strip() for v in f.filter_value.split(",")]
            placeholders_list = []
            for v in vals:
                p = add_param(v)
                placeholders_list.append(p)
            placeholders = ", ".join(placeholders_list)
            conditions.append(f"{col} IN ({placeholders})")
        elif op == "LIKE" and f.filter_value:
            p = add_param(f.filter_value)
            conditions.append(f"{col} LIKE {p}")
        elif f.filter_value:
            p = add_param(f.filter_value)
            conditions.append(f"{col} {op} {p}")

    # Date Range (Manual Override)
    if start_date and control and control.control_column:
        col = f"[{control.control_column}]"
        p = add_param(start_date)
        conditions.append(f"{col} >= {p}")
        
    if end_date and control and control.control_column:
        col = f"[{control.control_column}]"
        p = add_param(end_date)
        conditions.append(f"{col} <= {p}")

    # Incremental
    if not start_date and control and control.control_column and control.last_migrated_value:
        cols = [c.strip() for c in control.control_column.split(',')]
        if len(cols) == 1:
            col = f"[{control.control_column}]"
            p = add_param(control.last_migrated_value)
            conditions.append(f"{col} > {p}")
        # If len(cols) > 1, we intentionally skip SQL-based incremental tracking 
        # to prevent lexicographical jump bugs with non-monotonic categorical keys like coddoc.
        # Instead, we rely entirely on the Pandas idcontrol-based set difference below.

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    return where, params


def __get_col_simple(col_name, dataframe):
    """Busca una columna en el DataFrame ignorando mayúsculas/minúsculas y espacios."""
    if not col_name: return None
    col_clean = col_name.strip().upper()
    for c in dataframe.columns:
        if c.strip().upper() == col_clean: return c
    return None

def __apply_computed_rules(df, computed_rules, db, company_id, table_name):
    df_cols_lower = {str(c).lower(): str(c) for c in df.columns}
    from collections import defaultdict
    grouped = defaultdict(list)
    for rule in computed_rules:
        r_lower = rule.new_column_name.lower()
        actual_col = df_cols_lower.get(r_lower, rule.new_column_name)
        grouped[actual_col].append(rule)
    
    for new_col, col_rules in grouped.items():
        default = ""
        for cr in col_rules:
            if cr.default_value:
                default = cr.default_value
                break
        df[new_col] = default
        
        for rule in reversed(col_rules):
            try:
                val_upper = rule.condition_value.strip().upper()
                if val_upper in ("BUSCARX_TC_VENTA", "BUSCARX_TC_COMPRA"):
                    if rule.source_column in df.columns:
                        tc_col = "venta" if "VENTA" in val_upper else "compra"
                        from backend.app.models.models import TipoCambio
                        tc_rows = db.query(TipoCambio).all()
                        tc_map = {str(r.fecha): float(getattr(r, tc_col)) for r in tc_rows}
                        df[new_col] = df[rule.source_column].astype(str).str[:10].map(tc_map)
                        if default:
                            df[new_col] = df[new_col].fillna(float(default) if default.replace('.','',1).isdigit() else default)
                        else:
                            df[new_col] = df[new_col].fillna(0)
                        
                elif any(val_upper.startswith(p) for p in [
                    "CONCAT(", "LEFT(", "RIGHT(", "SI.CONJUNTO(", 
                    "BUSCARX(", "BUSCARX_EXT(", "BUSCARX_LOCAL(", "SUMA(", "RESTA(", "MULTIPLICA(", "DIVIDE(", "REDONDEAR(", "ABS(",
                    "LARGO(", "ESPACIOS(", "MAYUSC(", "REPETIR(", "TEXTO(", "AÑO(", "MES(", "Y(", "O("
                ]):
                    from backend.app.core.formula_parser import evaluate_formula_on_df
                    df[new_col] = evaluate_formula_on_df(
                        df=df, formula_str=rule.condition_value,
                        db=db, company_id=company_id, default=default if default else ""
                    )
                else:
                    actual_src = __get_col_simple(rule.source_column, df)
                    if actual_src:
                        mask = df[actual_src].astype(str).str.strip().str.upper() == val_upper
                        df.loc[mask, new_col] = rule.result_value
            except Exception as rule_err:
                rule_detail = f"Tabla: {table_name} | Columna Calculada: '{new_col}' | Regla ID: {rule.id} | Col Origen: '{rule.source_column}' | Fórmula/Valor: '{rule.condition_value}' | Error: {rule_err}"
                print(f"ERROR en columna calculada: {rule_detail}")
                raise Exception(rule_detail)


def run_incremental_etl(company_id: int, table_selection_id: int, db: Session, start_date: str = None, end_date: str = None, full_refresh: bool = False):
    """Ejecuta ETL incremental para una tabla específica con sus filtros"""
    sel = db.query(TableSelection).filter(TableSelection.id == table_selection_id).first()
    if not sel:
        return {"status": "ERROR", "message": "Selección de tabla no encontrada"}
        


    source_conn = db.query(SourceConnection).filter(SourceConnection.company_id == company_id).first()
    dest_conn = db.query(DestinationConnection).filter(DestinationConnection.company_id == company_id).first()

    if not source_conn or not dest_conn:
        return {"status": "ERROR", "message": "Conexiones no configuradas"}

    # Obtener filtros activos
    filters = db.query(ColumnFilter).filter(
        ColumnFilter.table_selection_id == table_selection_id,
        ColumnFilter.is_active == True
    ).all()

    # Obtener control incremental
    control = db.query(MigrationControl).filter(
        MigrationControl.company_id == company_id,
        MigrationControl.source_table == sel.table_name
    ).first()

    
    # If control type is not DATE, ignore dates to avoid SQL errors
    apply_dates = False
    if sel.control_column and sel.control_column_type and "DATE" in sel.control_column_type.upper():
         apply_dates = True
    p_style = "qmark" # Default to qmark for reliability with pyodbc/MSSQL
    
    active_control = control if not full_refresh else None
    active_start = start_date if apply_dates and not full_refresh else None
    active_end = end_date if apply_dates and not full_refresh else None

    where_clause, params = build_where_clause(filters, active_control, 
                                              active_start, 
                                              active_end,
                                              param_style=p_style)

    # Construir query de extracción
    schema = sel.table_schema or "dbo"
    query = f"SELECT * FROM [{schema}].[{sel.table_name}] {where_clause}"
    
    try:
        with open("C:\\SistemaMigConta\\debug_etl.txt", "a") as f:
            f.write(f"Query: {query}\nParams: {params}\n")
    except:
        pass

    log = IntegLog(
        company_id=company_id,
        process_name=f"ETL Incremental - {sel.table_name}",
        status="RUNNING",
        message=f"DEBUG: p_style={p_style} query={query} | Iniciando extracción..."
    )
    db.add(log)
    db.commit()

    try:
        computed_rules = db.query(ComputedColumnRule).filter(
            ComputedColumnRule.table_selection_id == table_selection_id,
            ComputedColumnRule.is_active == True
        ).order_by(ComputedColumnRule.priority).all()
        # Conectar a origen (SQL Server)
        src_data = {
            "host": source_conn.host, "port": source_conn.port,
            "database_name": source_conn.database_name,
            "username": source_conn.username, "password": source_conn.password,
            "driver": source_conn.driver, "db_type": source_conn.db_type
        }
        src_engine = ConnectionManager.get_source_engine(src_data)

        # Conectar a destino (migconta_db)
        dst_data = {
            "host": dest_conn.host, "port": dest_conn.port,
            "database_name": dest_conn.database_name,
            "username": dest_conn.username, "password": dest_conn.password
        }
        dst_engine = ConnectionManager.get_dest_engine(dst_data)

        # Usar pandas para leer y escribir
        import pandas as pd
        
        # Leer desde origen usando conexión raw pyodbc para evitar que SQLAlchemy
        # recompile la query y elimine los marcadores '?' (qmark style).
        # raw_connection() devuelve la conexión pyodbc subyacente directamente.
        raw_conn = src_engine.raw_connection()
        try:
            if params:
                df = pd.read_sql(query, raw_conn, params=tuple(params))
            else:
                df = pd.read_sql(query, raw_conn)
        finally:
            raw_conn.close()
                       
        # Add Unique Migration ID (as requested by user for mapping)
        if not df.empty:
            df['_migration_id'] = [str(uuid.uuid4()) for _ in range(len(df))]
            # Ensure company_id exists
            if 'company_id' not in df.columns:
                df['company_id'] = company_id
                
            # ── Calcular IDCONTROL unificado ──
            try:
                # Normalizar columnas del DF (quitar espacios y a minúsculas para comparar)
                df.columns = [c.strip() for c in df.columns]
                df_cols_lower = [c.lower() for c in df.columns]
                
                ctrl_cols = [c.strip().lower() for c in (sel.control_column or "CodCia,coddoc,nrodoc").split(",")]
                actual_cols = [col for col in df.columns if col.lower() in ctrl_cols]
                
                if actual_cols:
                    df['idcontrol'] = df[actual_cols].astype(str).agg('-'.join, axis=1)
                    diag_msg = f" | [IDCONTROL OK] Cols: {actual_cols}"
                    
                    if not full_refresh:
                        try:
                            from sqlalchemy import text, inspect
                            insp = inspect(dst_engine)
                            table_dest_empty = sel.table_name.lower().replace(" ", "_")
                            if insp.has_table(table_dest_empty):
                                cols_in_dest = [c['name'] for c in insp.get_columns(table_dest_empty)]
                                if 'idcontrol' in cols_in_dest:
                                    with dst_engine.connect() as d_conn:
                                        existing_ids_df = pd.read_sql(text(f'SELECT idcontrol FROM "{table_dest_empty}" WHERE company_id = {company_id}'), d_conn)
                                        existing_ids = set(existing_ids_df['idcontrol'].dropna())
                                        if existing_ids:
                                            df = df[~df['idcontrol'].isin(existing_ids)]
                                            diag_msg += f" | Filtro Delta: Extraídos nuevos descartando registros existentes."
                        except Exception as delta_e:
                            diag_msg += f" | [ERROR DELTA PANDAS] {delta_e}"
                else:
                    df['idcontrol'] = None # Siempre crear la columna
                    diag_msg = f" | [IDCONTROL NOT FOUND] Buscaba: {ctrl_cols} en: {df_cols_lower[:8]}"
                
                if hasattr(log, "message"):
                    if log.message is None: log.message = ""
                    log.message += diag_msg
            except Exception as e:
                df['idcontrol'] = None
                if hasattr(log, "message"):
                    if log.message is None: log.message = ""
                    log.message += f" | [IDCONTROL ERROR] {e}"
            
            # ── Aplicar Columnas Calculadas (condicionales tipo Excel) ──
            if computed_rules:
                __apply_computed_rules(df, computed_rules, db, company_id, sel.table_name)

        # ── Reaplicar reglas a registros pendientes (Incremental sin Full Refresh) ──
        if not full_refresh and computed_rules:
            table_dest_name = sel.table_name.lower().replace(" ", "_")
            print(f"DEBUG ETL: Incremental computing rules for {table_dest_name}")
            try:
                from sqlalchemy import text, inspect
                import pandas as pd
                import numpy as np
                
                insp = inspect(dst_engine)
                col_info_list = insp.get_columns(table_dest_name)
                existing_columns = [c['name'] for c in col_info_list]
                # Mapa de tipos de destino: nombre_col -> tipo PostgreSQL (str)
                dest_type_map = {c['name']: str(c['type']).upper() for c in col_info_list}
                
                # Garantizar que _migration_id exista y esté poblado ANTES de extraer df_pending
                with dst_engine.begin() as conn:
                    if "_migration_id" not in existing_columns:
                        try:
                            conn.execute(text(f'ALTER TABLE "{table_dest_name}" ADD COLUMN "_migration_id" TEXT'))
                            existing_columns.append("_migration_id")
                        except Exception as em:
                            print(f"Warn: No se pudo agregar _migration_id a {table_dest_name}: {em}")
                    
                    try:
                        conn.execute(text(f'UPDATE "{table_dest_name}" SET "_migration_id" = MD5(random()::text || clock_timestamp()::text) WHERE "_migration_id" IS NULL'))
                    except Exception as em2:
                        print(f"Warn: No se pudo poblar _migration_id: {em2}")
                
                where_clause = "company_id = :cid"
                if "estado" in existing_columns:
                    where_clause += " AND (estado IS NULL OR estado != 'MIGRADO')"
                    
                query_pend = text(f'SELECT * FROM "{table_dest_name}" WHERE {where_clause}')
                with dst_engine.connect() as conn:
                    df_pending = pd.read_sql(query_pend, conn, params={"cid": company_id})
                
                print(f"DEBUG ETL: df_pending length is {len(df_pending)}")
                
                if not df_pending.empty:
                    print("DEBUG ETL: Running __apply_computed_rules")
                    __apply_computed_rules(df_pending, computed_rules, db, company_id, sel.table_name)
                    
                    # Identificar columnas calculadas a actualizar
                    update_cols = []
                    df_cols_lower_pending = {str(c).lower(): str(c) for c in df_pending.columns}
                    for r in computed_rules:
                        r_lower = r.new_column_name.lower()
                        if r_lower in df_cols_lower_pending:
                            actual_col_name = df_cols_lower_pending[r_lower]
                            if actual_col_name not in update_cols:
                                update_cols.append(actual_col_name)
                    
                    # ── Coercer tipos de datos de columnas calculadas ──
                    # Las fórmulas producen TEXT pero la tabla destino puede tener BIGINT, DOUBLE, etc.
                    for col in update_cols:
                        col_type = dest_type_map.get(col, 'TEXT')
                        if 'INT' in col_type:
                            df_pending[col] = pd.to_numeric(df_pending[col], errors='coerce')
                            # Usar Int64 nullable para no perder NaN -> NULL
                            try:
                                df_pending[col] = df_pending[col].astype('Int64')
                            except Exception:
                                pass
                        elif any(t in col_type for t in ['DOUBLE', 'FLOAT', 'NUMERIC', 'REAL', 'DECIMAL']):
                            df_pending[col] = pd.to_numeric(df_pending[col], errors='coerce')
                        elif 'TIMESTAMP' in col_type or 'DATE' in col_type:
                            df_pending[col] = pd.to_datetime(df_pending[col], errors='coerce')
                        else:
                            # TEXT: limpiar valores nulos/vacíos
                            if df_pending[col].dtype == 'object':
                                df_pending[col] = df_pending[col].apply(
                                    lambda x: None if pd.isna(x) or str(x).strip() in ['', 'nan', 'None', '<NA>'] else x
                                )
                    
                    # Limpiar TODAS las columnas object restantes (no solo las calculadas)
                    for col in df_pending.select_dtypes(include=['object']).columns:
                        df_pending[col] = df_pending[col].apply(
                            lambda x: None if pd.isna(x) or str(x).strip() in ['', 'nan', 'None'] else x
                        )
                    
                    temp_table = f"temp_update_{table_dest_name}_{company_id}"
                    # Crear tabla temporal SIN dtype_map para evitar conflictos de tipos
                    df_pending.to_sql(temp_table, dst_engine, if_exists="replace", index=False)
                    print(f"DEBUG ETL: temp table {temp_table} creado con {len(df_pending)} filas")
                    
                    if update_cols:
                        # Elegir columna de match
                        if "_migration_id" in existing_columns:
                            match_col = "_migration_id"
                        elif "idcontrol" in existing_columns:
                            match_col = "idcontrol"
                        elif "id" in existing_columns:
                            match_col = "id"
                        else:
                            match_col = None
                            
                        if match_col:
                            # 1. Asegurar que las columnas calculadas existan en la tabla destino
                            with dst_engine.begin() as conn:
                                for new_col in update_cols:
                                    if new_col not in existing_columns:
                                        try:
                                            safe_col = new_col.replace('"', '""')
                                            conn.execute(text(f'ALTER TABLE "{table_dest_name}" ADD COLUMN "{safe_col}" TEXT'))
                                            existing_columns.append(new_col)
                                        except Exception as e:
                                            print(f"Error agregando calculada pendiente {new_col}: {e}")

                            # 2. Construir SET con CAST explícito por seguridad de tipos
                            set_parts = []
                            for c in update_cols:
                                ct = dest_type_map.get(c, 'TEXT')
                                if 'INT' in ct:
                                    set_parts.append(f'"{c}" = CASE WHEN temp."{c}" IS NULL THEN NULL ELSE CAST(temp."{c}" AS {ct}) END')
                                elif any(t in ct for t in ['DOUBLE', 'FLOAT', 'NUMERIC', 'REAL', 'DECIMAL']):
                                    set_parts.append(f'"{c}" = CASE WHEN temp."{c}" IS NULL THEN NULL ELSE CAST(temp."{c}" AS {ct}) END')
                                else:
                                    set_parts.append(f'"{c}" = temp."{c}"')
                            
                            set_clause = ", ".join(set_parts)
                            update_sql = f"""
                                UPDATE "{table_dest_name}" t
                                SET {set_clause}
                                FROM "{temp_table}" temp
                                WHERE t."{match_col}" = temp."{match_col}"
                            """
                            with dst_engine.begin() as conn:
                                conn.execute(text(update_sql))
                                conn.execute(text(f'DROP TABLE "{temp_table}"'))
                            log.message = log.message or ""
                            log.message += f" | Fórmulas actualizadas en {len(df_pending)} registros pendientes"
                            print(f"DEBUG ETL: Fórmulas OK para {table_dest_name}: {len(df_pending)} registros, {len(update_cols)} columnas")
                        else:
                            print(f"No key column found to update pending formulas in {table_dest_name}")
                            with dst_engine.begin() as conn:
                                conn.execute(text(f'DROP TABLE "{temp_table}"'))
                    else:
                        # No hay columnas para actualizar, limpiar temp table
                        with dst_engine.begin() as conn:
                            conn.execute(text(f'DROP TABLE "{temp_table}"'))
            except Exception as ev_e:
                import traceback
                traceback.print_exc()
                print(f"Error reevaluando formulas en pendientes de {table_dest_name}: {ev_e}")
                log.message = (log.message or "") + f" | [ERROR FORMULAS] {ev_e}"

        rows_count = len(df)

        if rows_count == 0:
            table_dest_empty = sel.table_name.lower().replace(" ", "_")
            if full_refresh:
                # Si piden full refresh y origen está vacío, solo borramos los registros de la empresa
                try:
                    from sqlalchemy import text
                    with dst_engine.begin() as conn:
                        conn.execute(text(f'DELETE FROM "{table_dest_empty}" WHERE company_id = {company_id}'))
                except:
                    pass
            else:
                # Crear la tabla vacía si aún no existe, para que no falle el preview
                from sqlalchemy import inspect as sa_inspect
                insp = sa_inspect(dst_engine)
                if not insp.has_table(table_dest_empty):
                    try:
                        df.head(0).to_sql(table_dest_empty, dst_engine, if_exists='replace', index=False)
                    except Exception as e:
                        print(f"Error creating empty table {table_dest_empty}: {e}")
            log.status = "SUCCESS"
            
            base_msg = f"Sin registros {'nuevos ' if not full_refresh else ''}en {sel.table_name}"
            if log.message and "Fórmulas actualizadas" in log.message:
                log.message = f"{base_msg} {log.message}"
            else:
                log.message = base_msg
                
            log.records_processed = 0
            db.commit()
            return {"status": "OK", "message": log.message, "records": 0}

        # Insertar en BD intermedia (append o replace)
        table_dest = sel.table_name.lower().replace(" ", "_")
        
        # ── Sincronizar esquema o limpiar tabla compartida ──
        from sqlalchemy import inspect
        from sqlalchemy import text
        inspector = inspect(dst_engine)
        
        if inspector.has_table(table_dest):
            if full_refresh:
                # Si es full refresh, borramos selectivamente los datos de la empresa (sin destruir la tabla)
                try:
                    with dst_engine.begin() as conn:
                        conn.execute(text(f'DELETE FROM "{table_dest}" WHERE company_id = {company_id}'))
                except Exception as e:
                    print(f"Error borrando datos previos de {company_id} en {table_dest}: {e}")

            # Sincronizar esquema SIEMPRE (agregar columnas nuevas como las calculadas)
            existing_cols = [c['name'] for c in inspector.get_columns(table_dest)]
            with dst_engine.begin() as conn:
                for col_name in df.columns:
                    if col_name not in existing_cols:
                        try:
                            safe_col = col_name.replace('"', '""')
                            conn.execute(text(f'ALTER TABLE "{table_dest}" ADD COLUMN "{safe_col}" TEXT'))
                        except Exception as e:
                            print(f"Error adding column {col_name}: {e}")

        # ── Limpiar Datos para PostgreSQL ──
        # Convertir strings vacíos a None para evitar errores de cast en columnas numéricas
        # (psycopg2.errors.InvalidTextRepresentation: invalid input syntax for type double precision: "")
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].apply(lambda x: None if x == "" else x)

        # Escribir en destino (siempre append ya que borramos previamente)
        df.to_sql(table_dest, dst_engine, if_exists='append', index=False, chunksize=1000)

        # Actualizar control incremental
        if sel.control_column and rows_count > 0:
            try:
                cols = [c.strip() for c in sel.control_column.split(',')]
                if len(cols) > 1:
                    # Sort by columns to find the "max" row based on the composite key order
                    # Need to ensure columns exist in DF
                    valid_cols = [c for c in cols if c in df.columns]
                    if len(valid_cols) == len(cols):
                        last_row = df.sort_values(by=cols).iloc[-1]
                        last_val = ", ".join([str(last_row[c]) for c in cols])
                    else:
                        last_val = None # Error logic
                else:
                    last_val = str(df[sel.control_column].max())
            except Exception as e:
                print(f"Error calculando incremental: {e}")
                last_val = None
            except:
                last_val = str(df.iloc[-1][sel.control_column])
                
            if not control:
                control = MigrationControl(
                    company_id=company_id,
                    source_table=sel.table_name,
                    control_column=sel.control_column
                )
                db.add(control)
            control.last_migrated_value = last_val
            control.total_migrated = (control.total_migrated or 0) + rows_count
            control.last_run_at = datetime.now()
            control.last_run_status = "OK"

        log.status = "SUCCESS"
        success_part = f"Migrados {rows_count} registros de {sel.table_name} a tabla '{table_dest}'"
        if hasattr(log, "message") and log.message:
            log.message += f" | {success_part}"
        else:
            log.message = success_part
        
        log.records_processed = rows_count
        db.commit()
        return {"status": "OK", "message": log.message, "records": rows_count}

    except Exception as e:
        import traceback
        log.status = "ERROR"
        log.message = f"[{sel.table_name}] {str(e)}"
        log.details = traceback.format_exc()
        db.commit()
        return {"status": "ERROR", "message": log.message}


@router.post("/run-incremental/{company_id}/{table_selection_id}")
def trigger_incremental_etl(company_id: int, table_selection_id: int,
                             db: Session = Depends(get_dest_db)):
    """Ejecuta ETL incremental para una tabla específica con sus filtros configurados"""
    result = run_incremental_etl(company_id, table_selection_id, db)
    if result["status"] == "ERROR":
        raise HTTPException(status_code=500, detail=result["message"])
    return result


@router.post("/run-etl/")
def trigger_etl(
    company_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    full_refresh: bool = False,
    db: Session = Depends(get_dest_db)
):
    """Runs the ETL process synchronously so the frontend knows when it truly finishes."""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    sd_str = str(start_date) if start_date else None
    ed_str = str(end_date) if end_date else None
    
    # Run synchronously so the frontend progress bar reflects the real status
    result = run_etl_job_sync(company_id, sd_str, ed_str, full_refresh, db)
    return result


def run_etl_job_sync(company_id: int, start_date: str, end_date: str, full_refresh: bool, db: Session):
    """Synchronous ETL: runs all extractions and returns the result to the caller."""
    company = db.query(Company).filter(Company.id == company_id).first()
    source_conn = db.query(SourceConnection).filter(SourceConnection.company_id == company_id).first()
    dest_conn = db.query(DestinationConnection).filter(DestinationConnection.company_id == company_id).first()

    if not company or not source_conn or not dest_conn:
        log = IntegLog(company_id=company_id, process_name="ETL Manual", status="ERROR",
                       message="Configuración incompleta: Faltan conexiones origen o destino")
        db.add(log); db.commit()
        raise HTTPException(status_code=400, detail="Configuración incompleta: Faltan conexiones origen o destino")

    refresh_msg = " (FULL REFRESH)" if full_refresh else ""
    log = IntegLog(company_id=company_id, process_name="ETL Manual", status="RUNNING",
                   message=f"Iniciando ETL{refresh_msg} para empresa {company.name}")
    db.add(log); db.commit()

    try:
        selections = db.query(TableSelection).filter(
            TableSelection.company_id == company_id,
            TableSelection.is_selected == True
        ).order_by(TableSelection.extraction_order).all()

        if not selections:
            raise Exception("No hay tablas seleccionadas para extraer")

        total_records = 0
        tables_processed = []
        for sel in selections:
            result = run_incremental_etl(company_id, sel.id, db, start_date, end_date, full_refresh=full_refresh)
            recs = result.get("records", 0)
            total_records += recs
            tables_processed.append({"table": sel.table_name, "records": recs})

        log.status = "SUCCESS"
        log.message = f"ETL finalizado. {total_records} registros extraídos de {len(selections)} tablas."
        log.records_processed = total_records
        db.commit()

        return {
            "message": f"ETL completado: {total_records} registros extraídos de {len(selections)} tablas",
            "records": total_records,
            "tables": len(selections),
            "details": tables_processed,
            "status": "OK"
        }
    except Exception as e:
        log.status = "ERROR"
        log.message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))


def run_etl_job(company_id: int, start_date: str, end_date: str, full_refresh: bool, db: Session):
    company = db.query(Company).filter(Company.id == company_id).first()
    source_conn = db.query(SourceConnection).filter(SourceConnection.company_id == company_id).first()
    dest_conn = db.query(DestinationConnection).filter(DestinationConnection.company_id == company_id).first()

    if not company or not source_conn or not dest_conn:
        log = IntegLog(company_id=company_id, process_name="ETL Manual", status="ERROR",
                       message="Configuración incompleta: Faltan conexiones origen o destino")
        db.add(log); db.commit(); return

    refresh_msg = " (FULL REFRESH)" if full_refresh else ""
    log = IntegLog(company_id=company_id, process_name="ETL Manual", status="RUNNING",
                   message=f"Iniciando ETL{refresh_msg} para empresa {company.name} ({start_date} a {end_date})")
    db.add(log); db.commit()

    try:
        selections = db.query(TableSelection).filter(
            TableSelection.company_id == company_id,
            TableSelection.is_selected == True
        ).order_by(TableSelection.extraction_order).all()

        if not selections:
            raise Exception("No hay tablas seleccionadas para extraer")

        total_records = 0
        for sel in selections:
            result = run_incremental_etl(company_id, sel.id, db, start_date, end_date, full_refresh=full_refresh)
            total_records += result.get("records", 0)

        log.status = "SUCCESS"
        log.message = f"ETL finalizado. {total_records} registros migrados de {len(selections)} tablas."
        log.records_processed = total_records
    except Exception as e:
        log.status = "ERROR"
        log.message = str(e)
    finally:
        db.commit()


# ─── Generación de Asientos Contables ────────────────────────────────────────

@router.post("/generate-asientos")
def generate_asientos_contables(
    body: dict,
    db: Session = Depends(get_dest_db)
):
    """
    Genera asientos contables en formato Contasis a partir de la configuración
    de mapeo de una subcategoría y los datos en la BD intermedia.
    """
    subcategoria_id = body.get("subcategoria_id")
    periodo = body.get("periodo") or str(datetime.now().year)
    mes = body.get("mes") or f"{datetime.now().month:02d}"

    sub = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.id == subcategoria_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subcategoría no encontrada")

    lineas = db.query(MapeoLineaAsiento).filter(
        MapeoLineaAsiento.subcategoria_id == subcategoria_id,
        MapeoLineaAsiento.is_active == True
    ).order_by(MapeoLineaAsiento.orden).all()

    if not lineas:
        raise HTTPException(status_code=400, detail="No hay líneas de asiento configuradas")

    if not sub.tabla_origen:
        raise HTTPException(status_code=400, detail="La subcategoría no tiene tabla origen configurada")

    # Construir filtros opcionales para la query
    filters = body.get("filters", [])
    query_str = f'SELECT * FROM "{sub.tabla_origen.lower()}"'
    query_params = {}
    
    if filters:
        where_parts = []
        for i, f in enumerate(filters):
            col = f.get("column", "")
            op = f.get("operator", "=").upper()
            val = f.get("value", "")
            val2 = f.get("value2", "")
            
            if not col:
                continue
            
            col_quoted = f'"{col}"'
            
            if op == "IS NULL":
                where_parts.append(f"{col_quoted} IS NULL")
            elif op == "IS NOT NULL":
                where_parts.append(f"{col_quoted} IS NOT NULL")
            elif op == "BETWEEN" and val and val2:
                where_parts.append(f"{col_quoted} BETWEEN :p{i}a AND :p{i}b")
                query_params[f"p{i}a"] = val
                query_params[f"p{i}b"] = val2
            elif op == "IN" and val:
                vals = [v.strip() for v in val.split(",")]
                placeholders = ", ".join([f":p{i}_{j}" for j in range(len(vals))])
                where_parts.append(f"{col_quoted} IN ({placeholders})")
                for j, v in enumerate(vals):
                    query_params[f"p{i}_{j}"] = v
            elif op == "LIKE" and val:
                where_parts.append(f"{col_quoted} LIKE :p{i}")
                query_params[f"p{i}"] = val
            elif val:
                where_parts.append(f"{col_quoted} {op} :p{i}")
                query_params[f"p{i}"] = val
        
        if where_parts:
            query_str += " WHERE " + " AND ".join(where_parts)

    # Obtener datos de la BD intermedia
    from backend.app.core.database import dest_engine
    try:
        with dest_engine.connect() as conn:
            result = conn.execute(text(query_str), query_params)
            rows = result.fetchall()
            columns = list(result.keys())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al leer tabla origen '{sub.tabla_origen}': {str(e)}")

    if not rows:
        return {"message": f"Sin datos en la tabla '{sub.tabla_origen}'", "generated": 0}

    # Obtener company_id de la categoría
    cat = sub.categoria
    company_id = cat.company_id

    # Generar lote único
    lote_id = str(uuid.uuid4())[:8].upper()

    # Número de asiento (correlativo)
    last_asiento = db.query(AsientoContableGenerado).filter(
        AsientoContableGenerado.company_id == company_id,
        AsientoContableGenerado.cper == periodo,
        AsientoContableGenerado.cmes == mes
    ).count()
    nasiento_base = last_asiento + 1

    generated = 0
    asiento_num = nasiento_base

    for row_idx, row in enumerate(rows):
        row_dict = dict(zip(columns, row))

        # Generar una línea de asiento por cada línea configurada
        for nidlin, linea in enumerate(lineas, start=1):
            # Calcular importe
            importe = 0.0
            if linea.columna_importe and linea.columna_importe in row_dict:
                try:
                    importe = float(row_dict[linea.columna_importe] or 0)
                except:
                    importe = 0.0

            # Cuenta contable
            if linea.cuenta_tipo == "FIJA":
                ccodcue = linea.cuenta_fija
            else:
                ccodcue = str(row_dict.get(linea.cuenta_columna, "")).strip() if linea.cuenta_columna else None

            # Tipo de cambio
            ntc = 1.0
            if linea.col_tc and linea.col_tc in row_dict:
                try:
                    ntc = float(row_dict[linea.col_tc] or 1)
                except:
                    ntc = 1.0

            # Moneda
            if linea.moneda == "COLUMNA" and linea.moneda_columna:
                moneda_val = str(row_dict.get(linea.moneda_columna, "SOLES"))
                ccodmon = "14" if "SOL" in moneda_val.upper() else "02"
            else:
                ccodmon = "14" if linea.moneda == "SOLES" else "02"

            # Debe / Haber
            ndebe = importe if linea.lado == "DEBE" else 0.0
            nhaber = importe if linea.lado == "HABER" else 0.0
            ndebes = ndebe if ccodmon == "14" else ndebe * ntc
            nhabers = nhaber if ccodmon == "14" else nhaber * ntc
            ndebed = ndebe if ccodmon == "02" else ndebe / ntc if ntc else 0
            nhaberd = nhaber if ccodmon == "02" else nhaber / ntc if ntc else 0

            # Glosa
            glosa = linea.glosa_template or ""
            for col_name, col_val in row_dict.items():
                glosa = glosa.replace(f"{{{col_name}}}", str(col_val or ""))
            glosa = glosa.replace("{nidlin}", str(nidlin))

            # Tipo movimiento
            if linea.tipo_mov_tipo == "FIJO":
                tipo_mov = linea.tipo_mov_fijo
            else:
                tipo_mov = str(row_dict.get(linea.tipo_mov_columna, "")) if linea.tipo_mov_columna else None

            # Centro de costo
            if linea.centro_costo_columna:
                ccodcos = str(row_dict.get(linea.centro_costo_columna, ""))
            elif linea.centro_costo_id:
                from backend.app.models.models import CatCentroCosto
                cc = db.query(CatCentroCosto).filter(CatCentroCosto.id == linea.centro_costo_id).first()
                ccodcos = cc.codigo if cc else None
            else:
                ccodcos = None

            # Cuenta presupuestal
            if linea.cuenta_presupuesto_columna:
                ccodpresu = str(row_dict.get(linea.cuenta_presupuesto_columna, ""))
            elif linea.cuenta_presupuesto_id:
                from backend.app.models.models import CatCuentaPresupuesto
                cp = db.query(CatCuentaPresupuesto).filter(CatCuentaPresupuesto.id == linea.cuenta_presupuesto_id).first()
                ccodpresu = cp.codigo if cp else None
            else:
                ccodpresu = None

            # Campos de referencia del asiento
            def get_col(col_attr):
                col_name = getattr(linea, col_attr)
                if col_name and col_name in row_dict:
                    return str(row_dict[col_name] or "")
                return None

            asiento = AsientoContableGenerado(
                company_id=company_id,
                subcategoria_id=subcategoria_id,
                cper=get_col("col_periodo") or periodo,
                cmes=get_col("col_mes") or mes,
                ccodori=get_col("ccodori") or sub.codigo_origen or "001",
                nasiento=asiento_num,
                nidlin=nidlin,
                ntc=ntc,
                ccodcue=ccodcue,
                ndebe=round(ndebe, 4),
                nhaber=round(nhaber, 4),
                cglosa=glosa[:500] if glosa else None,
                ndebes=round(ndebes, 4),
                nhabers=round(nhabers, 4),
                ndebed=round(ndebed, 4),
                nhaberd=round(nhaberd, 4),
                ccoddoc=get_col("col_tipo_doc") or tipo_mov,
                cserie=get_col("col_serie"),
                cnumero=get_col("col_numero"),
                ffechadoc=get_col("col_fecha"),
                ccodruc=get_col("col_ruc"),
                ccodenti=get_col("col_cod_entidad"),
                nbase1=float(row_dict.get(linea.col_base_imponible, 0) or 0) if linea.col_base_imponible else 0,
                nigv1=float(row_dict.get(linea.col_igv, 0) or 0) if linea.col_igv else 0,
                ntot=round(ndebe + nhaber, 4),
                nbase1s=float(row_dict.get(linea.col_base_imponible, 0) or 0) if linea.col_base_imponible and ccodmon == "14" else 0,
                nigv1s=float(row_dict.get(linea.col_igv, 0) or 0) if linea.col_igv and ccodmon == "14" else 0,
                ntots=round(ndebes + nhabers, 4),
                nbase1d=float(row_dict.get(linea.col_base_imponible, 0) or 0) if linea.col_base_imponible and ccodmon == "02" else 0,
                nigv1d=float(row_dict.get(linea.col_igv, 0) or 0) if linea.col_igv and ccodmon == "02" else 0,
                ntotd=round(ndebed + nhaberd, 4),
                ccodcos=ccodcos,
                ccodpresu=ccodpresu,
                ccodmon=ccodmon,
                cregis="V" if "VENTA" in (sub.nombre or "").upper() else None,
                ncomp=row_idx + 1,
                estado="PENDIENTE",
                lote_id=lote_id
            )
            db.add(asiento)
            generated += 1

        asiento_num += 1

    db.commit()
    return {
        "message": f"Se generaron {generated} líneas de asiento en {len(rows)} asientos",
        "lote_id": lote_id,
        "generated": generated,
        "asientos": len(rows)
    }


# ─── Proceso Completo (ETL + Generar + Migrar) ────────────────────────────────

@router.post("/run-full/{company_id}")
def run_full_etl(company_id: int, body: dict = {}, db: Session = Depends(get_dest_db)):
    """
    Ejecuta el flujo completo de migración:
    1. ETL incremental: extrae datos de SQL Server → migconta_db
    2. Generación: crea asientos en cf_diariol (staging)
    3. Migración: copia cf_diariol staging → Contasis final
    """
    from backend.app.models.models import MapeoCategoria, MapeoSubcategoria, FinalDestConnection
    from backend.app.api.endpoints.mapeo import generate_to_cf_diariol, migrate_to_final
    from datetime import datetime

    results = {
        "paso1_etl": {"status": "SKIP", "message": "No ejecutado", "records": 0},
        "paso2_generar": {"status": "SKIP", "message": "No ejecutado", "generated": 0},
        "paso3_migrar": {"status": "SKIP", "message": "No ejecutado", "migrated": 0},
    }

    # ── Paso 1: ETL incremental ──
    try:
        selections = db.query(TableSelection).filter(
            TableSelection.company_id == company_id,
            TableSelection.is_selected == True
        ).order_by(TableSelection.extraction_order).all()

        start_date = body.get("start_date")
        end_date = body.get("end_date")
        full_refresh = body.get("full_refresh", False)
        clear_prev = body.get("clear_previous", False)
        subcats_filter = body.get("subcategorias", [])

        # Identificar qué tablas origen necesitan extraerse basándonos en las subcategorías seleccionadas
        tablas_origen_permitidas = []
        if subcats_filter:
            subcats = db.query(MapeoSubcategoria).filter(
                MapeoSubcategoria.id.in_(subcats_filter)
            ).all()
            tablas_origen_permitidas = [s.tabla_origen for s in subcats if s.tabla_origen]

        total_etl = 0
        for sel in selections:
            if subcats_filter:
                sel_table_dest = sel.table_name.lower().replace(" ", "_")
                # Solo extraemos si la tabla coincide con alguna de las requeridas por los filtros
                if sel.table_name not in tablas_origen_permitidas and sel_table_dest not in tablas_origen_permitidas:
                    continue

            result = run_incremental_etl(company_id, sel.id, db, start_date, end_date, full_refresh=full_refresh)
            total_etl += result.get("records", 0)

        results["paso1_etl"] = {
            "status": "OK",
            "message": f"ETL completado: {total_etl} registros de {len(selections)} tablas",
            "records": total_etl
        }
    except Exception as e:
        results["paso1_etl"] = {"status": "ERROR", "message": str(e), "records": 0}

    # ── Paso 2: Generar asientos en cf_diariol ──
    try:
        categorias = db.query(MapeoCategoria).filter(
            MapeoCategoria.company_id == company_id,
            MapeoCategoria.is_active == True
        ).all()

        total_gen = 0
        lotes = []
        clear_prev = body.get("clear_previous", False)
        for cat in categorias:
            for sub in cat.subcategorias:
                if not sub.is_active or not sub.tabla_origen:
                    continue
                if subcats_filter and sub.id not in subcats_filter:
                    continue
                try:
                    gen_result = generate_to_cf_diariol(
                        {
                            "subcategoria_id": sub.id, 
                            "clear_previous": clear_prev
                        },
                        db
                    )
                    total_gen += gen_result.get("generated", 0)
                    if gen_result.get("lote_id"):
                        lotes.append(gen_result["lote_id"])
                except Exception as sub_e:
                    pass  # Continuar con las demás subcategorías

        results["paso2_generar"] = {
            "status": "OK",
            "message": f"Generados {total_gen} líneas en cf_diariol",
            "generated": total_gen,
            "lotes": lotes
        }
    except Exception as e:
        results["paso2_generar"] = {"status": "ERROR", "message": str(e), "generated": 0}

    # ── Paso 3: Migrar al destino final ──
    try:
        final_conn = db.query(FinalDestConnection).filter(
            FinalDestConnection.company_id == company_id,
            FinalDestConnection.is_active == True
        ).first()

        if not final_conn:
            results["paso3_migrar"] = {
                "status": "SKIP",
                "message": "No hay conexión destino final configurada",
                "migrated": 0
            }
        else:
            if subcats_filter:
                migrated_total = 0
                msg_total = ""
                for sid in subcats_filter:
                    mig_result = migrate_to_final(company_id=company_id, lote_id=None, allow_overwrite=False, subcategoria_id=sid, db=db)
                    migrated_total += mig_result.get("migrated_lineas", 0)
                    if mig_result.get("message"): msg_total += mig_result["message"] + ". "
                results["paso3_migrar"] = {
                    "status": "OK",
                    "message": msg_total.strip() or f"Migrados {migrated_total} registros de subcategorías filtradas",
                    "migrated": migrated_total
                }
            else:
                mig_result = migrate_to_final(company_id=company_id, lote_id=None, allow_overwrite=False, subcategoria_id=None, db=db)
                results["paso3_migrar"] = {
                    "status": "OK",
                    "message": mig_result.get("message", ""),
                    "migrated": mig_result.get("migrated_lineas", 0)
                }
    except Exception as e:
        failed_rows = []
        err_msg = str(e)
        if isinstance(e, HTTPException) and hasattr(e, "detail") and isinstance(e.detail, dict):
            failed_rows = e.detail.get("failed_rows", [])
            err_msg = e.detail.get("message", str(e))
        
        results["paso3_migrar"] = {"status": "ERROR", "message": err_msg, "migrated": 0, "failed_rows": failed_rows}

    overall_status = "OK" if all(
        r["status"] in ("OK", "SKIP") for r in results.values()
    ) else "PARTIAL"

    return {
        "status": overall_status,
        "company_id": company_id,
        "resultados": results
    }
