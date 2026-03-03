import sys
sys.path.append('c:\\SistemaMigConta')
from backend.app.core.database import dest_engine
import pandas as pd
df = pd.read_sql('SELECT coddoc, nrodoc, "C_car", "C_numercomprobante", "C_puntoventa" FROM ccbrgdoc WHERE coddoc IS NOT NULL LIMIT 10', dest_engine)
print(df)
