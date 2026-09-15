"""
Reporte (SOLO LECTURA) de asientos realmente FALTANTES en Contasis
(marcados MIGRADO en Migconta, sin asiento ni documento en Contasis).
Genera: /app/asientos_faltantes.xlsx y /app/asientos_faltantes.pdf
Campos: empresa, libro (ccodori), periodo, mes, asiento, serie, numero,
        fecha, cuenta contable, monto, RUC y razon social del proveedor.
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

registros = []  # filas del reporte

for comp in companies:
    cid = comp.id
    nombre_emp = getattr(comp, "razon_social", None) or getattr(comp, "nombre", f"Empresa {cid}")
    fc = db.query(FinalDestConnection).filter(
        FinalDestConnection.company_id == cid,
        FinalDestConnection.is_active == True
    ).first()
    if not fc:
        continue
    try:
        eng = ConnectionManager.get_dest_engine({
            "host": fc.host, "port": fc.port, "database_name": fc.database_name,
            "username": fc.username, "password": fc.password
        })
        with eng.connect() as fdb:
            contasis_keys = set()
            for r in fdb.execute(text("SELECT cper, cmes, TRIM(ccodori), nasiento FROM cf_diario")):
                contasis_keys.add((str(r[0]), str(r[1]), str(r[2]), int(r[3]) if r[3] is not None else None))
    except Exception as e:
        print(f"Empresa {cid}: sin acceso a Contasis ({str(e)[:80]})")
        continue

    mig = db.execute(text("""
        SELECT DISTINCT cper, cmes, TRIM(ccodori) AS ccodori, nasiento
        FROM cf_diariol WHERE company_id = :cid AND estado = 'MIGRADO'
    """), {"cid": cid}).fetchall()
    perdidos = [(str(r.cper), str(r.cmes), str(r.ccodori), int(r.nasiento)) for r in mig
                if (str(r.cper), str(r.cmes), str(r.ccodori), int(r.nasiento) if r.nasiento is not None else None) not in contasis_keys]
    if not perdidos:
        eng.dispose()
        continue

    print(f"Empresa {cid}: analizando {len(perdidos)} asientos perdidos...")
    n_faltantes = 0

    with eng.connect() as fdb:
        cache_doc = {}
        cache_razon = {}
        for (p, m, o, n) in sorted(perdidos):
            lineas = db.execute(text("""
                SELECT nidlin, ccoddoc, cserie, cnumero, ffechadoc, ccodcue, ndebe, nhaber, cglosa, ccodruc
                FROM cf_diariol
                WHERE company_id = :cid AND estado = 'MIGRADO'
                  AND cper = :p AND cmes = :m AND TRIM(ccodori) = :o AND nasiento = :n
                ORDER BY nidlin
            """), {"cid": cid, "p": p, "m": m, "o": o, "n": n}).fetchall()
            if not lineas:
                continue

            # Documento representativo del asiento
            doc = None
            for l in lineas:
                d = (str(l.ccoddoc or '').strip(), str(l.cserie or '').strip(), str(l.cnumero or '').strip())
                if any(d):
                    doc = d
                    break
            if doc is None:
                continue

            # Existe el documento en Contasis?
            if doc in cache_doc:
                existe = cache_doc[doc]
            else:
                try:
                    existe = fdb.execute(text("""
                        SELECT 1 FROM cf_diariol
                        WHERE TRIM(ccoddoc) = :d AND TRIM(cserie) = :s AND TRIM(cnumero) = :num LIMIT 1
                    """), {"d": doc[0], "s": doc[1], "num": doc[2]}).first() is not None
                except Exception:
                    existe = False
                cache_doc[doc] = existe
            if existe:
                continue  # ya esta en Contasis bajo otro asiento -> no es faltante

            n_faltantes += 1

            # Razon social del proveedor (cg_entitrib en Contasis)
            ruc = str(lineas[0].ccodruc or '').strip()
            if ruc in cache_razon:
                razon = cache_razon[ruc]
            else:
                razon = ""
                if ruc:
                    try:
                        rr = fdb.execute(text("""
                            SELECT COALESCE(NULLIF(TRIM(crazsoc), ''),
                                   TRIM(CONCAT(TRIM(capepat), ' ', TRIM(capemat), ' ', TRIM(cnom1), ' ', TRIM(cnom2))))
                            FROM cg_entitrib WHERE TRIM(ccodruc) = :ruc LIMIT 1
                        """), {"ruc": ruc}).scalar()
                        razon = (rr or "").strip()
                    except Exception:
                        razon = ""
                cache_razon[ruc] = razon

            # Monto del asiento = suma del debe (o haber si debe es 0)
            tot_debe = sum(float(l.ndebe or 0) for l in lineas)
            tot_haber = sum(float(l.nhaber or 0) for l in lineas)
            monto = max(tot_debe, tot_haber)
            cuentas = ", ".join(sorted({str(l.ccodcue or '').strip() for l in lineas if l.ccodcue}))

            registros.append({
                "Empresa": f"{cid} - {nombre_emp}",
                "Libro (Origen)": o,
                "Periodo": p,
                "Mes": m,
                "Asiento": n,
                "Tipo Doc": doc[0],
                "Serie": doc[1].lstrip('0') or doc[1],
                "Numero": doc[2].lstrip('0') or doc[2],
                "Fecha Doc": str(lineas[0].ffechadoc or '').strip(),
                "Cuentas Contables": cuentas,
                "Monto": round(monto, 2),
                "RUC": ruc,
                "Razon Social": razon,
                "Glosa": (lineas[0].cglosa or "").strip()[:60],
            })
    eng.dispose()
    print(f"  -> Faltantes reales: {n_faltantes}")

db.close()

if not registros:
    print("No hay asientos faltantes. No se generan archivos.")
    raise SystemExit(0)

# ── Excel ──
import pandas as pd
df = pd.DataFrame(registros)
xlsx_path = "/app/asientos_faltantes.xlsx"
with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
    df.to_excel(writer, index=False, sheet_name="Faltantes")
    ws = writer.sheets["Faltantes"]
    for col_cells in ws.columns:
        width = max(len(str(c.value or "")) for c in col_cells) + 2
        ws.column_dimensions[col_cells[0].column_letter].width = min(width, 45)
print(f"Excel generado: {xlsx_path} ({len(df)} filas)")

# ── PDF ──
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

pdf_path = "/app/asientos_faltantes.pdf"
docpdf = SimpleDocTemplate(pdf_path, pagesize=landscape(A4),
                           leftMargin=10*mm, rightMargin=10*mm, topMargin=12*mm, bottomMargin=12*mm)
styles = getSampleStyleSheet()
cell_style = ParagraphStyle("cell", parent=styles["Normal"], fontSize=6.5, leading=8)
head_style = ParagraphStyle("head", parent=styles["Normal"], fontSize=7, leading=8, textColor=colors.white)

elems = [Paragraph("Asientos Faltantes en Contasis (documento no encontrado)", styles["Title"]),
         Paragraph(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} — Total: {len(df)} asientos", styles["Normal"]),
         Spacer(1, 6)]

cols = ["Empresa", "Libro (Origen)", "Periodo", "Mes", "Asiento", "Tipo Doc", "Serie",
        "Numero", "Fecha Doc", "Cuentas Contables", "Monto", "RUC", "Razon Social"]
data = [[Paragraph(c, head_style) for c in cols]]
for _, row in df.iterrows():
    data.append([Paragraph(str(row[c]), cell_style) for c in cols])

t = Table(data, repeatRows=1, colWidths=[38*mm, 14*mm, 13*mm, 9*mm, 13*mm, 11*mm, 14*mm, 20*mm, 17*mm, 38*mm, 15*mm, 20*mm, 48*mm])
t.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3b5d")),
    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#9db2c4")),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f8")]),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
]))
elems.append(t)
docpdf.build(elems)
print(f"PDF generado: {pdf_path}")
