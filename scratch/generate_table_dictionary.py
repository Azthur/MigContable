import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.core.database import dest_engine
from sqlalchemy import inspect, text

# Descripciones de las tablas del sistema
TABLE_DESCRIPTIONS = {
    "users": "Usuarios del sistema con sus credenciales (hash de contraseña), roles (admin/operador) y estado de activación.",
    "companies": "Empresas registradas en el sistema para la integración de datos contables (con su nombre, RUC, descripción, etc.).",
    "source_connections": "Conexiones configuradas para las bases de datos de origen (SQL Server 2022 de Majestic/ventas) de cada empresa.",
    "destination_connections": "Conexiones configuradas para las bases de datos intermedias de destino (PostgreSQL) para cada empresa.",
    "final_dest_connections": "Conexiones a las bases de datos del destino contable final (por ejemplo, el software Contasis).",
    "final_table_selections": "Tablas seleccionadas en la base de datos de destino final para el mapeo.",
    "table_selections": "Configuración de las tablas que se extraerán de la base de datos de origen (esquema, nombre de tabla, orden de extracción, consultas personalizadas y columnas de control incremental).",
    "column_filters": "Filtros específicos aplicados a las columnas durante la extracción ETL de las tablas de origen.",
    "computed_column_rules": "Reglas condicionales para crear columnas calculadas en el ETL (fórmulas condicionales personalizadas estilo IF/ELSE).",
    "tipo_cambio": "Tipo de cambio diario (compra y venta) obtenido de la SUNAT.",
    "migration_controls": "Registro de control para la migración incremental de datos (último valor migrado, cantidad de registros, estado).",
    "cat_cuentas_contables": "Catálogo de plan de cuentas contables utilizado para realizar los mapeos.",
    "cat_cuentas_presupuesto": "Catálogo de cuentas presupuestales.",
    "cat_centros_costo": "Catálogo de centros de costo contables.",
    "cat_tipo_analitica": "Catálogo de tipos de analítica contable.",
    "cat_productos": "Catálogo de productos.",
    "cat_tipo_movimiento": "Catálogo de tipos de movimiento contable (ej. boletas, facturas).",
    "mapeo_categorias": "Categorías principales de mapeo contable (ej. 'Migración Majestic -> Contasis').",
    "mapeo_subcategorias": "Subcategorías específicas de mapeo contable (ej. 'Ventas', 'Compras'). Configura la tabla origen, cabeceras, detalles, redondeos, números de asientos iniciales, etc.",
    "mapeo_lineas_asiento": "Definición detallada de cada línea del asiento contable por subcategoría (cuentas contables, debe, haber, glosa, condiciones de aplicación, ajustes de redondeo, etc.).",
    "asientos_contables_generados": "Asientos contables generados y listos para ser exportados o migrados a Contasis en formato CSV.",
    "config_account_mapping": "Configuración personalizada para remapear cuentas de origen a cuentas de destino y centros de costo.",
    "config_document_mapping": "Configuración de mapeo de tipos de documentos de origen a tipos de documentos de destino (ej. 'F' -> '01').",
    "config_transformation_rules": "Reglas de transformación personalizadas para los datos.",
    "integ_logs": "Historial de registros de integración de datos (ETL) con detalles de ejecución, número de filas procesadas, errores y advertencias.",
    "accounting_entries": "Registro histórico de asientos contables procesados en el sistema.",
    "cf_diariol": "Staging / tabla intermedia para el detalle de asientos contables con la estructura exacta de la tabla `cf_diariol` de Contasis.",
    "cf_diario": "Staging / tabla intermedia para las cabeceras de asientos contables con la estructura exacta de la tabla `cf_diario` de Contasis.",
    "user_catalogs": "Catálogos personalizados definidos por el usuario.",
    "user_catalog_items": "Valores y elementos contenidos en los catálogos personalizados definidos por el usuario.",
    "scheduled_tasks": "Tareas del planificador interno (Celery Beat) programadas para ejecución de procesos recurrentes (ETL, descarga de tipo de cambio, etc.).",
    "task_logs": "Registro de ejecuciones de las tareas programadas.",
    "asiento_correlativos": "Control de los números de asientos correlativos por empresa, subcategoría, periodo (año) y mes.",
    "etl_realtime_logs": "Registro de logs en tiempo real para las ejecuciones del pipeline ETL.",
    "etl_pipeline_config": "Configuración maestra de las ejecuciones recurrentes de Celery para cada pipeline ETL.",
    "etl_ejecuciones": "Registro y log individual de cada tarea de pipeline ejecutada en Celery (tiempos, registros extraídos/generados/migrados, errores y logs).",
    
    # Tablas de Staging / Origen cargadas en migconta_db
    "admcaja": "Tabla de origen/staging que contiene los movimientos y transacciones de caja de la empresa.",
    "cbdmauxi": "Tabla de origen/staging relacionada con auxiliares o clientes/proveedores en el sistema.",
    "ccbmauxi": "Tabla de origen/staging de auxiliares contables y datos de terceras entidades de la base de datos.",
    "ccbmvtos": "Tabla de origen/staging que registra los movimientos y transacciones detalladas de cuentas por cobrar/pagar.",
    "ccbrgdoc": "Tabla de origen/staging que registra documentos de ventas, facturas y boletas emitidas (Registro de Documentos).",
    "ccbrrdoc": "Tabla de origen/staging que registra la información de referencia o relación de documentos de venta y notas de crédito.",
    "ccbtabla": "Tabla general de parámetros y constantes auxiliares configuradas en la base de datos de origen.",
    "cg_entitrib": "Tabla de origen/staging de entidades tributarias (clientes, proveedores, RUCs) para el reporte contable.",
    "cjamtipo": "Tabla de origen/staging que define los tipos de movimientos de caja.",
    "cntfacturacab": "Tabla de origen/staging que representa la cabecera de las facturas del sistema de ventas.",
    "cntfacturadet": "Tabla de origen/staging que representa el detalle (ítems) de las facturas del sistema de ventas.",
    "fac_electronica2": "Tabla de origen/staging que contiene información complementaria o de control de la facturación electrónica.",
    "finpagos": "Tabla de origen/staging que registra los pagos y cobranzas recibidas.",
    "finplanillamovilidadcab": "Tabla de origen/staging para las cabeceras de planillas de movilidad del personal.",
    "finplanillamovilidaddet": "Tabla de origen/staging para el detalle de gastos de movilidad del personal.",
    "finrendiciongastoscab": "Tabla de origen/staging para las cabeceras de rendiciones de gastos y caja chica.",
    "finrendiciongastosdet": "Tabla de origen/staging para los detalles de las rendiciones de gastos.",
    "postarje": "Tabla de origen/staging para transacciones con tarjeta de crédito/débito y terminales de punto de venta (POS).",
    "tbl_conciliados": "Tabla de origen/staging que guarda los registros que ya pasaron por conciliación bancaria.",
    "temp_empty_test": "Tabla temporal de prueba vacía creada con fines de testeo.",
    "temp_test_table": "Tabla temporal de prueba para validar la inserción de registros en la base de datos.",
    "vtaritem": "Tabla de origen/staging para los detalles de ítems de ventas y facturación diaria."
}

