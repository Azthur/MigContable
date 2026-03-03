from typing import List, Optional, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.core.database import get_dest_db
from backend.app.models.models import UserCatalog, UserCatalogItem, Company
from pydantic import BaseModel
import pandas as pd
import io

router = APIRouter()

# ─── SCHEMAS ──────────────────────────────────────────────────────────────────

class CatalogBase(BaseModel):
    name: str
    description: Optional[str] = None
    columns: List[str]

class CatalogCreate(CatalogBase):
    company_id: int

class CatalogUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    columns: Optional[List[str]] = None

class CatalogItemCreate(BaseModel):
    data: Dict[str, Any]

class CatalogResponse(CatalogBase):
    id: int
    company_id: int
    created_at: Any
    
    class Config:
        orm_mode = True

# ─── ENDPOINTS ────────────────────────────────────────────────────────────────

@router.get("/", response_model=List[CatalogResponse])
def list_catalogs(
    company_id: int,
    db: Session = Depends(get_dest_db),
    skip: int = 0,
    limit: int = 100
):
    """Listar catálogos de una empresa."""
    catalogs = db.query(UserCatalog).filter(UserCatalog.company_id == company_id)\
        .offset(skip).limit(limit).all()
    return catalogs

@router.post("/", response_model=CatalogResponse)
def create_catalog(
    catalog_in: CatalogCreate,
    db: Session = Depends(get_dest_db)
):
    """Crear un nuevo catálogo."""
    # Verificar empresa
    company = db.query(Company).get(catalog_in.company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    # Verificar nombre único per company?
    existing = db.query(UserCatalog).filter(
        UserCatalog.company_id == catalog_in.company_id,
        UserCatalog.name == catalog_in.name
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe un catálogo con este nombre en la empresa")

    db_catalog = UserCatalog(
        company_id=catalog_in.company_id,
        name=catalog_in.name,
        description=catalog_in.description,
        columns=catalog_in.columns
    )
    db.add(db_catalog)
    db.commit()
    db.refresh(db_catalog)
    return db_catalog

@router.put("/{id}", response_model=CatalogResponse)
def update_catalog(
    id: int,
    catalog_in: CatalogUpdate,
    db: Session = Depends(get_dest_db)
):
    """Actualizar catálogo."""
    catalog = db.query(UserCatalog).get(id)
    if not catalog:
        raise HTTPException(status_code=404, detail="Catálogo no encontrado")
    
    if catalog_in.name:
        catalog.name = catalog_in.name
    if catalog_in.description is not None:
        catalog.description = catalog_in.description
    if catalog_in.columns:
        catalog.columns = catalog_in.columns
        
    db.commit()
    db.refresh(catalog)
    return catalog

@router.get("/{id}", response_model=CatalogResponse)
def get_catalog(id: int, db: Session = Depends(get_dest_db)):
    """Obtener detalle de catálogo."""
    catalog = db.query(UserCatalog).get(id)
    if not catalog:
        raise HTTPException(status_code=404, detail="Catálogo no encontrado")
    return catalog

@router.delete("/{id}")
def delete_catalog(id: int, db: Session = Depends(get_dest_db)):
    """Eliminar catálogo y sus items."""
    catalog = db.query(UserCatalog).get(id)
    if not catalog:
        raise HTTPException(status_code=404, detail="Catálogo no encontrado")
    db.delete(catalog)
    db.commit()
    return {"message": "Catálogo eliminado"}

# ─── ITEMS ────────────────────────────────────────────────────────────────────

@router.get("/{id}/items", response_model=List[Dict[str, Any]])
def list_catalog_items(
    id: int,
    db: Session = Depends(get_dest_db),
    skip: int = 0,
    limit: int = 1000
):
    """Listar items (filas) de un catálogo en formato JSON plano."""
    items = db.query(UserCatalogItem).filter(UserCatalogItem.catalog_id == id)\
        .offset(skip).limit(limit).all()
    # Retornamos solo la data, tal vez deberíamos incluir el ID del item si queremos editar
    # Por uniformidad, retornamos una lista de diccionarios, inyectando '_id' si es util
    return [{**item.data, "_id": item.id} for item in items]

@router.post("/{id}/items")
def add_catalog_item(
    id: int,
    item_in: CatalogItemCreate,
    db: Session = Depends(get_dest_db)
):
    """Agregar un item manual."""
    catalog = db.query(UserCatalog).get(id)
    if not catalog:
        raise HTTPException(status_code=404, detail="Catálogo no encontrado")
    
    db_item = UserCatalogItem(catalog_id=id, data=item_in.data)
    db.add(db_item)
    db.commit()
    return {"message": "Item agregado", "id": db_item.id}

@router.put("/{id}/items/{item_id}")
def update_catalog_item(
    id: int,
    item_id: int,
    item_in: CatalogItemCreate,
    db: Session = Depends(get_dest_db)
):
    """Actualizar un item existente."""
    item = db.query(UserCatalogItem).filter(
        UserCatalogItem.catalog_id == id,
        UserCatalogItem.id == item_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    
    item.data = item_in.data
    db.commit()
    return {"message": "Item actualizado"}

@router.delete("/{id}/items/{item_id}")
def delete_catalog_item(
    id: int,
    item_id: int,
    db: Session = Depends(get_dest_db)
):
    """Eliminar un item existente."""
    item = db.query(UserCatalogItem).filter(
        UserCatalogItem.catalog_id == id,
        UserCatalogItem.id == item_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    
    db.delete(item)
    db.commit()
    return {"message": "Item eliminado"}

@router.post("/{id}/upload")
async def upload_catalog_items(
    id: int,
    file: UploadFile = File(...),
    mode: str = Form("replace"), # replace | append
    db: Session = Depends(get_dest_db)
):
    """
    Subir archivo CSV/Excel para poblar el catálogo.
    Mode: 'replace' borra todo lo anterior. 'append' agrega.
    """
    catalog = db.query(UserCatalog).get(id)
    if not catalog:
        raise HTTPException(status_code=404, detail="Catálogo no encontrado")

    # Leer archivo
    contents = await file.read()
    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        elif file.filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            raise HTTPException(status_code=400, detail="Formato no soportado. Use CSV o Excel.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error leyendo archivo: {str(e)}")

    # Validar columnas (opcional: solo advertencia, o estricto)
    # Por flexibilidad, aceptamos lo que venga, pero idealmente debe coincidir con catalog.columns
    # Ajustamos catalog.columns si es replace? No, el usuario define estructura.
    # Convertimos DF a lista de dicts
    records = df.to_dict(orient='records')

    # Limpiar NaN
    clean_records = []
    for r in records:
        clean_r = {k: (v if pd.notna(v) else None) for k, v in r.items()}
        clean_records.append(clean_r)

    if mode == 'replace':
        db.query(UserCatalogItem).filter(UserCatalogItem.catalog_id == id).delete()
    
    # Bulk insert
    db.bulk_save_objects([
        UserCatalogItem(catalog_id=id, data=r) for r in clean_records
    ])
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error guardando datos: {str(e)}")

    return {"message": f"Procesados {len(clean_records)} registros", "total": len(clean_records)}
