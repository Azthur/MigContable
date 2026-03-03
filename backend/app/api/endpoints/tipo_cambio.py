"""
Endpoints para Tipo de Cambio SUNAT.
- Sincronización mensual y diaria desde api.org.pe
- CRUD para consultar tipos de cambio
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date, datetime
from typing import Optional
import httpx

from backend.app.core.database import get_dest_db
from backend.app.models.models import TipoCambio

router = APIRouter()

# Token para api.org.pe
TC_API_TOKEN = "ebf3feafb06f11f09f1d005056563c20"
TC_API_BASE = "https://api.org.pe/v1"


@router.get("")
def list_tipo_cambio(
    year: Optional[int] = None,
    month: Optional[int] = None,
    db: Session = Depends(get_dest_db)
):
    """Lista tipos de cambio, opcionalmente filtrado por año-mes"""
    query = db.query(TipoCambio).order_by(TipoCambio.fecha.desc())
    
    if year and month:
        from sqlalchemy import extract
        query = query.filter(
            extract('year', TipoCambio.fecha) == year,
            extract('month', TipoCambio.fecha) == month
        )
    
    rows = query.limit(400).all()
    return [{
        "id": r.id,
        "fecha": str(r.fecha),
        "compra": float(r.compra),
        "venta": float(r.venta),
        "source": r.source
    } for r in rows]


@router.get("/{fecha_str}")
def get_tipo_cambio(fecha_str: str, db: Session = Depends(get_dest_db)):
    """Obtiene TC de una fecha específica (formato YYYY-MM-DD)"""
    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido. Use YYYY-MM-DD")
    
    tc = db.query(TipoCambio).filter(TipoCambio.fecha == fecha).first()
    if not tc:
        raise HTTPException(status_code=404, detail=f"No hay tipo de cambio para {fecha_str}")
    
    return {
        "fecha": str(tc.fecha),
        "compra": float(tc.compra),
        "venta": float(tc.venta)
    }


@router.post("/sync-month")
def sync_month(body: dict, db: Session = Depends(get_dest_db)):
    """Sincroniza TC de un mes completo desde api.org.pe.
    Body: {"year_month": "2026-02"}
    """
    year_month = body.get("year_month", "")
    if not year_month:
        raise HTTPException(status_code=400, detail="Se requiere year_month (ej: 2026-02)")
    
    url = f"{TC_API_BASE}/tcmes/{year_month}"
    headers = {"Authorization": f"Bearer {TC_API_TOKEN}"}
    
    try:
        with httpx.Client(timeout=15) as client:
            resp = client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Error API externa: {e.response.status_code}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error conectando a api.org.pe: {str(e)}")
    
    if not data.get("success"):
        raise HTTPException(status_code=502, detail=data.get("message", "Error desconocido de API"))
    
    records = data.get("data", [])
    inserted = 0
    updated = 0
    
    for item in records:
        fecha = datetime.strptime(item["fecha"], "%Y-%m-%d").date()
        compra = item["compra"]
        venta = item["venta"]
        
        existing = db.query(TipoCambio).filter(TipoCambio.fecha == fecha).first()
        if existing:
            existing.compra = compra
            existing.venta = venta
            existing.source = "api.org.pe"
            updated += 1
        else:
            tc = TipoCambio(fecha=fecha, compra=compra, venta=venta, source="api.org.pe")
            db.add(tc)
            inserted += 1
    
    db.commit()
    return {
        "message": f"Sincronizado {year_month}: {inserted} nuevos, {updated} actualizados",
        "inserted": inserted,
        "updated": updated,
        "total": len(records)
    }


@router.post("/sync-today")
def sync_today(db: Session = Depends(get_dest_db)):
    """Sincroniza TC del día de hoy desde api.org.pe"""
    today = date.today().strftime("%Y-%m-%d")
    url = f"{TC_API_BASE}/tc/{today}"
    headers = {"Authorization": f"Bearer {TC_API_TOKEN}"}
    
    try:
        with httpx.Client(timeout=15) as client:
            resp = client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Error API externa: {e.response.status_code}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error conectando a api.org.pe: {str(e)}")
    
    if not data.get("success"):
        raise HTTPException(status_code=502, detail=data.get("message", "Error desconocido"))
    
    item = data.get("data", {})
    if not item:
        raise HTTPException(status_code=404, detail="Sin datos para hoy")
    
    fecha = datetime.strptime(item["fecha"], "%Y-%m-%d").date()
    existing = db.query(TipoCambio).filter(TipoCambio.fecha == fecha).first()
    
    if existing:
        existing.compra = item["compra"]
        existing.venta = item["venta"]
        existing.source = "api.org.pe"
        action = "actualizado"
    else:
        tc = TipoCambio(fecha=fecha, compra=item["compra"], venta=item["venta"], source="api.org.pe")
        db.add(tc)
        action = "insertado"
    
    db.commit()
    return {
        "message": f"TC {today}: Compra={item['compra']}, Venta={item['venta']} ({action})",
        "fecha": today,
        "compra": item["compra"],
        "venta": item["venta"]
    }
