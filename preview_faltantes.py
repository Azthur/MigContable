import pandas as pd
df = pd.read_excel("/app/asientos_faltantes.xlsx")
pd.set_option("display.width", 250)
pd.set_option("display.max_columns", None)
print(df[["Empresa", "Libro (Origen)", "Periodo", "Mes", "Asiento", "Tipo Doc", "Serie", "Numero", "Fecha Doc", "Monto", "RUC", "Razon Social"]].to_string(index=False))
