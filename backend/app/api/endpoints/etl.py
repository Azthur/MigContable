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
    ComputedColumnRule, AsientoCorrelativo, EtlRealtimeLog
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

def __apply_computed_rules(df, computed_rules, db, company_id, table_name, db_engine=None):
    df_cols_lower = {str(c).lower(): str(c) for c in df.columns}
    # 1. Pre-escanear e inicializar columnas con su valor por defecto (o vacío)
    col_defaults = {}
    for rule in computed_rules:
        r_lower = rule.new_column_name.lower()
        actual_col = df_cols_lower.get(r_lower, rule.new_column_name)
        if actual_col not in col_defaults:
            col_defaults[actual_col] = rule.default_value if rule.default_value else ""
            
    for col, default in col_defaults.items():
        df[col] = default

    # 2. Ejecutar reglas de manera estrictamente secuencial de arriba hacia abajo
    for rule in computed_rules:
        r_lower = rule.new_column_name.lower()
        new_col = df_cols_lower.get(r_lower, rule.new_column_name)
        default = col_defaults.get(new_col, "")
        
        try:
            import re
            val_upper = rule.condition_value.strip().upper()
            func_match = re.match(r'^([\w\.]+)\s*\(', val_upper)
            
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
                        
            elif func_match and func_match.group(1) in [
                "CONCAT", "CONCAT_EXACTO", "LEFT", "RIGHT", "SI.CONJUNTO", "SI", "IF",
                "BUSCARX", "BUSCARX_EXT", "BUSCARX_LOCAL", "SUMA", "RESTA", "MULTIPLICA", "DIVIDE", "REDONDEAR", "ABS",
                "LARGO", "ESPACIOS", "MAYUSC", "REPETIR", "TEXTO", "AÑO", "MES", "Y", "O", "CHR", "CARACTER", "SUMAR.SI.CONJUNTO",
                "ENCONTRAR", "EXTRAER"
            ]:
                from backend.app.core.formula_parser import evaluate_formula_on_df
                df[new_col] = evaluate_formula_on_df(
                    df=df, formula_str=rule.condition_value,
                    db=db, company_id=company_id, default=default if default else "",
                    db_engine=db_engine
                )
            else:
                actual_src = __get_col_simple(rule.source_column, df)
                if actual_src:
                    mask = df[actual_src].astype(str).str.strip().str.upper() == val_upper
                    
                    res_val = rule.result_value
                    res_upper = res_val.strip().upper() if res_val else ""
                    func_match_res = re.match(r'^([\w\.]+)\s*\(', res_upper)
                    
                    if func_match_res and func_match_res.group(1) in [
                        "CONCAT", "CONCAT_EXACTO", "LEFT", "RIGHT", "SI.CONJUNTO", "SI", "IF",
                        "BUSCARX", "BUSCARX_EXT", "BUSCARX_LOCAL", "SUMA", "RESTA", "MULTIPLICA", "DIVIDE", "REDONDEAR", "ABS",
                        "LARGO", "ESPACIOS", "MAYUSC", "REPETIR", "TEXTO", "AÑO", "MES", "Y", "O", "CHR", "CARACTER", "SUMAR.SI.CONJUNTO",
                        "ENCONTRAR", "EXTRAER"
                    ]:
                        from backend.app.core.formula_parser import evaluate_formula_on_df
                        eval_res = evaluate_formula_on_df(df=df, formula_str=res_val, db=db, company_id=company_id, default="", db_engine=db_engine)
                        df.loc[mask, new_col] = eval_res[mask]
                    else:
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
                __apply_computed_rules(df, computed_rules, db, company_id, sel.table_name, db_engine=dst_engine)

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
                    __apply_computed_rules(df_pending, computed_rules, db, company_id, sel.table_name, db_engine=dst_engine)
                    
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
            return {"status": "OK", "message": log.message, "records": 0, "extracted_rows": []}

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

        # Crear índices para acelerar consultas posteriores
        try:
            with dst_engine.connect() as conn:
                conn.execute(text(f'CREATE INDEX IF NOT EXISTS "idx_{table_dest.lower()}_company_id" ON "{table_dest}" (company_id)'))
                if "idcontrol" in df.columns:
                    conn.execute(text(f'CREATE INDEX IF NOT EXISTS "idx_{table_dest.lower()}_idcontrol" ON "{table_dest}" (idcontrol)'))
                conn.commit()
        except Exception as idx_err:
            print(f"Error creando indices en {table_dest}: {idx_err}")

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
        
        # Sanitize for JSON safety (converting NaN/NaT to None)
        df_clean = df.copy()
        for col in df_clean.columns:
            try:
                if df_clean[col].dtype == 'object':
                    df_clean[col] = df_clean[col].apply(lambda x: None if pd.isna(x) else x)
                elif pd.api.types.is_numeric_dtype(df_clean[col]):
                    df_clean[col] = df_clean[col].apply(lambda x: None if pd.isna(x) else x)
                else:
                    df_clean[col] = df_clean[col].apply(lambda x: None if pd.isna(x) else str(x))
            except:
                pass
        extracted_rows_dict = df_clean.to_dict(orient="records")
        
        return {"status": "OK", "message": log.message, "records": rows_count, "extracted_rows": extracted_rows_dict}

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
    from backend.app.core.database import dest_engine
    from sqlalchemy import inspect
    try:
        insp = inspect(dest_engine)
        actual_cols = [c['name'] for c in insp.get_columns(sub.tabla_origen.lower().replace(" ", "_"))]
    except Exception as e:
        print(f"Error inspecting columns for table {sub.tabla_origen}: {e}")
        actual_cols = []
    cols_map = {c.lower(): c for c in actual_cols}

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
            
            col_actual = cols_map.get(col.lower(), col)
            col_quoted = f'"{col_actual}"'
            
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
                            "clear_previous": clear_prev,
                            "is_realtime": body.get("is_realtime", True)
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


# ─── ETL en Tiempo Real & Control de Correlativos ─────────────────────────────

