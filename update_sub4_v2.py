from sqlalchemy import create_engine, text
import json
from backend.app.core.config import get_settings

def update_mapping():
    settings = get_settings()
    engine = create_engine(settings.POSTGRES_CONNECTION_STRING)
    with engine.connect() as conn:
        # Use single characters in quotes for char(1) columns
        m = {
            'cper': 'anos', 'cmes': 'C_mes', 'ccodori': "'0'", 
            'ffecasi': 'C_fechaEmision', 'cmoneda': "'S'", 
            'ccodusu': "'S'", 'tregistro': 'C_fechaEmision', 
            'ccodsu': "'1'", 'ntcblo': '0', 'ccodbas': '0', 
            'nidreg': '0', 'nidlin': '0', 'chknotc': '0', 'cglosa_2': '0'
        }
        conn.execute(
            text("UPDATE mapeo_subcategorias SET mapeo_cabecera = :m WHERE id = 4"),
            {'m': json.dumps(m)}
        )
        conn.commit()
        print("Updated subcategory 4 mapping for char(1) columns.")

if __name__ == "__main__":
    update_mapping()
