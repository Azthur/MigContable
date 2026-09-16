"""
Monitor de recursos para SistemaMigConta.

- log_memory_checkpoint(): registra RSS del proceso + memoria del cgroup
  (límite/uso del contenedor) en puntos críticos del ETL. Permite ubicar
  en qué etapa la memoria explota antes de un OOMKill.
- attach_slow_query_logging(): listener SQLAlchemy que loguea queries
  que superen un umbral de duración.
"""
import os
import time
import logging
import psutil
from sqlalchemy import event
from sqlalchemy.engine import Engine

logger = logging.getLogger("resource_monitor")

SLOW_QUERY_THRESHOLD_S = float(os.getenv("SLOW_QUERY_THRESHOLD_S", "5"))
MEM_WARN_PCT = float(os.getenv("MEM_WARN_PCT", "80"))


def _cgroup_memory():
    """Lee uso y límite de memoria del contenedor (cgroup v2 y v1)."""
    for cur_path, max_path in (
        ("/sys/fs/cgroup/memory.current", "/sys/fs/cgroup/memory.max"),          # v2
        ("/sys/fs/cgroup/memory/memory.usage_in_bytes",                          # v1
         "/sys/fs/cgroup/memory/memory.limit_in_bytes"),
    ):
        try:
            with open(cur_path) as f:
                current = int(f.read().strip())
            with open(max_path) as f:
                raw = f.read().strip()
            limit = int(raw) if raw != "max" else 0
            # En v1 sin límite el valor es un número enorme
            if limit > 1 << 60:
                limit = 0
            return current, limit
        except Exception:
            continue
    return 0, 0


def log_memory_checkpoint(label: str, extra: str = ""):
    """Loguea snapshot de memoria. WARN si el contenedor supera MEM_WARN_PCT."""
    try:
        proc = psutil.Process(os.getpid())
        rss_mb = proc.memory_info().rss / (1024 * 1024)
        cg_cur, cg_max = _cgroup_memory()
        cg_cur_mb = cg_cur / (1024 * 1024)
        sys_mem = psutil.virtual_memory()

        if cg_max:
            cg_max_mb = cg_max / (1024 * 1024)
            pct = cg_cur * 100.0 / cg_max
            msg = (
                f"[MEM] {label} | proc_rss={rss_mb:.0f}MB | "
                f"container={cg_cur_mb:.0f}/{cg_max_mb:.0f}MB ({pct:.1f}%) | "
                f"sys_avail={sys_mem.available / (1024**3):.1f}GB"
            )
            if pct >= MEM_WARN_PCT:
                logger.warning(msg + " <== CRITICO")
            else:
                logger.info(msg)
        else:
            logger.info(
                f"[MEM] {label} | proc_rss={rss_mb:.0f}MB | "
                f"sys_used={sys_mem.percent}% | "
                f"sys_avail={sys_mem.available / (1024**3):.1f}GB"
            )
        if extra:
            logger.info(f"[MEM] {label} | {extra}")
    except Exception as e:
        logger.warning(f"[MEM] {label} | error capturando memoria: {e}")


def attach_slow_query_logging(engine: Engine, engine_name: str):
    """Loguea queries que superen SLOW_QUERY_THRESHOLD_S segundos."""

    @event.listens_for(engine, "before_cursor_execute")
    def _before(conn, cursor, statement, parameters, context, executemany):
        conn.info["_query_start_time"] = time.time()

    @event.listens_for(engine, "after_cursor_execute")
    def _after(conn, cursor, statement, parameters, context, executemany):
        start = conn.info.pop("_query_start_time", None)
        if start is None:
            return
        elapsed = time.time() - start
        if elapsed >= SLOW_QUERY_THRESHOLD_S:
            logger.warning(
                f"[SLOW_QUERY] {engine_name} | {elapsed:.2f}s | "
                f"{statement[:500]}"
            )
