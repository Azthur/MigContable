"""
Endpoints para gestión de catálogos contables:
- Cuentas Contables
- Cuentas Presupuesto
- Centros de Costo
- Tipo Analítica
- Productos
- Tipos de Movimiento
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app.core.database import get_dest_db
from backend.app.models.models import (
    CatCuentaContable, CatCuentaPresupuesto, CatCentroCosto,
    CatTipoAnalitica, CatProducto, CatTipoMovimiento
)
from backend.app.schemas.company import (
    CatCuentaContableCreate, CatCuentaContableSchema,
    CatCuentaPresupuestoCreate, CatCuentaPresupuestoSchema,
    CatCentroCostoCreate, CatCentroCostoSchema,
    CatTipoAnaliticaCreate, CatTipoAnaliticaSchema,
    CatProductoCreate, CatProductoSchema,
    CatTipoMovimientoCreate, CatTipoMovimientoSchema,
)

router = APIRouter()


# ─── Cuentas Contables ────────────────────────────────────────────────────────

@router.get("/cuentas-contables", response_model=List[CatCuentaContableSchema])
def list_cuentas(company_id: Optional[int] = None, q: Optional[str] = None,
                 skip: int = 0, limit: int = 200, db: Session = Depends(get_dest_db)):
    query = db.query(CatCuentaContable).filter(CatCuentaContable.is_active == True)
    if company_id:
        query = query.filter(
            (CatCuentaContable.company_id == company_id) | (CatCuentaContable.company_id == None)
        )
    if q:
        query = query.filter(
            CatCuentaContable.codigo.ilike(f"%{q}%") | CatCuentaContable.descripcion.ilike(f"%{q}%")
        )
    return query.order_by(CatCuentaContable.codigo).offset(skip).limit(limit).all()

@router.post("/cuentas-contables", response_model=CatCuentaContableSchema)
def create_cuenta(item: CatCuentaContableCreate, db: Session = Depends(get_dest_db)):
    db_item = CatCuentaContable(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.put("/cuentas-contables/{item_id}", response_model=CatCuentaContableSchema)
def update_cuenta(item_id: int, item: CatCuentaContableCreate, db: Session = Depends(get_dest_db)):
    db_item = db.query(CatCuentaContable).filter(CatCuentaContable.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    for k, v in item.model_dump().items():
        setattr(db_item, k, v)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.delete("/cuentas-contables/{item_id}")
def delete_cuenta(item_id: int, db: Session = Depends(get_dest_db)):
    db_item = db.query(CatCuentaContable).filter(CatCuentaContable.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    db_item.is_active = False
    db.commit()
    return {"message": "Eliminado"}

@router.post("/cuentas-contables/bulk")
def bulk_import_cuentas(items: List[CatCuentaContableCreate], db: Session = Depends(get_dest_db)):
    """Importación masiva de cuentas contables"""
    created = 0
    for item in items:
        existing = db.query(CatCuentaContable).filter(
            CatCuentaContable.codigo == item.codigo,
            CatCuentaContable.company_id == item.company_id
        ).first()
        if existing:
            for k, v in item.model_dump().items():
                setattr(existing, k, v)
        else:
            db.add(CatCuentaContable(**item.model_dump()))
            created += 1
    db.commit()
    return {"message": f"Importados {created} registros nuevos"}


# ─── Cuentas Presupuesto ──────────────────────────────────────────────────────

@router.get("/cuentas-presupuesto", response_model=List[CatCuentaPresupuestoSchema])
def list_presupuesto(company_id: Optional[int] = None, q: Optional[str] = None,
                     skip: int = 0, limit: int = 200, db: Session = Depends(get_dest_db)):
    query = db.query(CatCuentaPresupuesto).filter(CatCuentaPresupuesto.is_active == True)
    if company_id:
        query = query.filter(
            (CatCuentaPresupuesto.company_id == company_id) | (CatCuentaPresupuesto.company_id == None)
        )
    if q:
        query = query.filter(
            CatCuentaPresupuesto.codigo.ilike(f"%{q}%") | CatCuentaPresupuesto.descripcion.ilike(f"%{q}%")
        )
    return query.order_by(CatCuentaPresupuesto.codigo).offset(skip).limit(limit).all()

@router.post("/cuentas-presupuesto", response_model=CatCuentaPresupuestoSchema)
def create_presupuesto(item: CatCuentaPresupuestoCreate, db: Session = Depends(get_dest_db)):
    db_item = CatCuentaPresupuesto(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.put("/cuentas-presupuesto/{item_id}", response_model=CatCuentaPresupuestoSchema)
def update_presupuesto(item_id: int, item: CatCuentaPresupuestoCreate, db: Session = Depends(get_dest_db)):
    db_item = db.query(CatCuentaPresupuesto).filter(CatCuentaPresupuesto.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="No encontrado")
    for k, v in item.model_dump().items():
        setattr(db_item, k, v)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.delete("/cuentas-presupuesto/{item_id}")
def delete_presupuesto(item_id: int, db: Session = Depends(get_dest_db)):
    db_item = db.query(CatCuentaPresupuesto).filter(CatCuentaPresupuesto.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="No encontrado")
    db_item.is_active = False
    db.commit()
    return {"message": "Eliminado"}


# ─── Centros de Costo ─────────────────────────────────────────────────────────

@router.get("/centros-costo", response_model=List[CatCentroCostoSchema])
def list_centros(company_id: Optional[int] = None, q: Optional[str] = None,
                 skip: int = 0, limit: int = 200, db: Session = Depends(get_dest_db)):
    query = db.query(CatCentroCosto).filter(CatCentroCosto.is_active == True)
    if company_id:
        query = query.filter(
            (CatCentroCosto.company_id == company_id) | (CatCentroCosto.company_id == None)
        )
    if q:
        query = query.filter(
            CatCentroCosto.codigo.ilike(f"%{q}%") | CatCentroCosto.descripcion.ilike(f"%{q}%")
        )
    return query.order_by(CatCentroCosto.codigo).offset(skip).limit(limit).all()

@router.post("/centros-costo", response_model=CatCentroCostoSchema)
def create_centro(item: CatCentroCostoCreate, db: Session = Depends(get_dest_db)):
    db_item = CatCentroCosto(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.put("/centros-costo/{item_id}", response_model=CatCentroCostoSchema)
def update_centro(item_id: int, item: CatCentroCostoCreate, db: Session = Depends(get_dest_db)):
    db_item = db.query(CatCentroCosto).filter(CatCentroCosto.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="No encontrado")
    for k, v in item.model_dump().items():
        setattr(db_item, k, v)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.delete("/centros-costo/{item_id}")
def delete_centro(item_id: int, db: Session = Depends(get_dest_db)):
    db_item = db.query(CatCentroCosto).filter(CatCentroCosto.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="No encontrado")
    db_item.is_active = False
    db.commit()
    return {"message": "Eliminado"}


# ─── Tipo Analítica ───────────────────────────────────────────────────────────

@router.get("/tipo-analitica", response_model=List[CatTipoAnaliticaSchema])
def list_analitica(company_id: Optional[int] = None, q: Optional[str] = None,
                   db: Session = Depends(get_dest_db)):
    query = db.query(CatTipoAnalitica).filter(CatTipoAnalitica.is_active == True)
    if company_id:
        query = query.filter(
            (CatTipoAnalitica.company_id == company_id) | (CatTipoAnalitica.company_id == None)
        )
    if q:
        query = query.filter(
            CatTipoAnalitica.codigo.ilike(f"%{q}%") | CatTipoAnalitica.descripcion.ilike(f"%{q}%")
        )
    return query.order_by(CatTipoAnalitica.codigo).all()

@router.post("/tipo-analitica", response_model=CatTipoAnaliticaSchema)
def create_analitica(item: CatTipoAnaliticaCreate, db: Session = Depends(get_dest_db)):
    db_item = CatTipoAnalitica(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.put("/tipo-analitica/{item_id}", response_model=CatTipoAnaliticaSchema)
def update_analitica(item_id: int, item: CatTipoAnaliticaCreate, db: Session = Depends(get_dest_db)):
    db_item = db.query(CatTipoAnalitica).filter(CatTipoAnalitica.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="No encontrado")
    for k, v in item.model_dump().items():
        setattr(db_item, k, v)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.delete("/tipo-analitica/{item_id}")
def delete_analitica(item_id: int, db: Session = Depends(get_dest_db)):
    db_item = db.query(CatTipoAnalitica).filter(CatTipoAnalitica.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="No encontrado")
    db_item.is_active = False
    db.commit()
    return {"message": "Eliminado"}


# ─── Productos ────────────────────────────────────────────────────────────────

@router.get("/productos", response_model=List[CatProductoSchema])
def list_productos(company_id: Optional[int] = None, q: Optional[str] = None,
                   skip: int = 0, limit: int = 200, db: Session = Depends(get_dest_db)):
    query = db.query(CatProducto).filter(CatProducto.is_active == True)
    if company_id:
        query = query.filter(
            (CatProducto.company_id == company_id) | (CatProducto.company_id == None)
        )
    if q:
        query = query.filter(
            CatProducto.codigo.ilike(f"%{q}%") | CatProducto.descripcion.ilike(f"%{q}%")
        )
    return query.order_by(CatProducto.codigo).offset(skip).limit(limit).all()

@router.post("/productos", response_model=CatProductoSchema)
def create_producto(item: CatProductoCreate, db: Session = Depends(get_dest_db)):
    db_item = CatProducto(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.put("/productos/{item_id}", response_model=CatProductoSchema)
def update_producto(item_id: int, item: CatProductoCreate, db: Session = Depends(get_dest_db)):
    db_item = db.query(CatProducto).filter(CatProducto.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="No encontrado")
    for k, v in item.model_dump().items():
        setattr(db_item, k, v)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.delete("/productos/{item_id}")
def delete_producto(item_id: int, db: Session = Depends(get_dest_db)):
    db_item = db.query(CatProducto).filter(CatProducto.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="No encontrado")
    db_item.is_active = False
    db.commit()
    return {"message": "Eliminado"}


# ─── Tipos de Movimiento ──────────────────────────────────────────────────────

@router.get("/tipos-movimiento", response_model=List[CatTipoMovimientoSchema])
def list_tipos_mov(company_id: Optional[int] = None, q: Optional[str] = None,
                   db: Session = Depends(get_dest_db)):
    query = db.query(CatTipoMovimiento).filter(CatTipoMovimiento.is_active == True)
    if company_id:
        query = query.filter(
            (CatTipoMovimiento.company_id == company_id) | (CatTipoMovimiento.company_id == None)
        )
    if q:
        query = query.filter(
            CatTipoMovimiento.codigo.ilike(f"%{q}%") | CatTipoMovimiento.descripcion.ilike(f"%{q}%")
        )
    return query.order_by(CatTipoMovimiento.codigo).all()

@router.post("/tipos-movimiento", response_model=CatTipoMovimientoSchema)
def create_tipo_mov(item: CatTipoMovimientoCreate, db: Session = Depends(get_dest_db)):
    db_item = CatTipoMovimiento(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.put("/tipos-movimiento/{item_id}", response_model=CatTipoMovimientoSchema)
def update_tipo_mov(item_id: int, item: CatTipoMovimientoCreate, db: Session = Depends(get_dest_db)):
    db_item = db.query(CatTipoMovimiento).filter(CatTipoMovimiento.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="No encontrado")
    for k, v in item.model_dump().items():
        setattr(db_item, k, v)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.delete("/tipos-movimiento/{item_id}")
def delete_tipo_mov(item_id: int, db: Session = Depends(get_dest_db)):
    db_item = db.query(CatTipoMovimiento).filter(CatTipoMovimiento.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="No encontrado")
    db_item.is_active = False
    db.commit()
    return {"message": "Eliminado"}
