import pandas as pd
from sqlalchemy.orm import Session
# Mock imports or simple local test of formula parser logic
import sys
sys.path.append('c:/SistemaMigConta')

from backend.app.core.formula_parser import evaluate_formula_on_df

# Create dummy df
df = pd.DataFrame({
    'urlvta_pdf': ['https://bmyelave.efactura.org.pe/print/document/6a644024-6f8a-450e-b33d-0436c6e15681/ticket'],
    'urlvta_xml': ['https://bmyelave.efactura.org.pe/downloads/document/xml/6a644024-6f8a-450e-b33d-0436c6e15681'],
    'urlvta_cdr': ['https://bmyelave.efactura.org.pe/downloads/document/cdr/6a644024-6f8a-450e-b33d-0436c6e15681ESTADO COMPROBANTE: Aceptado | La Factura numero FM06-24970, ha sido aceptado']
})

formula = 'CONCAT_EXACTO("PDF: ", CHR(10), URLVTA_pdf, CHR(10), "XML: ", CHR(10), URLVTA_XML, CHR(10), "CDR: ", CHR(10), URLVTA_CDR, CHR(10))'

# Test evaluate
res = evaluate_formula_on_df(df, formula, db=None, company_id=1)
print("Result:\n" + res.iloc[0])