def format_source_row_log(row):
    import pandas as pd
    # Try to find standard columns like coddoc, cserie, cnumero, nrodoc, ffechadoc, etc.
    cols = {str(k).lower(): str(k) for k in row.keys()}
    
    # Extract values
    doc_type = row.get(cols.get("coddoc")) or row.get(cols.get("ccoddoc")) or ""
    serie = row.get(cols.get("cserie")) or row.get(cols.get("serie")) or ""
    numero = row.get(cols.get("cnumero")) or row.get(cols.get("nrodoc")) or row.get(cols.get("numero")) or ""
    fecha = row.get(cols.get("ffechadoc")) or row.get(cols.get("fchdoc")) or row.get(cols.get("fecha")) or ""
    ruc = row.get(cols.get("ccodruc")) or row.get(cols.get("ruc")) or ""
    total = row.get(cols.get("ntot")) or row.get(cols.get("total")) or row.get(cols.get("impnet")) or ""
    
    parts = []
    if doc_type: parts.append(f"Doc: {doc_type}")
    if serie or numero: parts.append(f"Num: {serie}-{numero}")
    if fecha: parts.append(f"Fecha: {fecha}")
    if ruc: parts.append(f"RUC: {ruc}")
    if total: parts.append(f"Monto: {total}")
    
    if not parts:
        # Fallback to listing first 5 columns and values
        p_list = []
        for k, v in list(row.items())[:5]:
            if v is not None and str(v).strip() != "":
                p_list.append(f"{k}: {v}")
        return ", ".join(p_list)
        
    return " | ".join(parts)


