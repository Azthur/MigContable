from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from backend.app.core.config import get_settings
from backend.app.models.models import MapeoSubcategoria

def update_sub():
    settings = get_settings()
    engine = create_engine(settings.POSTGRES_CONNECTION_STRING)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        sub = session.query(MapeoSubcategoria).filter(MapeoSubcategoria.id == 4).first()
        if sub:
            print(f"Before: {sub.col_destino_nasiento}, {sub.col_destino_nidlin}")
            sub.col_destino_nasiento = "nasiento"
            sub.col_destino_nidlin = "nidlin"
            session.commit()
            print("Committed.")
            
            session.refresh(sub)
            print(f"After: {sub.col_destino_nasiento}, {sub.col_destino_nidlin}")
        else:
            print("Sub 4 not found.")
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    update_sub()
