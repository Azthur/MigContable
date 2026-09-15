"""
Verificacion (SOLO LECTURA) de consistencia de migracion para TODAS las empresas.
Genera un informe HTML: /app/informe_migracion.html
"""
import sys
import logging
from datetime import datetime

logging.disable(logging.CRITICAL)

from sqlalchemy import text
from backend.app.core.database import DestSessionLocal
from backend.app.models.models import FinalDestConnection, Company
from backend.app.services.connection_manager import ConnectionManager

db = DestSessionLocal()
companies = db.query(Company).order_by(Company.id).all()

report = []

for comp in companies:
    cid = comp.id
    data = {"id": cid, "nombre": getattr(comp, "razon_social", None) or getattr(comp, "nombre", f"Empresa {cid}")}
    print(f"Procesando empresa {cid}...")

    # 1. Conteos por estado
    data["estados"] = [dict(r._mapping) for r in db.execute(text("""
        SELECT cper, cmes, estado, COUNT(*) AS lineas, COUNT(DISTINCT nasiento) AS asientos
        FROM cf_diariol WHERE company_id = :cid
        GROUP BY cper, cmes, estado ORDER BY cper, cmes, estado
    """), {"cid": cid}).fetchall()]

    # 2. Duplicados internos
    data["dup_internos"] = [dict(r._mapping) for r in db.execute(text("""
        SELECT cper, cmes, ccodori, nasiento, nidlin, COUNT(*) AS veces
        FROM cf_diariol WHERE company_id = :cid
        GROUP BY cper, cmes, ccodori, nasiento, nidlin HAVING COUNT(*) > 1
        ORDER BY cper, cmes, nasiento LIMIT 200
    """), {"cid": cid}).fetchall()]
    data["dup_internos_total"] = db.execute(text("""
        SELECT COUNT(*) FROM (
            SELECT 1 FROM cf_diariol WHERE company_id = :cid
            GROUP BY cper, cmes, ccodori, nasiento, nidlin HAVING COUNT(*) > 1
        ) t
    """), {"cid": cid}).scalar()

    # 3. Conexion Contasis
    final_conn = db.query(FinalDestConnection).filter(
        FinalDestConnection.company_id == cid,
        FinalDestConnection.is_active == True
    ).first()

    data["contasis"] = None
    data["pend_duplicados"] = []
    data["migrados_perdidos"] = []
    data["pend_total"] = 0
    data["mig_total"] = 0
    data["error_conexion"] = None

    if final_conn:
        try:
            final_engine = ConnectionManager.get_dest_engine({
                "host": final_conn.host, "port": final_conn.port,
                "database_name": final_conn.database_name,
                "username": final_conn.username, "password": final_conn.password
            })
            with final_engine.connect() as fdb:
                contasis_keys = set()
                for r in fdb.execute(text("SELECT cper, cmes, TRIM(ccodori), nasiento FROM cf_diario")):
                    contasis_keys.add((str(r[0]), str(r[1]), str(r[2]), int(r[3]) if r[3] is not None else None))
                det_count = fdb.execute(text("SELECT COUNT(*) FROM cf_diariol")).scalar()
            data["contasis"] = {
                "host": f"{final_conn.host}:{final_conn.port}/{final_conn.database_name}",
                "asientos": len(contasis_keys), "lineas": det_count
            }

            def get_keys(estado):
                rows = db.execute(text("""
                    SELECT DISTINCT cper, cmes, TRIM(ccodori) AS ccodori, nasiento
                    FROM cf_diariol WHERE company_id = :cid AND estado = :est
                """), {"cid": cid, "est": estado}).fetchall()
                return [(str(r.cper), str(r.cmes), str(r.ccodori), int(r.nasiento) if r.nasiento is not None else None) for r in rows]

            pend_keys = get_keys("PENDIENTE")
            mig_keys = get_keys("MIGRADO")
            data["pend_total"] = len(pend_keys)
            data["mig_total"] = len(mig_keys)
            data["pend_duplicados"] = [k for k in pend_keys if k in contasis_keys]
            data["migrados_perdidos"] = [k for k in mig_keys if k not in contasis_keys]
            final_engine.dispose()
        except Exception as e:
            data["error_conexion"] = str(e)[:300]
    report.append(data)