def run_realtime_etl(company_id: Optional[int], db: Session, subcategorias: Optional[List[int]] = None):
    """
    Ejecuta el flujo completo de migración en tiempo real (Steps 1 + 2 + 3):
    1. ETL incremental (extrae de SQL Server a migconta_db)
    2. Genera asientos en cf_diariol (staging) sin borrar anteriores (clear_previous=False)
    3. Migra a Contasis (copia cf_diariol staging a Contasis final)
    Guarda los resultados estructurados en etl_realtime_logs.
    """
    from backend.app.models.models import Company, TableSelection, MapeoCategoria, FinalDestConnection, EtlRealtimeLog, MapeoSubcategoria
    from backend.app.api.endpoints.mapeo import generate_to_cf_diariol, migrate_to_final
    from datetime import datetime
    import traceback

    # Map subcategory IDs to names
    subcat_map = {s.id: s.nombre for s in db.query(MapeoSubcategoria).all()}

    # Resolve subcategory names for this run
    subcat_names = "Todas"
    if subcategorias:
        subs = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.id.in_(subcategorias)).all()
        if subs:
            subcat_names = ", ".join([s.nombre for s in subs])

    # Resolve companies to process
    if company_id:
        companies = db.query(Company).filter(Company.id == company_id, Company.is_active == True).all()
    else:
        companies = db.query(Company).filter(Company.is_active == True).all()

    overall_results = []

    for comp in companies:
        records_extracted = 0
        records_generated = 0
        records_migrated = 0
        status = "SUCCESS"
        message_parts = []
        history_list = []

        try:
            # ── Paso 1: ETL Incremental ──
            selections = db.query(TableSelection).filter(
                TableSelection.company_id == comp.id,
                TableSelection.is_selected == True
            ).order_by(TableSelection.extraction_order).all()

            for sel in selections:
                try:
                    # Resolve table subcategory
                    sub_id_etl = None
                    sub_name_etl = "Extracción"

                    etl_res = run_incremental_etl(comp.id, sel.id, db, full_refresh=False)
                    if etl_res.get("status") == "ERROR":
                        status = "WARNING"
                        message_parts.append(f"Error ETL {sel.table_name}: {etl_res.get('message')}")
                        history_list.append({
                            "step": "ETL",
                            "table": sel.table_name,
                            "reference": "Extracción Incremental",
                            "status": "ERROR",
                            "column": None,
                            "error": etl_res.get("message"),
                            "subcategoria_id": sub_id_etl,
                            "subcategoria_nombre": sub_name_etl
                        })
                    else:
                        recs = etl_res.get("records", 0)
                        records_extracted += recs
                        history_list.append({
                            "step": "ETL",
                            "table": sel.table_name,
                            "reference": "Extracción Incremental",
                            "status": "SUCCESS",
                            "column": None,
                            "error": f"Extraídos {recs} registros nuevos delta.",
                            "subcategoria_id": sub_id_etl,
                            "subcategoria_nombre": sub_name_etl
                        })
                        
                        # Log row-by-row extracted records
                        extracted_rows = etl_res.get("extracted_rows", [])
                        for row in extracted_rows:
                            formatted_desc = format_source_row_log(row)
                            id_ctrl = row.get("idcontrol") or ""
                            history_list.append({
                                "step": "ETL",
                                "table": sel.table_name,
                                "reference": f"Fila ID: {id_ctrl}" if id_ctrl else "Fila Extraída",
                                "status": "SUCCESS",
                                "column": None,
                                "error": f"Registro extraído de origen: {formatted_desc}",
                                "subcategoria_id": sub_id_etl,
                                "subcategoria_nombre": sub_name_etl
                            })
                except Exception as ex_etl:
                    status = "WARNING"
                    message_parts.append(f"Fallo ETL {sel.table_name}: {str(ex_etl)}")
                    history_list.append({
                        "step": "ETL",
                        "table": sel.table_name,
                        "reference": "Extracción Incremental",
                        "status": "ERROR",
                        "column": None,
                        "error": str(ex_etl),
                        "subcategoria_id": None,
                        "subcategoria_nombre": "Extracción"
                    })

            # ── Paso 2: Generar asientos (Staging) ──
            # Se genera de manera incremental pero LIMPIANDO asientos previos no migrados (clear_previous=True)
            lote_id = None
            try:
                if subcategorias:
                    records_generated = 0
                    errors_list = []
                    for sub_id in subcategorias:
                        gen_body = {"company_id": comp.id, "subcategoria_id": sub_id, "clear_previous": True, "is_realtime": True}
                        gen_res = generate_to_cf_diariol(gen_body, db)
                        records_generated += gen_res.get("generated", 0)
                        if gen_res.get("lote_id"):
                            lote_id = gen_res.get("lote_id")
                        if gen_res.get("errors"):
                            errors_list.extend(gen_res["errors"])
                    gen_res = {"generated": records_generated, "lote_id": lote_id, "errors": errors_list}
                else:
                    gen_body = {"company_id": comp.id, "clear_previous": True, "is_realtime": True}
                    gen_res = generate_to_cf_diariol(gen_body, db)
                    records_generated = gen_res.get("generated", 0)
                    lote_id = gen_res.get("lote_id")

                # Log successful generations
                if lote_id and records_generated > 0:
                    from backend.app.models.models import CfDiariol
                    try:
                        gen_rows = db.query(CfDiariol).filter(
                            CfDiariol.company_id == comp.id,
                            CfDiariol.lote_id == lote_id
                        ).all()
                        for row in gen_rows:
                            history_list.append({
                                "step": "GENERATION",
                                "table": "cf_diariol (Staging)",
                                "reference": f"Asiento {row.nasiento} (Lín {row.nidlin})",
                                "status": "SUCCESS",
                                "column": None,
                                "error": f"Asiento generado localmente. Cuenta: {row.ccodcue} | Debe: {row.ndebe} | Haber: {row.nhaber} | Glosa: {row.cglosa}",
                                "subcategoria_id": row.subcategoria_id,
                                "subcategoria_nombre": subcat_map.get(row.subcategoria_id, "Generación")
                            })
                    except Exception as e_q:
                        print(f"Error querying staging details: {e_q}")

                if gen_res.get("errors"):
                    # Hay advertencias/errores de validación
                    status = "WARNING"
                    for err in gen_res["errors"]:
                        err_sub_id = err.get("subcategoria_id")
                        history_list.append({
                            "step": "VALIDATION",
                            "table": err.get("table", "cf_diariol"),
                            "reference": f"Asiento {err.get('nasiento')} (Lín {err.get('nidlin')})",
                            "status": "ERROR",
                            "column": err.get("field"),
                            "error": err.get("error"),
                            "subcategoria_id": err_sub_id,
                            "subcategoria_nombre": subcat_map.get(err_sub_id, "Validación")
                        })
            except Exception as ex_gen:
                status = "ERROR"
                message_parts.append(f"Fallo Generación: {str(ex_gen)}")
                history_list.append({
                    "step": "GENERATION",
                    "table": "Staging",
                    "reference": "Secuencia de Generación",
                    "status": "ERROR",
                    "column": None,
                    "error": str(ex_gen),
                    "subcategoria_id": None,
                    "subcategoria_nombre": "Generación"
                })

            # ── Paso 3: Migración Final a Contasis ──
            if status != "ERROR":
                try:
                    # check final connection
                    final_conn = db.query(FinalDestConnection).filter(
                        FinalDestConnection.company_id == comp.id,
                        FinalDestConnection.is_active == True
                    ).first()
                    
                    if not final_conn:
                        message_parts.append("No hay conexión destino final configurada (Tratado como SKIP)")
                        history_list.append({
                            "step": "MIGRATION",
                            "table": "Contasis Final",
                            "reference": "Conexión Contasis",
                            "status": "WARNING",
                            "column": None,
                            "error": "No hay conexión destino final configurada. Omitido.",
                            "subcategoria_id": None,
                            "subcategoria_nombre": "Migración"
                        })
                    else:
                        # Migrate only pending selected subcategories
                        if subcategorias:
                            records_migrated = 0
                            for sub_id in subcategorias:
                                try:
                                    mig_res = migrate_to_final(company_id=comp.id, subcategoria_id=sub_id, allow_overwrite=False, db=db)
                                    records_migrated += mig_res.get("migrated_lineas", 0)
                                except Exception as e_mig_sub:
                                    print(f"Error migrating subcategory {sub_id}: {e_mig_sub}")
                        else:
                            mig_res = migrate_to_final(company_id=comp.id, allow_overwrite=False, db=db)
                            records_migrated = mig_res.get("migrated_lineas", 0)

                        # Log successful migrations
                        if lote_id and records_migrated > 0:
                            from backend.app.models.models import CfDiariol
                            try:
                                mig_rows = db.query(CfDiariol).filter(
                                    CfDiariol.company_id == comp.id,
                                    CfDiariol.lote_id == lote_id,
                                    CfDiariol.estado == "MIGRADO"
                                ).all()
                                for row in mig_rows:
                                    history_list.append({
                                        "step": "MIGRATION",
                                        "table": "Contasis Final",
                                        "reference": f"Asiento {row.nasiento} (Lín {row.nidlin})",
                                        "status": "SUCCESS",
                                        "column": None,
                                        "error": f"Migrado correctamente a Contasis. Cuenta: {row.ccodcue} | Debe: {row.ndebe} | Haber: {row.nhaber} | Glosa: {row.cglosa}",
                                        "subcategoria_id": row.subcategoria_id,
                                        "subcategoria_nombre": subcat_map.get(row.subcategoria_id, "Migración")
                                    })
                            except Exception as e_m:
                                print(f"Error querying migrated details: {e_m}")

                except HTTPException as ex_http:
                    status = "WARNING"
                    detail = ex_http.detail
                    if isinstance(detail, dict):
                        message_parts.append(detail.get("message", "Error de migración"))
                        for row in detail.get("failed_rows", []):
                            row_sub_id = row.get("subcategoria_id")
                            history_list.append({
                                "step": "MIGRATION",
                                "table": "Contasis Final",
                                "reference": f"Asiento {row.get('seat')}",
                                "status": "ERROR",
                                "column": None,
                                "error": row.get("error"),
                                "subcategoria_id": row_sub_id,
                                "subcategoria_nombre": subcat_map.get(row_sub_id, "Migración")
                            })
                    else:
                        message_parts.append(str(detail))
                        history_list.append({
                            "step": "MIGRATION",
                            "table": "Contasis Final",
                            "reference": "Proceso de Migración",
                            "status": "ERROR",
                            "column": None,
                            "error": str(detail),
                            "subcategoria_id": None,
                            "subcategoria_nombre": "Migración"
                        })
                except Exception as ex_mig:
                    status = "WARNING"
                    message_parts.append(f"Fallo Migración: {str(ex_mig)}")
                    history_list.append({
                        "step": "MIGRATION",
                        "table": "Contasis Final",
                        "reference": "Proceso de Migración",
                        "status": "ERROR",
                        "column": None,
                        "error": str(ex_mig),
                        "subcategoria_id": None,
                        "subcategoria_nombre": "Migración"
                    })

        except Exception as e:
            status = "ERROR"
            message_parts.append(f"Fallo general del proceso: {str(e)}")
            history_list.append({
                "step": "SYSTEM",
                "table": "General",
                "reference": "Ciclo Principal",
                "status": "ERROR",
                "column": None,
                "error": str(e),
                "subcategoria_id": None,
                "subcategoria_nombre": "Sistema"
            })

        # Armar mensaje resumen
        if not message_parts:
            message = f"Ejecución exitosa: Extracción ({records_extracted}), Generación ({records_generated}), Migración ({records_migrated})"
        else:
            message = " | ".join(message_parts)

        # Crear y persistir log de tiempo real
        rt_log = EtlRealtimeLog(
            company_id=comp.id,
            status=status,
            message=message,
            records_extracted=records_extracted,
            records_generated=records_generated,
            records_migrated=records_migrated,
            errors=history_list,
            subcategorias=subcat_names
        )
        db.add(rt_log)
        db.commit()

        overall_results.append({
            "company_name": comp.name,
            "status": status,
            "extracted": records_extracted,
            "generated": records_generated,
            "migrated": records_migrated,
            "message": message,
            "errors_count": len(history_list)
        })

    return overall_results


