from backend.app.core.database import DestSessionLocal
from sqlalchemy import text

db = DestSessionLocal()

print("=== VERIFICACIÓN DE ENCODING EN STAGING LOCAL (migconta_db) ===\n")

# Consulta SQL para verificar encoding de la base de datos
print("CONSULTA SQL:")
print("SELECT pg_database.datname, pg_encoding_to_char(pg_database.encoding)")
print("FROM pg_database")
print("WHERE pg_database.datname = current_database();\n")

result = db.execute(text("""
    SELECT pg_database.datname, pg_encoding_to_char(pg_database.encoding)
    FROM pg_database
    WHERE pg_database.datname = current_database()
""")).fetchone()

print(f"Base de datos: {result[0]}")
print(f"Encoding: {result[1]}")

# Verificar encoding del cliente
print("\nCONSULTA SQL:")
print("SHOW client_encoding;\n")

client_result = db.execute(text("SHOW client_encoding")).fetchone()
print(f"Client encoding: {client_result[0]}")

# Verificar encoding del servidor
print("\nCONSULTA SQL:")
print("SHOW server_encoding;\n")

server_result = db.execute(text("SHOW server_encoding")).fetchone()
print(f"Server encoding: {server_result[0]}")

db.close()
