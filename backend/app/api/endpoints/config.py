from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from backend.app.core.database import get_dest_db
from backend.app.models.models import AccountMapping, DocumentTypeMapping
from backend.app.schemas.config import (
    AccountMapping as AccountMappingSchema,
    AccountMappingCreate,
    DocumentMapping as DocumentMappingSchema,
    DocumentMappingCreate
)

router = APIRouter()

# ─── Account Mappings ───────────────────────────────────────────────────────

@router.post("/accounts/", response_model=AccountMappingSchema)
def create_account_mapping(mapping: AccountMappingCreate, db: Session = Depends(get_dest_db)):
    db_mapping = db.query(AccountMapping).filter(AccountMapping.source_account_code == mapping.source_account_code).first()
    if db_mapping:
        raise HTTPException(status_code=400, detail="Account mapping already exists")
    new_mapping = AccountMapping(**mapping.model_dump())
    db.add(new_mapping)
    db.commit()
    db.refresh(new_mapping)
    return new_mapping

@router.get("/accounts/", response_model=List[AccountMappingSchema])
def read_account_mappings(skip: int = 0, limit: int = 100, db: Session = Depends(get_dest_db)):
    return db.query(AccountMapping).offset(skip).limit(limit).all()

@router.put("/accounts/{mapping_id}", response_model=AccountMappingSchema)
def update_account_mapping(mapping_id: int, mapping: AccountMappingCreate, db: Session = Depends(get_dest_db)):
    db_mapping = db.query(AccountMapping).filter(AccountMapping.id == mapping_id).first()
    if not db_mapping:
        raise HTTPException(status_code=404, detail="Account mapping not found")
    for key, value in mapping.model_dump().items():
        setattr(db_mapping, key, value)
    db.commit()
    db.refresh(db_mapping)
    return db_mapping

@router.delete("/accounts/{mapping_id}")
def delete_account_mapping(mapping_id: int, db: Session = Depends(get_dest_db)):
    db_mapping = db.query(AccountMapping).filter(AccountMapping.id == mapping_id).first()
    if not db_mapping:
        raise HTTPException(status_code=404, detail="Account mapping not found")
    db.delete(db_mapping)
    db.commit()
    return {"message": "Deleted successfully"}

# ─── Document Type Mappings ──────────────────────────────────────────────────

@router.post("/documents/", response_model=DocumentMappingSchema)
def create_document_mapping(mapping: DocumentMappingCreate, db: Session = Depends(get_dest_db)):
    db_mapping = db.query(DocumentTypeMapping).filter(DocumentTypeMapping.source_doc_type == mapping.source_doc_type).first()
    if db_mapping:
        raise HTTPException(status_code=400, detail="Document mapping already exists")
    new_mapping = DocumentTypeMapping(**mapping.model_dump())
    db.add(new_mapping)
    db.commit()
    db.refresh(new_mapping)
    return new_mapping

@router.get("/documents/", response_model=List[DocumentMappingSchema])
def read_document_mappings(skip: int = 0, limit: int = 100, db: Session = Depends(get_dest_db)):
    return db.query(DocumentTypeMapping).offset(skip).limit(limit).all()

@router.put("/documents/{mapping_id}", response_model=DocumentMappingSchema)
def update_document_mapping(mapping_id: int, mapping: DocumentMappingCreate, db: Session = Depends(get_dest_db)):
    db_mapping = db.query(DocumentTypeMapping).filter(DocumentTypeMapping.id == mapping_id).first()
    if not db_mapping:
        raise HTTPException(status_code=404, detail="Document mapping not found")
    for key, value in mapping.model_dump().items():
        setattr(db_mapping, key, value)
    db.commit()
    db.refresh(db_mapping)
    return db_mapping

@router.delete("/documents/{mapping_id}")
def delete_document_mapping(mapping_id: int, db: Session = Depends(get_dest_db)):
    db_mapping = db.query(DocumentTypeMapping).filter(DocumentTypeMapping.id == mapping_id).first()
    if not db_mapping:
        raise HTTPException(status_code=404, detail="Document mapping not found")
    db.delete(db_mapping)
    db.commit()
    return {"message": "Deleted successfully"}
