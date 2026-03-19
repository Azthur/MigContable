import os
from dotenv import load_dotenv
load_dotenv()
from sqlalchemy import create_engine, text
from app.core.config import get_settings

def main():
    settings = get_settings()
    engine = create_engine(settings.POSTGRES_CONNECTION_STRING)
    
    with engine.connect() as conn:
        try:
            print("Adding col_destino_debe to mapeo_subcategorias...")
            conn.execute(text("ALTER TABLE mapeo_subcategorias ADD COLUMN col_destino_debe VARCHAR(100);"))
        except Exception as e:
            print(f"Skipping (might exist): {e}")

        try:
            print("Adding col_destino_haber to mapeo_subcategorias...")
            conn.execute(text("ALTER TABLE mapeo_subcategorias ADD COLUMN col_destino_haber VARCHAR(100);"))
        except Exception as e:
            print(f"Skipping (might exist): {e}")

        try:
            print("Adding aplica_ajuste_redondeo to mapeo_lineas_asiento...")
            conn.execute(text("ALTER TABLE mapeo_lineas_asiento ADD COLUMN aplica_ajuste_redondeo BOOLEAN DEFAULT FALSE;"))
        except Exception as e:
            print(f"Skipping (might exist): {e}")
            
        conn.commit()
    print("Columns added successfully!")

if __name__ == "__main__":
    main()