db.close()

# ── Generar HTML ──
def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

html = ["""<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8">
<title>Informe de Consistencia de Migracion</title>
<style>
  body { font-family: 'Segoe UI', Arial, sans-serif; background: #f4f6f9; color: #222; margin: 0; padding: 24px; }
  h1 { color: #1a3b5d; border-bottom: 3px solid #1a3b5d; padding-bottom: 8px; }
  h2 { color: #fff; background: #1a3b5d; padding: 10px 14px; border-radius: 6px 6px 0 0; margin-bottom: 0; }
  .empresa { background: #fff; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,.12); margin-bottom: 28px; overflow: hidden; }
  .body { padding: 16px 20px; }
  table { border-collapse: collapse; width: 100%; margin: 10px 0 18px; font-size: 13px; }
  th { background: #e8eef5; text-align: left; padding: 6px 10px; border: 1px solid #cdd8e3; }
  td { padding: 5px 10px; border: 1px solid #dde5ec; }
  .ok { color: #1b7f3b; font-weight: 600; }
  .warn { color: #b26a00; font-weight: 600; }
  .err { color: #c0392b; font-weight: 600; }
  .badge { display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: 700; margin-left: 8px; }
  .b-ok { background: #d4efdf; color: #1b7f3b; }
  .b-err { background: #fadbd8; color: #c0392b; }
  .b-warn { background: #fdebd0; color: #b26a00; }
  .kpis { display: flex; gap: 14px; flex-wrap: wrap; margin: 14px 0; }
  .kpi { background: #f0f4f8; border: 1px solid #d7e0ea; border-radius: 8px; padding: 10px 16px; min-width: 150px; }
  .kpi .v { font-size: 22px; font-weight: 700; }
  .kpi .l { font-size: 12px; color: #567; }
  .small { font-size: 12px; color: #666; }
  details summary { cursor: pointer; font-weight: 600; color: #1a3b5d; margin: 6px 0; }
</style></head><body>
<h1>Informe de Consistencia de Migraci&oacute;n &mdash; Migconta vs Contasis</h1>
<p class="small">Generado: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """ | Verificaci&oacute;n de solo lectura. Llave de asiento: (cper, cmes, ccodori, nasiento)</p>
"""]

for d in report:
    n_dup = d["dup_internos_total"] or 0
    n_bloq = len(d["pend_duplicados"])
    n_perd = len(d["migrados_perdidos"])
    problema = n_dup > 0 or n_bloq > 0 or n_perd > 0 or d["error_conexion"]
    badge = '<span class="badge b-err">CON PROBLEMAS</span>' if problema else '<span class="badge b-ok">OK</span>'

    html.append(f'<div class="empresa"><h2>Empresa {d["id"]}: {esc(d["nombre"])} {badge}</h2><div class="body">')

    if d["error_conexion"]:
        html.append(f'<p class="err">Error de conexi&oacute;n a Contasis: {esc(d["error_conexion"])}</p>')
    elif not d["contasis"]:
        html.append('<p class="warn">Sin conexi&oacute;n Contasis configurada (no se pudo comparar destino final).</p>')
    else:
        c = d["contasis"]
        html.append(f'<p class="small">Contasis: <b>{esc(c["host"])}</b> &mdash; {c["asientos"]:,} asientos / {c["lineas"]:,} l&iacute;neas</p>')

    html.append('<div class="kpis">')
    html.append(f'<div class="kpi"><div class="v {"err" if n_dup else "ok"}">{n_dup}</div><div class="l">Llaves duplicadas internas (staging)</div></div>')
    html.append(f'<div class="kpi"><div class="v {"err" if n_bloq else "ok"}">{n_bloq}</div><div class="l">PENDIENTE que ya existen en Contasis (bloquean)</div></div>')
    html.append(f'<div class="kpi"><div class="v {"warn" if n_perd else "ok"}">{n_perd}</div><div class="l">MIGRADO ausentes en Contasis (perdidos)</div></div>')
    html.append(f'<div class="kpi"><div class="v">{d["pend_total"]}</div><div class="l">Asientos PENDIENTE</div></div>')
    html.append(f'<div class="kpi"><div class="v">{d["mig_total"]}</div><div class="l">Asientos MIGRADO</div></div>')
    html.append('</div>')

    if d["estados"]:
        html.append('<details><summary>Detalle por periodo/mes/estado</summary><table><tr><th>Periodo</th><th>Mes</th><th>Estado</th><th>L&iacute;neas</th><th>Asientos</th></tr>')
        for r in d["estados"]:
            html.append(f'<tr><td>{esc(r["cper"])}</td><td>{esc(r["cmes"])}</td><td>{esc(r["estado"])}</td><td>{r["lineas"]:,}</td><td>{r["asientos"]:,}</td></tr>')
        html.append('</table></details>')

    if d["dup_internos"]:
        html.append(f'<details><summary class="err">Duplicados internos en staging ({n_dup} llaves, mostrando max 200)</summary><table><tr><th>Periodo</th><th>Mes</th><th>Origen</th><th>Asiento</th><th>L&iacute;nea</th><th>Veces</th></tr>')
        for r in d["dup_internos"]:
            html.append(f'<tr><td>{esc(r["cper"])}</td><td>{esc(r["cmes"])}</td><td>{esc(r["ccodori"])}</td><td>{r["nasiento"]}</td><td>{r["nidlin"]}</td><td class="err">{r["veces"]}</td></tr>')
        html.append('</table></details>')

    if d["pend_duplicados"]:
        html.append(f'<details><summary class="err">PENDIENTE ya existentes en Contasis ({n_bloq}, mostrando max 200)</summary><table><tr><th>Periodo</th><th>Mes</th><th>Origen</th><th>Asiento</th></tr>')
        for k in d["pend_duplicados"][:200]:
            html.append(f'<tr><td>{esc(k[0])}</td><td>{esc(k[1])}</td><td>{esc(k[2])}</td><td>{k[3]}</td></tr>')
        html.append('</table></details>')

    if d["migrados_perdidos"]:
        html.append(f'<details><summary class="warn">MIGRADO ausentes en Contasis ({n_perd}, mostrando max 200)</summary><table><tr><th>Periodo</th><th>Mes</th><th>Origen</th><th>Asiento</th></tr>')
        for k in sorted(d["migrados_perdidos"])[:200]:
            html.append(f'<tr><td>{esc(k[0])}</td><td>{esc(k[1])}</td><td>{esc(k[2])}</td><td>{k[3]}</td></tr>')
        html.append('</table></details>')

    if not problema:
        html.append('<p class="ok">Sin inconsistencias detectadas.</p>')

    html.append('</div></div>')

html.append("""
<div class="empresa"><h2>Leyenda y Recomendaciones</h2><div class="body">
<ul>
<li><b>Llaves duplicadas internas:</b> la misma l&iacute;nea de asiento existe 2+ veces en staging (Migconta). Causa <i>UniqueViolation</i> al migrar. Soluci&oacute;n: eliminar copias dejando solo una.</li>
<li><b>PENDIENTE ya existentes en Contasis:</b> asientos que el sistema intentar&aacute; insertar pero ya est&aacute;n en el destino. Causa <i>UniqueViolation</i>. Soluci&oacute;n: marcarlos como MIGRADO si el contenido coincide.</li>
<li><b>MIGRADO ausentes en Contasis:</b> el sistema cree que migraron pero no est&aacute;n en el destino (migraci&oacute;n incompleta). Soluci&oacute;n: re-marcarlos como PENDIENTE y volver a migrar.</li>
</ul>
</div></div>
</body></html>""")

with open("/app/informe_migracion.html", "w", encoding="utf-8") as f:
    f.write("".join(html))

print("\nInforme generado: /app/informe_migracion.html")