# API Endpoints: Correlativos

@router.get("/correlativos")
def list_correlativos(
    company_id: Optional[int] = None,
    subcategoria_id: Optional[int] = None,
    periodo: Optional[str] = None,
    mes: Optional[str] = None,
    db: Session = Depends(get_dest_db)
):
    query = db.query(AsientoCorrelativo)
    if company_id:
        query = query.filter(AsientoCorrelativo.company_id == company_id)
    if subcategoria_id:
        query = query.filter(AsientoCorrelativo.subcategoria_id == subcategoria_id)
    if periodo:
        query = query.filter(AsientoCorrelativo.periodo == periodo)
    if mes:
        query = query.filter(AsientoCorrelativo.mes == mes)
    
    correlativos = query.order_by(AsientoCorrelativo.periodo.desc(), AsientoCorrelativo.mes.desc()).all()
    
    result = []
    for c in correlativos:
        from backend.app.models.models import MapeoSubcategoria
        sub = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.id == c.subcategoria_id).first()
        result.append({
            "id": c.id,
            "company_id": c.company_id,
            "company_name": c.company.name if c.company else f"Empresa {c.company_id}",
            "subcategoria_id": c.subcategoria_id,
            "subcategoria_name": sub.nombre if sub else f"Subcat {c.subcategoria_id}",
            "periodo": c.periodo,
            "mes": c.mes,
            "asiento_inicial": c.asiento_inicial,
            "asiento_actual": c.asiento_actual,
            "col_origen_periodo": sub.col_origen_periodo if sub else None,
            "col_origen_mes": sub.col_origen_mes if sub else None,
            "updated_at": str(c.updated_at) if c.updated_at else None
        })
    return result


@router.post("/correlativos")
def create_correlativo(body: dict, db: Session = Depends(get_dest_db)):
    company_id = body.get("company_id")
    subcategoria_id = body.get("subcategoria_id")
    periodo = str(body.get("periodo") or "").strip()
    mes = str(body.get("mes") or "").strip()
    asiento_inicial = int(body.get("asiento_inicial") or 1)
    
    col_origen_periodo = body.get("col_origen_periodo")
    col_origen_mes = body.get("col_origen_mes")
    bulk_year = body.get("bulk_year", False)
    
    if not company_id or not subcategoria_id or not periodo:
        raise HTTPException(status_code=400, detail="Faltan campos obligatorios")
        
    if not bulk_year and not mes:
        raise HTTPException(status_code=400, detail="Falta el campo obligatorio: mes")

    # Sync subcategory columns if specified
    from backend.app.models.models import MapeoSubcategoria
    sub = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.id == subcategoria_id).first()
    if sub:
        if col_origen_periodo is not None:
            sub.col_origen_periodo = col_origen_periodo
        if col_origen_mes is not None:
            sub.col_origen_mes = col_origen_mes

    if bulk_year:
        months = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]
        created_count = 0
        updated_count = 0
        last_id = None
        for m in months:
            existing = db.query(AsientoCorrelativo).filter(
                AsientoCorrelativo.company_id == company_id,
                AsientoCorrelativo.subcategoria_id == subcategoria_id,
                AsientoCorrelativo.periodo == periodo,
                AsientoCorrelativo.mes == m
            ).first()
            if existing:
                existing.asiento_inicial = asiento_inicial
                existing.asiento_actual = max(existing.asiento_actual, asiento_inicial - 1)
                updated_count += 1
                last_id = existing.id
            else:
                new_corr = AsientoCorrelativo(
                    company_id=company_id,
                    subcategoria_id=subcategoria_id,
                    periodo=periodo,
                    mes=m,
                    asiento_inicial=asiento_inicial,
                    asiento_actual=asiento_inicial - 1
                )
                db.add(new_corr)
                created_count += 1
        try:
            db.commit()
            if not last_id:
                # Get the id of one of the newly created elements to return
                last_corr = db.query(AsientoCorrelativo).filter(
                    AsientoCorrelativo.company_id == company_id,
                    AsientoCorrelativo.subcategoria_id == subcategoria_id,
                    AsientoCorrelativo.periodo == periodo
                ).first()
                last_id = last_corr.id if last_corr else 0
            return {
                "id": last_id,
                "message": f"Registro masivo completado. Creados: {created_count}, Actualizados: {updated_count}"
            }
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    else:
        if len(mes) == 1 and mes.isdigit():
            mes = f"0{mes}"

        existing = db.query(AsientoCorrelativo).filter(
            AsientoCorrelativo.company_id == company_id,
            AsientoCorrelativo.subcategoria_id == subcategoria_id,
            AsientoCorrelativo.periodo == periodo,
            AsientoCorrelativo.mes == mes
        ).first()

        if existing:
            existing.asiento_inicial = asiento_inicial
            existing.asiento_actual = max(existing.asiento_actual, asiento_inicial - 1)
            message = "Correlativo actualizado exitosamente (Upsert)"
        else:
            existing = AsientoCorrelativo(
                company_id=company_id,
                subcategoria_id=subcategoria_id,
                periodo=periodo,
                mes=mes,
                asiento_inicial=asiento_inicial,
                asiento_actual=asiento_inicial - 1
            )
            db.add(existing)
            message = "Correlativo creado exitosamente"

        try:
            db.commit()
            return {"id": existing.id, "message": message}
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))


