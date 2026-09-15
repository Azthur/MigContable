import psycopg2
import json

# Conexión a la base de datos migconta_db
conn = psycopg2.connect(
    host="localhost",
    port=5434,
    database="migconta_db",
    user="postgres",
    password="postgres"
)

cursor = conn.cursor()

# Consultar configuración de mapeo_subcategorias para auxiliares
query = """
SELECT id, nombre, tabla_origen, tabla_destino_detalle, tabla_destino_cabecera, 
       mapeo_cabecera, filter_rules, tipo_generacion
FROM mapeo_subcategorias 
WHERE nombre ILIKE '%auxi%' OR tabla_origen ILIKE '%auxi%' OR tabla_destino_detalle ILIKE '%auxi%'
ORDER BY id;
"""

cursor.execute(query)
results = cursor.fetchall()

print("=== CONFIGURACIÓN MAPEO SUBCATEGORIAS (AUXILIARES) ===\n")
for row in results:
    print(f"ID: {row[0]}")
    print(f"Nombre: {row[1]}")
    print(f"Tabla Origen: {row[2]}")
    print(f"Tabla Destino Detalle: {row[3]}")
    print(f"Tabla Destino Cabecera: {row[4]}")
    print(f"Mapeo Cabecera: {row[5]}")
    print(f"Filter Rules: {row[6]}")
    print(f"Tipo Generación: {row[7]}")
    print("-" * 80)

# Consultar column_filters para estas tablas
query_filters = """
SELECT cf.id, cf.column_name, cf.operator, cf.filter_value, cf.filter_value2, ts.table_name
FROM column_filters cf
JOIN table_selections ts ON cf.table_selection_id = ts.id
WHERE ts.table_name ILIKE '%auxi%'
ORDER BY cf.id;
"""

cursor.execute(query_filters)
filter_results = cursor.fetchall()

print("\n=== COLUMN FILTERS PARA TABLAS AUXILIARES ===\n")
for row in filter_results:
    print(f"ID: {row[0]}")
    print(f"Tabla: {row[5]}")
    print(f"Columna: {row[1]}")
    print(f"Operador: {row[2]}")
    print(f"Valor: {row[3]}")
    print(f"Valor2: {row[4]}")
    print("-" * 80)

cursor.close()
conn.close()
