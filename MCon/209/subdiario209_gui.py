#!/usr/bin/env python3
"""Interfaz gráfica para el migrador del Subdiario 209."""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import sys
import os
from datetime import datetime
from subdiario209_migrator import Subdiario209Migrator
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class Subdiario209GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Migrador Subdiario 209")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        
        self.migrator = None
        self.migrating = False
        
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz de usuario."""
        # Título
        title_label = ttk.Label(
            self.root, 
            text="Migrador Subdiario 209", 
            font=('Arial', 16, 'bold')
        )
        title_label.pack(pady=10)
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Selección en una sola línea
        seleccion_frame = ttk.Frame(main_frame)
        seleccion_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(seleccion_frame, text="Empresa:").pack(side=tk.LEFT, padx=5)
        self.empresa_combo = ttk.Combobox(seleccion_frame, width=20, state="readonly")
        self.empresa_combo['values'] = [
            '002 - BOTICA YLV',
            '003 - CORP YLV', 
            '004 - GRUPO YLV',
            '005 - INDUSTRIAS',
            '007 - YELAVE NATURE'
        ]
        self.empresa_combo.current(4)  # Seleccionar 007 por defecto
        self.empresa_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(seleccion_frame, text="Año:").pack(side=tk.LEFT, padx=5)
        self.anio_combo = ttk.Combobox(seleccion_frame, width=8, state="readonly")
        anios = [str(y) for y in range(2024, 2031)]
        self.anio_combo['values'] = anios
        self.anio_combo.current(2)  # 2026 por defecto
        self.anio_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(seleccion_frame, text="Mes:").pack(side=tk.LEFT, padx=5)
        self.mes_combo = ttk.Combobox(seleccion_frame, width=15, state="readonly")
        meses = [
            '01 - Enero', '02 - Febrero', '03 - Marzo', '04 - Abril',
            '05 - Mayo', '06 - Junio', '07 - Julio', '08 - Agosto',
            '09 - Septiembre', '10 - Octubre', '11 - Noviembre', '12 - Diciembre'
        ]
        self.mes_combo['values'] = meses
        self.mes_combo.current(6)  # Julio por defecto
        self.mes_combo.pack(side=tk.LEFT, padx=5)
        
        # Botón de migrar
        self.migrar_button = ttk.Button(
            main_frame, 
            text="Iniciar Migración", 
            command=self.iniciar_migracion
        )
        self.migrar_button.pack(pady=15)
        
        # Área de log
        log_frame = ttk.Frame(main_frame)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        ttk.Label(log_frame, text="Log de migración:").pack(anchor=tk.W)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame, 
            height=15, 
            width=70,
            state='disabled'
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Configurar colores para el log
        self.log_text.tag_config('INFO', foreground='black')
        self.log_text.tag_config('WARNING', foreground='orange')
        self.log_text.tag_config('ERROR', foreground='red')
        self.log_text.tag_config('SUCCESS', foreground='green')
        
    def log_message(self, message, level='INFO'):
        """Agrega un mensaje al log."""
        self.log_text.config(state='normal')
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n", level)
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
        self.root.update()
        
    def get_codcia(self):
        """Obtiene el código de empresa seleccionado."""
        seleccion = self.empresa_combo.get()
        return seleccion.split(' - ')[0]
    
    def get_anio(self):
        """Obtiene el año seleccionado."""
        return self.anio_combo.get()
    
    def get_mes(self):
        """Obtiene el mes seleccionado."""
        seleccion = self.mes_combo.get()
        return seleccion.split(' - ')[0]
    
    def iniciar_migracion(self):
        """Inicia el proceso de migración en un hilo separado."""
        if self.migrating:
            messagebox.showwarning("Advertencia", "Ya hay una migración en proceso.")
            return
        
        codcia = self.get_codcia()
        anio = self.get_anio()
        mes = self.get_mes()
        
        self.log_message(f"Iniciando migración: Empresa {codcia}, Periodo {anio}-{mes}", 'INFO')
        
        self.migrating = True
        self.migrar_button.config(state='disabled')
        
        # Crear hilo para la migración
        thread = threading.Thread(target=self.ejecutar_migracion, args=(codcia, anio, mes))
        thread.daemon = True
        thread.start()
    
    def ejecutar_migracion(self, codcia, anio, mes):
        """Ejecuta la migración en un hilo separado."""
        try:
            # Crear instancia del migrador
            config_file = os.path.join(os.path.dirname(__file__), 'subdiario209_config.json')
            self.migrator = Subdiario209Migrator(config_file)
            
            # Cargar configuración
            if not self.migrator.load_config():
                self.log_message("Error cargando configuración", 'ERROR')
                self.finalizar_migracion(False)
                return
            
            self.log_message("Configuración cargada exitosamente", 'SUCCESS')
            
            # Ejecutar migración
            resultado = self.migrator.migrate_empresa(codcia, anio, mes)
            
            if resultado:
                self.log_message("Migración completada exitosamente", 'SUCCESS')
            else:
                self.log_message("Migración completada con errores", 'ERROR')
                self.log_message("Verifique la consola para detalles del error", 'WARNING')
                
        except Exception as e:
            self.log_message(f"Error en migración: {str(e)}", 'ERROR')
            self.log_message(f"Tipo de error: {type(e).__name__}", 'ERROR')
            import traceback
            self.log_message(f"Traceback: {traceback.format_exc()}", 'ERROR')
            logger.error(f"Error en migración: {e}")
        finally:
            self.finalizar_migracion()
    
    def finalizar_migracion(self, exito=True):
        """Finaliza el proceso de migración."""
        self.migrating = False
        self.migrar_button.config(state='normal')
        
        if self.migrator:
            self.migrator.close_connections()
            self.migrator = None


def main():
    """Función principal."""
    root = tk.Tk()
    app = Subdiario209GUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
