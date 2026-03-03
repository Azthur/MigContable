from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.core.config import get_settings
from backend.app.api.endpoints.mapeo import _generate_subcategoria_cf_diariol
from backend.app.models.models import MapeoSubcategoria
import json

def debug_generation():
    settings = get_settings()
    engine = create_engine(settings.POSTGRES_CONNECTION_STRING)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        sub = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.id == 4).first()
        if not sub:
            print("Sub 4 not found")
            return
            
        print(f"Subcategoria: {sub.nombre}")
        print(f"Col Nasiento: {sub.col_destino_nasiento}")
        print(f"Col Nidlin: {sub.col_destino_nidlin}")
        
        # Simulate generation for a small sample
        # We need a dataframe. Let's get it from the intermediate DB if possible, or mock it.
        # For now, let's just inspect the code's data structures by running it partially.
        # Actually, let's look at the mapping logic one more time.
        
        for linea in sub.lineas_asiento:
            print(f"\nLine ID {linea.id} ({linea.orden}):")
            print(f"  Level: {linea.nivel}")
            keys = list(linea.mapeo_detalle.keys())
            print(f"  Mapping keys: {keys}")
            
    finally:
        db.close()

if __name__ == "__main__":
    debug_generation()
