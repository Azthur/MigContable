"""
Módulo de monitoreo de I/O para SistemaMigConta
Proporciona métricas y tracking de operaciones I/O para identificar cuellos de botella
"""
import time
import psutil
from functools import wraps
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional
import threading

class IOMonitor:
    """Monitor de operaciones I/O con métricas agregadas"""
    
    def __init__(self):
        self.metrics = defaultdict(lambda: {
            'count': 0,
            'total_time': 0.0,
            'avg_time': 0.0,
            'min_time': float('inf'),
            'max_time': 0.0,
            'last_executed': None,
            'errors': 0
        })
        self._lock = threading.Lock()
        self._enabled = True
        
    def track_operation(self, operation_name: str):
        """Decorator para trackear operaciones I/O"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if not self._enabled:
                    return func(*args, **kwargs)
                
                start_time = time.time()
                error_occurred = False
                
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    error_occurred = True
                    raise
                finally:
                    elapsed = time.time() - start_time
                    self._record_metric(operation_name, elapsed, error_occurred)
                    print(f"[I/O Monitor] {operation_name}: {elapsed:.3f}s")
            
            return wrapper
        return decorator
    
    def _record_metric(self, operation_name: str, elapsed: float, error: bool):
        """Registra una métrica de operación"""
        with self._lock:
            metric = self.metrics[operation_name]
            metric['count'] += 1
            metric['total_time'] += elapsed
            metric['avg_time'] = metric['total_time'] / metric['count']
            metric['min_time'] = min(metric['min_time'], elapsed)
            metric['max_time'] = max(metric['max_time'], elapsed)
            metric['last_executed'] = datetime.now()
            if error:
                metric['errors'] += 1
    
    def get_metrics(self, operation_name: Optional[str] = None) -> Dict:
        """Obtiene métricas de una operación específica o todas"""
        with self._lock:
            if operation_name:
                return dict(self.metrics.get(operation_name, {}))
            return {k: dict(v) for k, v in self.metrics.items()}
    
    def get_system_io_stats(self) -> Dict:
        """Obtiene estadísticas de I/O del sistema"""
        try:
            disk_io = psutil.disk_io_counters()
            return {
                'read_bytes': disk_io.read_bytes if disk_io else 0,
                'write_bytes': disk_io.write_bytes if disk_io else 0,
                'read_count': disk_io.read_count if disk_io else 0,
                'write_count': disk_io.write_count if disk_io else 0,
                'timestamp': datetime.now()
            }
        except Exception:
            return {}
    
    def get_top_operations(self, limit: int = 10) -> List[Dict]:
        """Obtiene las operaciones con mayor tiempo total"""
        with self._lock:
            sorted_ops = sorted(
                self.metrics.items(),
                key=lambda x: x[1]['total_time'],
                reverse=True
            )
            return [
                {'operation': k, **v}
                for k, v in sorted_ops[:limit]
            ]
    
    def reset_metrics(self, operation_name: Optional[str] = None):
        """Resetea métricas de una operación o todas"""
        with self._lock:
            if operation_name:
                if operation_name in self.metrics:
                    del self.metrics[operation_name]
            else:
                self.metrics.clear()
    
    def enable(self):
        """Habilita el monitoreo"""
        self._enabled = True
    
    def disable(self):
        """Deshabilita el monitoreo"""
        self._enabled = False
    
    def generate_report(self) -> str:
        """Genera un reporte legible de las métricas"""
        report = []
        report.append("=== I/O Monitor Report ===")
        report.append(f"Generated at: {datetime.now()}")
        report.append("")
        
        top_ops = self.get_top_operations(5)
        if top_ops:
            report.append("Top 5 Operations by Total Time:")
            for i, op in enumerate(top_ops, 1):
                report.append(
                    f"{i}. {op['operation']}: "
                    f"count={op['count']}, "
                    f"total_time={op['total_time']:.3f}s, "
                    f"avg_time={op['avg_time']:.3f}s, "
                    f"errors={op['errors']}"
                )
        else:
            report.append("No operations tracked yet.")
        
        report.append("")
        system_stats = self.get_system_io_stats()
        if system_stats:
            report.append("System I/O Stats:")
            report.append(f"  Read bytes: {system_stats.get('read_bytes', 0)}")
            report.append(f"  Write bytes: {system_stats.get('write_bytes', 0)}")
            report.append(f"  Read count: {system_stats.get('read_count', 0)}")
            report.append(f"  Write count: {system_stats.get('write_count', 0)}")
        
        return "\n".join(report)


# Instancia global del monitor
io_monitor = IOMonitor()


def track_io(operation_name: str):
    """Convenience function para usar como decorator"""
    return io_monitor.track_operation(operation_name)