@router.put("/correlativos/{id}")
def update_correlativo(id: int, body: dict, db: Session = Depends(get_dest_db)):
    corr = db.query(AsientoCorrelativo).filter(AsientoCorrelativo.id == id).first()
    if not corr:
        raise HTTPException(status_code=404, detail="Correlativo no encontrado")
        
    if "asiento_inicial" in body:
        corr.asiento_inicial = int(body["asiento_inicial"])
    if "asiento_actual" in body:
        corr.asiento_actual = int(body["asiento_actual"])
        
    col_origen_periodo = body.get("col_origen_periodo")
    col_origen_mes = body.get("col_origen_mes")
    
    # Sync subcategory columns if specified
    from backend.app.models.models import MapeoSubcategoria
    sub = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.id == corr.subcategoria_id).first()
    if sub:
        if col_origen_periodo is not None:
            sub.col_origen_periodo = col_origen_periodo
        if col_origen_mes is not None:
            sub.col_origen_mes = col_origen_mes
        
    try:
        db.commit()
        return {"id": corr.id, "message": "Correlativo actualizado exitosamente"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/correlativos/{id}")
def delete_correlativo(id: int, db: Session = Depends(get_dest_db)):
    corr = db.query(AsientoCorrelativo).filter(AsientoCorrelativo.id == id).first()
    if not corr:
        raise HTTPException(status_code=404, detail="Correlativo no encontrado")
        
    try:
        db.delete(corr)
        db.commit()
        return {"message": "Correlativo eliminado"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# API Endpoints: Realtime Logs

@router.get("/realtime-logs")
def list_realtime_logs(
    company_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_dest_db)
):
    query = db.query(EtlRealtimeLog)
    if company_id:
        query = query.filter(EtlRealtimeLog.company_id == company_id)
    if status:
        query = query.filter(EtlRealtimeLog.status == status)
        
    logs = query.order_by(EtlRealtimeLog.run_date.desc()).offset(skip).limit(limit).all()
    
    result = []
    for l in logs:
        result.append({
            "id": l.id,
            "company_id": l.company_id,
            "company_name": l.company.name if l.company else f"Empresa {l.company_id}",
            "run_date": str(l.run_date) if l.run_date else None,
            "status": l.status,
            "message": l.message,
            "records_extracted": l.records_extracted,
            "records_generated": l.records_generated,
            "records_migrated": l.records_migrated,
            "errors": l.errors,
            "subcategorias": l.subcategorias or "Todas"
        })
    return result


@router.get("/staging-summary")
def staging_summary(
    company_id: int,
    periodo: Optional[str] = None,
    mes: Optional[str] = None,
    db: Session = Depends(get_dest_db)
):
    """Resumen de staging agrupado por subcategoría con conteos por estado y desglose por período."""
    from backend.app.models.models import MapeoSubcategoria, MapeoCategoria
    from sqlalchemy import Table, MetaData, select, func, literal

    # Get all active subcategories for the company
    subcategorias = db.query(MapeoSubcategoria).join(
        MapeoCategoria, MapeoSubcategoria.categoria_id == MapeoCategoria.id
    ).filter(
        MapeoCategoria.company_id == company_id,
        MapeoSubcategoria.is_active == True
    ).all()

    result = []
    metadata = MetaData()

    for sub in subcategorias:
        # Determine staging/destination table name
        tabla_name = sub.tabla_destino_detalle or "cf_diariol"
        try:
            target_table = Table(tabla_name, metadata, autoload_with=db.bind)
        except Exception as e:
            print(f"Error loading staging table {tabla_name} for subcat {sub.id}: {e}")
            continue

        has_company = "company_id" in target_table.c
        has_subcat = "subcategoria_id" in target_table.c
        has_cper = "cper" in target_table.c
        has_cmes = "cmes" in target_table.c
        has_estado = "estado" in target_table.c

        # Select columns
        select_cols = [
            target_table.c.estado if has_estado else literal("1").label("estado"),
            func.count().label("total")
        ]
        group_cols = []
        if has_estado:
            group_cols.append(target_table.c.estado)

        if has_cper:
            select_cols.append(target_table.c.cper)
            group_cols.append(target_table.c.cper)
        if has_cmes:
            select_cols.append(target_table.c.cmes)
            group_cols.append(target_table.c.cmes)

        stmt = select(*select_cols)
        if has_company:
            stmt = stmt.where(target_table.c.company_id == company_id)
        if has_subcat:
            stmt = stmt.where(target_table.c.subcategoria_id == sub.id)

        # Filters from query parameters (only filter if columns exist in the table)
        if periodo and has_cper:
            stmt = stmt.where(target_table.c.cper == periodo)
        if mes and has_cmes:
            stmt = stmt.where(target_table.c.cmes == mes)

        if group_cols:
            stmt = stmt.group_by(*group_cols)

        try:
            rows = db.execute(stmt).fetchall()
        except Exception as e:
            print(f"Error executing staging query for subcat {sub.id} on table {tabla_name}: {e}")
            continue

        if not rows:
            continue

        sub_summary = {
            "subcategoria_id": sub.id,
            "subcategoria_nombre": sub.nombre,
            "pendiente": 0,
            "migrado": 0,
            "error": 0,
            "total": 0,
            "periodos_dict": {}
        }

        for row in rows:
            # Resolve estado
            raw_estado = getattr(row, "estado", "1")
            estado_str = str(raw_estado or "1").strip().upper()
            if estado_str in ("1", "PENDIENTE") or not estado_str:
                norm_estado = "PENDIENTE"
            elif estado_str == "MIGRADO":
                norm_estado = "MIGRADO"
            elif estado_str in ("0", "ERROR"):
                norm_estado = "ERROR"
            else:
                norm_estado = "PENDIENTE"

            # Resolve period/month
            r_cper = getattr(row, "cper", "GLOBAL") if has_cper else "GLOBAL"
            r_cmes = getattr(row, "cmes", "00") if has_cmes else "00"
            r_cper = str(r_cper or "GLOBAL")
            r_cmes = str(r_cmes or "00")

            count = getattr(row, "total", 0) or 0
            sub_summary["total"] += count
            if norm_estado == "MIGRADO":
                sub_summary["migrado"] += count
            elif norm_estado == "ERROR":
                sub_summary["error"] += count
            else:
                sub_summary["pendiente"] += count

            pkey = (r_cper, r_cmes)
            if pkey not in sub_summary["periodos_dict"]:
                sub_summary["periodos_dict"][pkey] = {
                    "periodo": r_cper,
                    "mes": r_cmes,
                    "pendiente": 0,
                    "migrado": 0,
                    "error": 0,
                    "total": 0
                }

            sub_summary["periodos_dict"][pkey]["total"] += count
            if norm_estado == "MIGRADO":
                sub_summary["periodos_dict"][pkey]["migrado"] += count
            elif norm_estado == "ERROR":
                sub_summary["periodos_dict"][pkey]["error"] += count
            else:
                sub_summary["periodos_dict"][pkey]["pendiente"] += count

        # Convert periodos_dict to list
        periodos_list = list(sub_summary["periodos_dict"].values())
        periodos_list.sort(key=lambda x: (x["periodo"], x["mes"]), reverse=True)
        sub_summary["periodos"] = periodos_list
        del sub_summary["periodos_dict"]
        result.append(sub_summary)

    return result


@router.post("/run-realtime")
def trigger_realtime_etl(body: dict, db: Session = Depends(get_dest_db)):
    company_id = body.get("company_id")
    subcategorias = body.get("subcategorias")
    try:
        results = run_realtime_etl(company_id, db, subcategorias=subcategorias)
        return {"message": "Proceso de ETL en tiempo real ejecutado exitosamente", "resultados": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def reprocess_staging_seat(company_id: int, nasiento: str, db: Session):
    from backend.app.models.models import CfDiariol, CfDiario, FinalDestConnection, MapeoSubcategoria
    from backend.app.services.connection_manager import ConnectionManager
    from sqlalchemy import Table, MetaData
    
    # 1. Fetch staging details for this seat
    details = db.query(CfDiariol).filter(
        CfDiariol.company_id == company_id,
        CfDiariol.nasiento == nasiento
    ).all()
    
    if not details:
        raise Exception(f"No se encontraron líneas de detalle en staging para el asiento {nasiento}")
        
    cper = details[0].cper
    cmes = details[0].cmes
    ccodori = details[0].ccodori
    subcategoria_id = details[0].subcategoria_id
    
    sub = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.id == subcategoria_id).first()
    if not sub:
        raise Exception("Subcategoría de mapeo no encontrada")
        
    # Fetch header if generate_headers is True
    header = None
    if sub.generate_headers is not False:
        header = db.query(CfDiario).filter(
            CfDiario.company_id == company_id,
            CfDiario.nasiento == nasiento,
            CfDiario.cper == cper,
            CfDiario.cmes == cmes
        ).first()
        if not header:
            raise Exception(f"No se encontró cabecera en staging para el asiento {nasiento}")
            
    # 2. Connect to Final Contasis DB
    final_conn = db.query(FinalDestConnection).filter(
        FinalDestConnection.company_id == company_id,
        FinalDestConnection.is_active == True
    ).first()
    if not final_conn:
        raise Exception("No hay conexión destino final configurada")
        
    conn_data = {
        "host": final_conn.host, "port": final_conn.port,
        "database_name": final_conn.database_name,
        "username": final_conn.username, "password": final_conn.password
    }
    final_engine = ConnectionManager.get_dest_engine(conn_data)
    
    metadata_final = MetaData()
    head_table_name = sub.tabla_destino_cabecera or "cf_diario"
    det_table_name = sub.tabla_destino_detalle or "cf_diariol"
    
    try: FinalHeadTable = Table(head_table_name, metadata_final, autoload_with=final_engine)
    except: FinalHeadTable = None
        
    try: FinalDetTable = Table(det_table_name, metadata_final, autoload_with=final_engine)
    except: FinalDetTable = None
    
    remote_head_cols = [c.name for c in FinalHeadTable.columns] if FinalHeadTable is not None else []
    remote_det_cols = [c.name for c in FinalDetTable.columns] if FinalDetTable is not None else []
    
    # 3. Perform Insert / Upsert into final Contasis
    with final_engine.begin() as final_db:
        # Clean existing seat in final DB first
        if FinalDetTable is not None:
            final_db.execute(FinalDetTable.delete().where(
                FinalDetTable.c.cper == cper,
                FinalDetTable.c.cmes == cmes,
                FinalDetTable.c.ccodori == ccodori,
                getattr(FinalDetTable.c, sub.col_destino_nasiento or "nasiento") == nasiento
            ))
        if FinalHeadTable is not None:
            final_db.execute(FinalHeadTable.delete().where(
                FinalHeadTable.c.cper == cper,
                FinalHeadTable.c.cmes == cmes,
                FinalHeadTable.c.ccodori == ccodori,
                getattr(FinalHeadTable.c, sub.col_destino_nasiento or "nasiento") == nasiento
            ))
            
        # Insert Header
        if header and FinalHeadTable is not None:
            h_dict = {c.name: getattr(header, c.name) for c in header.__table__.columns if c.name in remote_head_cols}
            final_db.execute(FinalHeadTable.insert(), [h_dict])
            
        # Insert Details
        if details and FinalDetTable is not None:
            d_list = []
            for d in details:
                insert_item = {}
                for c in d.__table__.columns:
                    k = c.name
                    v = getattr(d, k)
                    if k in remote_det_cols:
                        if v is not None and str(FinalDetTable.columns[k].type) in ['NUMERIC', 'FLOAT', 'INTEGER']:
                            try: insert_item[k] = float(v)
                            except: insert_item[k] = None
                        else:
                            insert_item[k] = v
                d_list.append(insert_item)
            final_db.execute(FinalDetTable.insert(), d_list)
            
    # 4. Mark staging status as MIGRADO
    for d in details:
        d.estado = "MIGRADO"
    if header:
        header.estado = "MIGRADO"
        
    db.commit()
    return f"Asiento {nasiento} remigrado exitosamente a Contasis"


@router.post("/reprocess-row")
def reprocess_row(body: dict, db: Session = Depends(get_dest_db)):
    company_id = body.get("company_id")
    step = body.get("step")
    table = body.get("table")
    reference = str(body.get("reference") or "")
    subcategoria_id = body.get("subcategoria_id")

    if not company_id:
        raise HTTPException(status_code=400, detail="Falta company_id")

    import re
    # Extract nasiento from reference if present (e.g. "Asiento 150 (Lín 1)" or "Asiento 150")
    m = re.search(r"Asiento\s+([A-Za-z0-9\-]+)", reference)
    nasiento = None
    if m:
        try:
            nasiento = int(m.group(1))
        except ValueError:
            nasiento = m.group(1)

    # Step A: Attempt direct staging re-migration if staging seat rows exist
    if nasiento:
        try:
            from backend.app.models.models import CfDiariol
            staging_exists = db.query(CfDiariol).filter(
                CfDiariol.company_id == company_id,
                CfDiariol.nasiento == nasiento
            ).first()
            if staging_exists:
                msg = reprocess_staging_seat(company_id, nasiento, db)
                return {"status": "SUCCESS", "message": msg}
        except Exception as ex_direct:
            db.rollback()
            print(f"Direct seat migration failed, falling back to subcategory generation: {ex_direct}")

    # Step B: Fallback - Regenerate and migrate the entire subcategory
    if not subcategoria_id and nasiento:
        from backend.app.models.models import CfDiariol
        try:
            row = db.query(CfDiariol).filter(
                CfDiariol.company_id == company_id,
                CfDiariol.nasiento == nasiento
            ).first()
            if row:
                subcategoria_id = row.subcategoria_id
        except Exception as ex_fallback_sub:
            db.rollback()
            print(f"Failed to find subcategory from seat: {ex_fallback_sub}")

    if not subcategoria_id:
        from backend.app.models.models import MapeoSubcategoria
        sub = db.query(MapeoSubcategoria).filter(
            MapeoSubcategoria.tabla_origen.ilike(table) | 
            MapeoSubcategoria.tabla_destino_detalle.ilike(table)
        ).first()
        if sub:
            subcategoria_id = sub.id

    if not subcategoria_id:
        raise HTTPException(
            status_code=400,
            detail="No se pudo determinar la subcategoría de mapeo para esta fila para reprocesar"
        )

    # Trigger generation & migration for this subcategory
    from backend.app.api.endpoints.mapeo import generate_to_cf_diariol, migrate_to_final
    try:
        # 1. Regenerate seats (clear_previous=True deletes prior failed staging seats)
        gen_res = generate_to_cf_diariol({
            "company_id": company_id,
            "subcategoria_id": subcategoria_id,
            "clear_previous": True,
            "is_realtime": True
        }, db)
        
        # 2. Migrate subcategory to final
        mig_res = migrate_to_final(
            company_id=company_id,
            subcategoria_id=subcategoria_id,
            allow_overwrite=True,
            db=db
        )
        
        return {
            "status": "SUCCESS",
            "message": f"Subcategoría reprocesada. Generado: {gen_res.get('generated')} líneas. Migrado: {mig_res.get('migrated_lineas')} líneas."
        }
    except Exception as ex_reproc:
        raise HTTPException(
            status_code=500,
            detail=f"Fallo al reprocesar subcategoría: {str(ex_reproc)}"
        )


@router.get("/raw-tables/{company_id}")
def list_raw_tables(company_id: int, db: Session = Depends(get_dest_db)):
    """Lista las tablas intermedias seleccionadas para una empresa"""
    selections = db.query(TableSelection).filter(
        TableSelection.company_id == company_id,
        TableSelection.is_selected == True
    ).order_by(TableSelection.extraction_order).all()
    return [{"id": s.id, "table_name": s.table_name, "table_dest": s.table_name.lower().replace(" ", "_")} for s in selections]


@router.get("/raw-table-data/{company_id}/{table_dest}")
def get_raw_table_data(
    company_id: int,
    table_dest: str,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: Session = Depends(get_dest_db)
):
    """Obtiene los datos de la tabla intermedia con paginación y búsqueda global"""
    from backend.app.core.database import dest_engine
    from sqlalchemy import inspect, text
    import numpy as np
    from decimal import Decimal
    from datetime import datetime as _dt, date as _date
    
    # Validar que el nombre de la tabla sea seguro
    insp = inspect(dest_engine)
    all_tables = [t.lower() for t in insp.get_table_names()]
    
    clean_table = table_dest.strip().lower()
    if clean_table not in all_tables:
        raise HTTPException(status_code=400, detail=f"Tabla '{table_dest}' no existe en la base de datos intermedia")
    
    # Obtener las columnas reales de la tabla
    columns = [c['name'] for c in insp.get_columns(clean_table)]
    
    # Construir query con filtros
    if "company_id" in columns:
        query_str = f'SELECT * FROM "{clean_table}" WHERE company_id = :cid'
        query_params = {"cid": company_id}
    else:
        query_str = f'SELECT * FROM "{clean_table}" WHERE 1=1'
        query_params = {}
    
    if search:
        # Búsqueda global en todas las columnas
        search_parts = []
        for idx, col in enumerate(columns):
            search_parts.append(f'CAST("{col}" AS TEXT) ILIKE :search_{idx}')
            query_params[f"search_{idx}"] = f"%{search}%"
        if search_parts:
            query_str += " AND (" + " OR ".join(search_parts) + ")"
            
    # Contar total
    count_query = f'SELECT COUNT(*) FROM ({query_str}) AS sub'
    try:
        with dest_engine.connect() as conn:
            total = conn.execute(text(count_query), query_params).scalar() or 0
    except Exception as e:
        total = 0
        print(f"Error counting table rows: {e}")
        
    # Obtener filas paginadas
    paginated_query = f'{query_str} LIMIT :limit OFFSET :offset'
    query_params["limit"] = limit
    query_params["offset"] = skip
    
    try:
        with dest_engine.connect() as conn:
            result = conn.execute(text(paginated_query), query_params)
            rows = result.fetchall()
            keys = list(result.keys())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al leer la tabla '{clean_table}': {str(e)}")
        
    # Sanitizar filas
    sanitized_items = []
    
    def _clean_val(v):
        if v is None: return None
        if isinstance(v, Decimal): return float(v)
        if isinstance(v, (_dt, _date)): return str(v)
        if isinstance(v, bytes): return v.decode("utf-8", errors="replace")
        if isinstance(v, float) and np.isnan(v): return None
        return v

    for row in rows:
        row_dict = dict(zip(keys, row))
        sanitized_items.append({k: _clean_val(v) for k, v in row_dict.items()})
        
    return {
        "columns": columns,
        "total": total,
        "items": sanitized_items
    }


@router.post("/clear-period-staging")
def clear_period_staging(body: dict, db: Session = Depends(get_dest_db)):
    company_id = body.get("company_id")
    subcategoria_id = body.get("subcategoria_id")
    periodo = body.get("periodo")
    mes = body.get("mes")

    if not company_id or not subcategoria_id or not periodo or not mes:
        raise HTTPException(status_code=400, detail="Falta company_id, subcategoria_id, periodo o mes")

    from backend.app.models.models import MapeoSubcategoria, AsientoCorrelativo
    from sqlalchemy import Table, MetaData, select, func

    sub = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.id == subcategoria_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subcategoría no encontrada")

    tabla_det_name = sub.tabla_destino_detalle or "cf_diariol"
    tabla_head_name = sub.tabla_destino_cabecera or "cf_diario"

    metadata = MetaData()
    engine = db.get_bind()

    try:
        DetTable = Table(tabla_det_name, metadata, autoload_with=engine)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"No se pudo cargar la tabla de detalle '{tabla_det_name}': {str(e)}")

    try:
        HeadTable = Table(tabla_head_name, metadata, autoload_with=engine)
    except:
        HeadTable = None

    deleted_det = 0
    deleted_head = 0

    has_company = "company_id" in DetTable.c
    has_subcat = "subcategoria_id" in DetTable.c
    has_cper = "cper" in DetTable.c
    has_cmes = "cmes" in DetTable.c
    nasiento_col = sub.col_destino_nasiento or "nasiento"
    has_nasiento = nasiento_col in DetTable.c

    # We build the deletion filters dynamically
    det_del_stmt = DetTable.delete()
    det_sel_stmt = select(DetTable.c[nasiento_col]) if (has_nasiento and HeadTable is not None) else None

    # Apply where clauses for selecting/deleting detail rows
    where_clauses = []
    if has_company:
        where_clauses.append(DetTable.c.company_id == company_id)
    if has_subcat:
        where_clauses.append(DetTable.c.subcategoria_id == subcategoria_id)
    if has_cper and periodo != "GLOBAL":
        where_clauses.append(DetTable.c.cper == periodo)
    if has_cmes and mes != "00":
        where_clauses.append(DetTable.c.cmes == mes)

    if where_clauses:
        for clause in where_clauses:
            det_del_stmt = det_del_stmt.where(clause)
            if det_sel_stmt is not None:
                det_sel_stmt = det_sel_stmt.where(clause)

    # Collect nasiento values to delete headers
    asientos_to_delete = []
    if det_sel_stmt is not None:
        try:
            res_asientos = db.execute(det_sel_stmt.distinct()).fetchall()
            asientos_to_delete = [r[0] for r in res_asientos if r[0] is not None]
        except Exception as e:
            print(f"Error fetching seats to delete: {e}")

    # Delete details
    try:
        res_del_det = db.execute(det_del_stmt)
        deleted_det = res_del_det.rowcount
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al borrar detalles de staging: {str(e)}")

    # Delete headers
    if HeadTable is not None and asientos_to_delete:
        head_del_stmt = HeadTable.delete()
        head_where = []
        if "company_id" in HeadTable.c:
            head_where.append(HeadTable.c.company_id == company_id)
        if "cper" in HeadTable.c and periodo != "GLOBAL":
            head_where.append(HeadTable.c.cper == periodo)
        if "cmes" in HeadTable.c and mes != "00":
            head_where.append(HeadTable.c.cmes == mes)
        
        # Match seat col in head table
        head_nasiento_col = nasiento_col if nasiento_col in HeadTable.c else "nasiento"
        if head_nasiento_col in HeadTable.c:
            head_where.append(HeadTable.c[head_nasiento_col].in_(asientos_to_delete))

        if head_where:
            for hw in head_where:
                head_del_stmt = head_del_stmt.where(hw)
            try:
                res_del_head = db.execute(head_del_stmt)
                deleted_head = res_del_head.rowcount
            except Exception as e:
                db.rollback()
                raise HTTPException(status_code=500, detail=f"Error al borrar cabeceras de staging: {str(e)}")

    # Reset subcategory control value to None so it restarts from scratch
    sub.last_generated_control_value = None

    # Reset correlatives
    try:
        corrs = db.query(AsientoCorrelativo).filter(
            AsientoCorrelativo.company_id == company_id,
            AsientoCorrelativo.subcategoria_id == sub.id
        ).all()
        for corr in corrs:
            is_target_corr = (corr.periodo == periodo and corr.mes == mes)
            if is_target_corr:
                corr.asiento_actual = corr.asiento_inicial - 1
            elif corr.periodo == "GLOBAL" and corr.mes == "00":
                # Recompute global seat based on remaining MIGRADO records in DetTable
                if has_nasiento:
                    stmt_max_mig = select(func.max(DetTable.c[nasiento_col])).where(
                        DetTable.c.company_id == company_id,
                        DetTable.c.subcategoria_id == sub.id,
                        DetTable.c.estado == "MIGRADO"
                    )
                    max_mig = db.execute(stmt_max_mig).scalar()
                    if max_mig is not None:
                        corr.asiento_actual = int(max_mig)
                    else:
                        corr.asiento_actual = corr.asiento_inicial - 1
                else:
                    corr.asiento_actual = corr.asiento_inicial - 1
    except Exception as ex_corr:
        print(f"Error resetting correlativos in clear_period_staging: {ex_corr}")

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al confirmar la limpieza: {str(e)}")

    return {
        "status": "SUCCESS",
        "message": f"Limpieza completada. Borrados {deleted_det} detalles y {deleted_head} cabeceras de staging para el periodo {periodo}-{mes}.",
        "deleted_details": deleted_det,
        "deleted_headers": deleted_head
    }


