import sys
sys.path.append('c:/SistemaMigConta')
import pyodbc
import pandas as pd

try:
    conn = pyodbc.connect('DRIVER={SQL Server};SERVER=192.168.1.17\\SQL2022;DATABASE=yelave22;UID=JUBER2;PWD=PasswordSeguro123!')
    print("Connected to SQL Server successfully.")
    
    query = "SELECT * FROM CcbRRdoc WHERE NroDoc = 'B050000015' AND CodCia = '002'"
    df = pd.read_sql(query, conn)
    print(f"Found {len(df)} rows in SQL Server:")
    print(df.to_dict('records'))
    
    # Also let's check count for CodCia = '002'
    res_cnt = conn.cursor().execute("SELECT COUNT(*) FROM CcbRRdoc WHERE CodCia = '002'").fetchone()[0]
    print("Total rows for CodCia '002' in SQL Server:", res_cnt)
    
finally:
    pass
