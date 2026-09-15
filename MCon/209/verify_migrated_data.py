#!/usr/bin/env python3
"""Script para verificar datos migrados en Contasis."""

import psycopg2
import sys

def verify_migrated_data():
    """Verifica los datos migrados en Contasis."""
    try:
        conn_str = "postgresql://postgres:postgres@192.168.2.90:5432/contasis_002"
        print("Conectando a Contasis...")
        conn = psycopg2.connect(conn_str)
        
        cursor = conn.cursor()
        
        # Obtener últimas cabeceras migradas
        query_cabecera = """
            SELECT nasiento, cper, cmes, ccodori, cmoneda, cglosa_2
            FROM cf_diario
            WHERE cper = '2026' AND cmes = '05' AND ccodori = '209'
            ORDER BY nasiento DESC
            LIMIT 5
        """
        cursor.execute(query_cabecera)
        cabeceras = cursor.fetchall()
        
        print(f"\nÚltimas 5 cabeceras migradas:")
        for cab in cabeceras:
            print(f"  - Asiento {cab[0]}: Periodo {cab[1]}-{cab[2]}, Origen {cab[3]}, Moneda {cab[4]}, Glosa: {cab[5]}")
        
        # Verificar líneas de detalle con cserie y cnumero
        query_detalle = """
            SELECT d.nasiento, d.nidlin, d.ccodcue, d.ndebe, d.nhaber, d.cglosa, d.cper, d.cmes, d.ccodori, d.cserie, d.cnumero
            FROM cf_diariol d
            WHERE d.cper = '2026' AND d.cmes = '05' AND d.ccodori = '209'
            ORDER BY d.nasiento DESC, d.nidlin
            LIMIT 10
        """
        cursor.execute(query_detalle)
        detalles = cursor.fetchall()
        
        print(f"\nÚltimas 10 líneas de detalle migradas:")
        for det in detalles:
            print(f"  - Asiento {det[0]}, Línea {det[1]}: Cuenta {det[2]}, Debe {det[3]}, Haber {det[4]}")
            print(f"    Glosa: {det[5]}, Serie: {det[9]}, Número: {det[10]}")
        
        # Verificar totales por asiento
        query_totales = """
            SELECT d.nasiento, 
                   SUM(CASE WHEN d.ndebe > 0 THEN d.ndebe ELSE 0 END) as total_debe,
                   SUM(CASE WHEN d.nhaber > 0 THEN d.nhaber ELSE 0 END) as total_haber,
                   COUNT(*) as num_lineas
            FROM cf_diariol d
            WHERE d.cper = '2026' AND d.cmes = '05' AND d.ccodori = '209'
            GROUP BY d.nasiento
            ORDER BY d.nasiento
        """
        cursor.execute(query_totales)
        totales = cursor.fetchall()
        
        print(f"\nTotales por asiento:")
        for tot in totales:
            print(f"  - Asiento {tot[0]}: Total Debe {tot[1]}, Total Haber {tot[2]}, Líneas {tot[3]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = verify_migrated_data()
    sys.exit(0 if success else 1)
