"""
Endpoint para monitoreo de I/O del sistema
Proporciona métricas en tiempo real del consumo de I/O
"""
from fastapi import APIRouter
from typing import Dict, Optional
from backend.app.core.io_monitor import io_monitor

router = APIRouter()


@router.get("/io-metrics")
def get_io_metrics(operation: Optional[str] = None):
    """
    Obtiene métricas de I/O del sistema.
    
    Args:
        operation: Nombre específico de operación (opcional). Si no se proporciona, retorna todas.
    
    Returns:
        Diccionario con métricas de la operación especificada o todas las operaciones.
    """
    return io_monitor.get_metrics(operation)


@router.get("/io-system-stats")
def get_system_io_stats():
    """
    Obtiene estadísticas de I/O del sistema operativo.
    
    Returns:
        Diccionario con estadísticas de disco I/O (read/write bytes y counts).
    """
    return io_monitor.get_system_io_stats()


@router.get("/io-top-operations")
def get_top_io_operations(limit: int = 10):
    """
    Obtiene las operaciones con mayor consumo de I/O.
    
    Args:
        limit: Número de operaciones a retornar (default: 10).
    
    Returns:
        Lista de operaciones ordenadas por tiempo total de ejecución.
    """
    return io_monitor.get_top_operations(limit)


@router.get("/io-report")
def get_io_report():
    """
    Genera un reporte legible de las métricas de I/O.
    
    Returns:
        Reporte formateado como texto con las métricas principales.
    """
    return {"report": io_monitor.generate_report()}


@router.post("/io-reset")
def reset_io_metrics(operation: Optional[str] = None):
    """
    Resetea las métricas de I/O.
    
    Args:
        operation: Nombre específico de operación a resetear (opcional). 
                  Si no se proporciona, resetea todas las métricas.
    
    Returns:
        Mensaje de confirmación del reset.
    """
    io_monitor.reset_metrics(operation)
    return {
        "message": f"Metrics reset for {operation if operation else 'all operations'}",
        "operation": operation,
        "timestamp": io_monitor.get_system_io_stats().get("timestamp")
    }


@router.post("/io-toggle")
def toggle_io_monitoring(enabled: bool):
    """
    Habilita o deshabilita el monitoreo de I/O.
    
    Args:
        enabled: True para habilitar, False para deshabilitar.
    
    Returns:
        Estado actual del monitoreo.
    """
    if enabled:
        io_monitor.enable()
    else:
        io_monitor.disable()
    
    return {
        "enabled": enabled,
        "message": f"I/O monitoring {'enabled' if enabled else 'disabled'}"
    }
