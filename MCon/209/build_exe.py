#!/usr/bin/env python3
"""Script para crear el ejecutable del migrador Subdiario 209."""

import PyInstaller.__main__
import os
import sys

def build_executable():
    """Construye el ejecutable usando PyInstaller."""
    
    # Directorio actual
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Archivos a incluir
    config_file = os.path.join(current_dir, 'subdiario209_config.json')
    
    # Opciones de PyInstaller
    options = [
        'subdiario209_gui.py',  # Script principal
        '--name=MigradorSubdiario209',  # Nombre del ejecutable
        '--onefile',  # Crear un solo archivo
        '--console',  # Con consola para ver errores
        '--icon=NONE',  # Sin icono por ahora
        '--add-data={config_file};.'.format(config_file=config_file),  # Incluir config
        '--hidden-import=pyodbc',  # Importaciones ocultas necesarias
        '--hidden-import=psycopg2',
        '--clean',  # Limpiar build anterior
        '--noconfirm',  # No pedir confirmación
    ]
    
    print("Iniciando construcción del ejecutable...")
    print("Esto puede tomar varios minutos...")
    
    try:
        PyInstaller.__main__.run(options)
        print("\n[OK] Ejecutable creado exitosamente!")
        print("Ubicación: dist/MigradorSubdiario209.exe")
    except Exception as e:
        print(f"\n[ERROR] Error creando ejecutable: {e}")
        sys.exit(1)

if __name__ == "__main__":
    build_executable()