def generate_dictionary():
    inspector = inspect(dest_engine)
    tables = sorted(inspector.get_table_names())
    
    output_lines = []
    output_lines.append("=" * 80)
    output_lines.append("DICCIONARIO DE TABLAS DE LA BASE DE DATOS (MIGCONTA_DB)")
    output_lines.append(f"Proyecto: http://localhost:8080/")
    output_lines.append("=" * 80)
    output_lines.append("")
    output_lines.append("Este documento contiene el listado completo, el propósito y el esquema detallado de")
    output_lines.append("cada una de las tablas utilizadas en el sistema de integración contable SistemaMigConta.")
    output_lines.append("")
    output_lines.append(f"Total de tablas detectadas: {len(tables)}")
    output_lines.append("")
    
    # Generar índice de tablas
    output_lines.append("ÍNDICE DE TABLAS:")
    output_lines.append("-" * 40)
    for i, table_name in enumerate(tables, 1):
        desc = TABLE_DESCRIPTIONS.get(table_name, "Sin descripción registrada.")
        output_lines.append(f"{i:2d}. {table_name:<32} | {desc}")
    output_lines.append("")
    output_lines.append("=" * 80)
    output_lines.append("")
    
    # Generar detalle por tabla
    for i, table_name in enumerate(tables, 1):
        output_lines.append(f"TABLA {i:02d}: {table_name}")
        output_lines.append("-" * 80)
        
        desc = TABLE_DESCRIPTIONS.get(table_name, "Sin descripción registrada.")
        output_lines.append(f"Descripción: {desc}")
        
        # Obtener cantidad de registros
        row_count = 0
        try:
            with dest_engine.connect() as conn:
                res = conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"')).fetchone()
                row_count = res[0] if res else 0
            output_lines.append(f"Registros en BD: {row_count}")
        except Exception as e:
            output_lines.append(f"Registros en BD: Error al obtener conteo ({e})")
            
        output_lines.append("")
        
        # Obtener columnas
        columns = inspector.get_columns(table_name)
        pk_columns = inspector.get_pk_constraint(table_name).get("constrained_columns", [])
        
        # Dibujar tabla de columnas
        output_lines.append(f"  {'Columna':<30} | {'Tipo de Datos':<20} | {'Null?':<6} | {'PK?':<3}")
        output_lines.append(f"  {'-'*30}-+-{'-'*20}-+-{'-'*6}-+-{'-'*3}")
        
        for col in columns:
            name = col["name"]
            type_str = str(col["type"])
            nullable = "SÍ" if col["nullable"] else "NO"
            pk = "SÍ" if name in pk_columns else "NO"
            output_lines.append(f"  {name:<30} | {type_str:<20} | {nullable:<6} | {pk:<3}")
            
        output_lines.append("")
        
        # Obtener llaves foráneas (si hay)
        fks = inspector.get_foreign_keys(table_name)
        if fks:
            output_lines.append("  Llaves Foráneas:")
            for fk in fks:
                referred_table = fk["referred_table"]
                constrained_cols = ", ".join(fk["constrained_columns"])
                referred_cols = ", ".join(fk["referred_columns"])
                output_lines.append(f"   * {constrained_cols} -> {referred_table}({referred_cols})")
            output_lines.append("")
            
        output_lines.append("=" * 80)
        output_lines.append("")
        
    # Escribir el resultado
    out_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "diccionario_tablas.txt"))
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))
        
    print(f"Diccionario de tablas generado exitosamente en: {out_path}")

if __name__ == "__main__":
    generate_dictionary()
