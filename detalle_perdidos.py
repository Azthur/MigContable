"""
Detalle (SOLO LECTURA) de asientos marcados MIGRADO en Migconta que NO existen en Contasis.
Muestra documento, tipo doc, serie, numero y cuenta contable.
Genera tambien /app/detalle_perdidos.html
"""
import logging
from datetime import datetime

logging.disable(logging.CRITICAL)

from sqlalchemy import text
from backend.app.core.database import DestSessionLocal
from backend.app.models.models import FinalDestConnection, Company
from backend.app.services.connection_manager import ConnectionManager

db = DestSessionLocal()
companies = db.query(Company).order_by(Company.id).all()

html = ["""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
<title>Detalle: MIGRADO ausentes en Contasis</title>
<style>
 body{font-family:'Segoe UI',Arial,sans-serif;background:#f4f6f9;margin:0;padding:24px;color:#222}
 h1{color:#1a3b5d;border-bottom:3px solid #1a3b5d;padding-bottom:8px}
 h2{color:#fff;background:#1a3b5d;padding:10px 14px;border-radius:6px;margin-top:30px}
 table{border-collapse:collapse;width:100%;font-size:12px;background:#fff;box-shadow:0 1px 4px rgba(0,0,0,.1)}
 th{background:#e8eef5;text-align:left;padding:6px 8px;border:1px solid #cdd8e3;position:sticky;top:0}
 td{padding:4px 8px;border:1px solid #dde5ec}
 tr:nth-child(even){background:#f7fafc}
 .num{text-align:right}
 .small{font-size:12px;color:#666}
</style></head><body>
<h1>Asientos MIGRADO en Migconta ausentes en Contasis</h1>
<p class="small">Generado: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """ | Solo lectura</p>"""]

for comp in companies:
    cid = comp.id
    final_conn = db.query(FinalDestConnection).filter(
        FinalDestConnection.company_id == cid,
        FinalDestConnection.is_active == True
    ).first()
    if not final_conn:
        continue
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
        final_engine.dispose()
    except Exception as e:
        print(f"Empresa {cid}: error conexion Contasis: {str(e)[:120]}")
        continue

    mig = db.execute(text("""
        SELECT DISTINCT cper, cmes, TRIM(ccodori) AS ccodori, nasiento
        FROM cf_diariol WHERE company_id = :cid AND estado = 'MIGRADO'
    """), {"cid": cid}).fetchall()
    perdidos = [(str(r.cper), str(r.cmes), str(r.ccodori), int(r.nasiento)) for r in mig
                if (str(r.cper), str(r.cmes), str(r.ccodori), int(r.nasiento) if r.nasiento is not None else None) not in contasis_keys]

    if not perdidos:
        continue

    nombre = getattr(comp, "razon_social", None) or getattr(comp, "nombre", f"Empresa {cid}")
    print(f"\n{'='*130}")
    print(f"EMPRESA {cid}: {nombre}  ->  {len(perdidos)} asientos perdidos")
    print(f"{'='*130}")
    header = f"{'Per-Mes':9s} {'Ori':4s} {'Asiento':8s} {'Lin':4s} {'TDoc':5s} {'Serie':8s} {'Numero':12s} {'FechaDoc':11s} {'Cuenta':14s} {'Debe':>12s} {'Haber':>12s}  Glosa"
    print(header)
    print("-" * 130)

    html.append(f'<h2>Empresa {cid}: {nombre} &mdash; {len(perdidos)} asientos</h2>')
    html.append('<table><tr><th>Periodo</th><th>Mes</th><th>Origen</th><th>Asiento</th><th>L&iacute;nea</th><th>Tipo Doc</th><th>Serie</th><th>N&uacute;mero</th><th>Fecha Doc</th><th>Cuenta</th><th>Debe</th><th>Haber</th><th>Glosa</th></tr>')

    for (p, m, o, n) in sorted(perdidos):
        lineas = db.execute(text("""
            SELECT nidlin, ccoddoc, cserie, cnumero, ffechadoc, ccodcue, ndebe, nhaber, cglosa
            FROM cf_diariol
            WHERE company_id = :cid AND estado = 'MIGRADO'
              AND cper = :p AND cmes = :m AND TRIM(ccodori) = :o AND nasiento = :n
            ORDER BY nidlin
        """), {"cid": cid, "p": p, "m": m, "o": o, "n": n}).fetchall()
        for l in lineas:
            glosa = (l.cglosa or "").strip()[:45]
            fila = (f"{p}-{m}".ljust(9) + " " + str(o).ljust(4) + " " + str(n).ljust(8) + " "
                    + str(l.nidlin or 0).ljust(4) + " " + str(l.ccoddoc or '').ljust(5) + " "
                    + str(l.cserie or '').ljust(8) + " " + str(l.cnumero or '').ljust(12) + " "
                    + str(l.ffechadoc or '').ljust(11) + " " + str(l.ccodcue or '').ljust(14) + " "
                    + ("%.2f" % float(l.ndebe or 0)).rjust(12) + " " + ("%.2f" % float(l.nhaber or 0)).rjust(12) + "  " + glosa)
            print(fila)
            html.append(f'<tr><td>{p}</td><td>{m}</td><td>{o}</td><td>{n}</td><td>{l.nidlin or ""}</td>'
                        f'<td>{l.ccoddoc or ""}</td><td>{l.cserie or ""}</td><td>{l.cnumero or ""}</td>'
                        f'<td>{l.ffechadoc or ""}</td><td>{l.ccodcue or ""}</td>'
                        f'<td class="num">{float(l.ndebe or 0):,.2f}</td><td class="num">{float(l.nhaber or 0):,.2f}</td>'
                        f'<td>{(l.cglosa or "").strip()[:80]}</td></tr>')
    html.append('</table>')

db.close()
html.append('</body></html>')
with open("/app/detalle_perdidos.html", "w", encoding="utf-8") as f:
    f.write("".join(html))
print("\nDetalle HTML generado: /app/detalle_perdidos.html")
