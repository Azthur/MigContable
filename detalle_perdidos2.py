"""
Detalle (SOLO LECTURA) de asientos MIGRADO en Migconta ausentes en Contasis,
verificando ademas si el DOCUMENTO (tipo, serie, numero) existe en Contasis
bajo OTRO asiento (posible ingreso manual).
Genera /app/detalle_perdidos.html
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
 .manual{background:#fdebd0 !important;font-weight:600;color:#b26a00}
 .nofound{color:#c0392b;font-weight:600}
 .kpis{display:flex;gap:14px;flex-wrap:wrap;margin:10px 0}
 .kpi{background:#f0f4f8;border:1px solid #d7e0ea;border-radius:8px;padding:8px 14px}
 .kpi .v{font-size:20px;font-weight:700}.kpi .l{font-size:11px;color:#567}
</style></head><body>
<h1>Asientos MIGRADO en Migconta ausentes en Contasis</h1>
<p class="small">Generado: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """ | Solo lectura.
Columna <b>&iquest;Doc en Contasis?</b>: indica si el mismo documento (tipo+serie+n&uacute;mero) ya existe en Contasis bajo otro asiento (posible ingreso manual).</p>"""]

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
        final_engine.dispose()
        continue

    nombre = getattr(comp, "razon_social", None) or getattr(comp, "nombre", f"Empresa {cid}")
    print(f"Empresa {cid}: {len(perdidos)} asientos perdidos, verificando documentos en Contasis...")

    filas = []
    docs_encontrados = 0
    docs_no_encontrados = 0
    cache_doc = {}

    with final_engine.connect() as fdb:
        for (p, m, o, n) in sorted(perdidos):
            lineas = db.execute(text("""
                SELECT nidlin, ccoddoc, cserie, cnumero, ffechadoc, ccodcue, ndebe, nhaber, cglosa
                FROM cf_diariol
                WHERE company_id = :cid AND estado = 'MIGRADO'
                  AND cper = :p AND cmes = :m AND TRIM(ccodori) = :o AND nasiento = :n
                ORDER BY nidlin
            """), {"cid": cid, "p": p, "m": m, "o": o, "n": n}).fetchall()

            # Documento representativo del asiento (primera linea con doc)
            doc_status_asiento = None
            for l in lineas:
                doc = (str(l.ccoddoc or '').strip(), str(l.cserie or '').strip(), str(l.cnumero or '').strip())
                if not any(doc):
                    doc_status = ""
                elif doc in cache_doc:
                    doc_status = cache_doc[doc]
                else:
                    try:
                        found = fdb.execute(text("""
                            SELECT DISTINCT cper, cmes, TRIM(ccodori), nasiento
                            FROM cf_diariol
                            WHERE TRIM(ccoddoc) = :d AND TRIM(cserie) = :s AND TRIM(cnumero) = :num
                            LIMIT 5
                        """), {"d": doc[0], "s": doc[1], "num": doc[2]}).fetchall()
                    except Exception:
                        found = []
                    if found:
                        refs = "; ".join(f"{f[0]}-{f[1]}-{f[2]}-{f[3]}" for f in found)
                        doc_status = f"SI (asiento: {refs})"
                    else:
                        doc_status = "NO"
                    cache_doc[doc] = doc_status
                if doc_status_asiento is None and doc_status:
                    doc_status_asiento = doc_status
                filas.append((p, m, o, n, l, doc_status))

            if doc_status_asiento and doc_status_asiento.startswith("SI"):
                docs_encontrados += 1
            elif doc_status_asiento == "NO":
                docs_no_encontrados += 1

    final_engine.dispose()

    html.append(f'<h2>Empresa {cid}: {nombre} &mdash; {len(perdidos)} asientos perdidos</h2>')
    html.append('<div class="kpis">')
    html.append(f'<div class="kpi"><div class="v" style="color:#b26a00">{docs_encontrados}</div><div class="l">Asientos cuyo documento S&Iacute; existe en Contasis (otro asiento / posible manual)</div></div>')
    html.append(f'<div class="kpi"><div class="v" style="color:#c0392b">{docs_no_encontrados}</div><div class="l">Asientos cuyo documento NO existe en Contasis (falta migrar)</div></div>')
    html.append('</div>')
    html.append('<table><tr><th>Periodo</th><th>Mes</th><th>Origen</th><th>Asiento</th><th>L&iacute;nea</th><th>Tipo Doc</th><th>Serie</th><th>N&uacute;mero</th><th>Fecha Doc</th><th>Cuenta</th><th>Debe</th><th>Haber</th><th>Glosa</th><th>&iquest;Doc en Contasis?</th></tr>')
    for (p, m, o, n, l, doc_status) in filas:
        css = ' class="manual"' if doc_status.startswith("SI") else (' class="nofound"' if doc_status == "NO" else '')
        html.append(f'<tr><td>{p}</td><td>{m}</td><td>{o}</td><td>{n}</td><td>{l.nidlin or ""}</td>'
                    f'<td>{l.ccoddoc or ""}</td><td>{(l.cserie or "").strip()}</td><td>{(l.cnumero or "").strip()}</td>'
                    f'<td>{l.ffechadoc or ""}</td><td>{l.ccodcue or ""}</td>'
                    f'<td class="num">{float(l.ndebe or 0):,.2f}</td><td class="num">{float(l.nhaber or 0):,.2f}</td>'
                    f'<td>{(l.cglosa or "").strip()[:70]}</td><td{css}>{doc_status}</td></tr>')
    html.append('</table>')
    print(f"  -> Documentos encontrados en Contasis (otro asiento): {docs_encontrados} | No encontrados: {docs_no_encontrados}")

db.close()
html.append('</body></html>')
with open("/app/detalle_perdidos.html", "w", encoding="utf-8") as f:
    f.write("".join(html))
print("\nInforme actualizado: /app/detalle_perdidos.html")
