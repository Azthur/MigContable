#!/usr/bin/env python3
"""Script para debug del DataFrame y columna Fecha."""
import sys
sys.path.insert(0, '/app')

import importlib
import backend.app.api.endpoints.mapeo as mapeo_module
importlib.reload(mapeo_module)

from backend.app.core.database import get_dest_db
from backend.app.models.models import MapeoSubcategoria
from backend.app.api.endpoints.mapeo import _get_df_period_month_cols, _extract_period_month
from sqlalchemy import text
import pandas as pd

def debug_dataframe_fecha():
    db = next(get_dest_db())
    
    try:
        # Subcategoría 81 (YLV Nature, mes 07)
        sub = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.id == 81).first()
        
        print(f"=== DEBUG SUBCATEGORÍA {sub.id}: {sub.nombre} ===")
        print(f"Filter rules: {sub.filter_rules}")
        print(f"Tabla origen: {sub.tabla_origen}")
        
        # Cargar datos de la tabla origen
        from sqlalchemy import Table, MetaData
        metadata = MetaData()
        engine = db.bind
        
        tabla_origen = Table(sub.tabla_origen.lower(), metadata, autoload_with=engine)
        
        # Construir query con filtros
        query_str = f'SELECT * FROM "{sub.tabla_origen.lower()}"'
        where_parts = ["company_id = 5"]
        
        # Aplicar filtros de la subcategoría
        for rule in sub.filter_rules:
            col = rule.get("column", "")
            op = rule.get("operator", "=")
            val = rule.get("value", "")
            if col and val:
                where_parts.append(f'"{col}" {op} \'{val}\'')
        
        if where_parts:
            query_str += " WHERE " + " AND ".join(where_parts)
        
        print(f"\nQuery: {query_str}")
        
        # Ejecutar query
        result = db.execute(text(query_str))
        rows = result.fetchall()
        columns = list(result.keys())
        
        print(f"Columnas: {columns}")
        print(f"Total filas: {len(rows)}")
        
        if rows:
            df = pd.DataFrame(rows, columns=columns)
            print(f"\nPrimeras 5 filas del DataFrame:")
            print(df.head())
            
            # Verificar si hay columna Fecha
            print(f"\nColumnas en DataFrame: {df.columns.tolist()}")
            
            # Probar _get_df_period_month_cols
            # Debug: mostrar df_cols_lower
            df_cols_lower = {col_name.lower(): col_name for col_name in df.columns}
            print(f"\ndf_cols_lower: {df_cols_lower}")
            print(f"'fecha' in df_cols_lower: {'fecha' in df_cols_lower}")
            
            period_col, mes_col = _get_df_period_month_cols(df, sub)
            print(f"\nperiod_col: {period_col}")
            print(f"mes_col: {mes_col}")
            
            # Probar _extract_period_month
            default_period, default_mes = _extract_period_month(sub.filter_rules, None, sub=sub, df=df)
            print(f"\ndefault_period: {default_period}")
            print(f"default_mes: {default_mes}")
            
            # Verificar valores de la columna Fecha
            if 'Fecha' in df.columns:
                print(f"\nValores de Fecha:")
                print(df['Fecha'].head())
                print(f"Tipo de datos: {df['Fecha'].dtype}")
                
                # Convertir a string
                df['Fecha_str'] = df['Fecha'].astype(str)
                print(f"\nValores de Fecha como string:")
                print(df['Fecha_str'].head())
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    debug_dataframe_fecha()
