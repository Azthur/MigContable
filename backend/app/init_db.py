from backend.app.core.database import dest_engine, DestBase
from backend.app.models.models import AccountMapping, DocumentTypeMapping, TransformationRule, IntegLog

def init_db():
    print("Creando tablas en la base de datos de destino...")
    DestBase.metadata.create_all(bind=dest_engine)
    print("Tablas creadas exitosamente.")

if __name__ == "__main__":
    init_db()
