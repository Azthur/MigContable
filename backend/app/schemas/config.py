from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Shared properties
class AccountMappingBase(BaseModel):
    source_account_code: str
    source_account_name: Optional[str] = None
    dest_account_code: str
    dest_cost_center: Optional[str] = None
    is_active: bool = True

# Properties to receive on creation
class AccountMappingCreate(AccountMappingBase):
    pass

# Properties to return to client
class AccountMapping(AccountMappingBase):
    id: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class DocumentMappingBase(BaseModel):
    source_doc_type: str
    dest_doc_type: str
    description: Optional[str] = None
    is_active: bool = True

class DocumentMappingCreate(DocumentMappingBase):
    pass

class DocumentMapping(DocumentMappingBase):
    id: int

    class Config:
        from_attributes = True
