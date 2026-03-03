from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


# ─── Company ─────────────────────────────────────────────────────────────────

class CompanyBase(BaseModel):
    name: str
    ruc: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True

class CompanyCreate(CompanyBase):
    pass

class CompanySchema(CompanyBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    class Config:
        from_attributes = True


# ─── Source Connection ────────────────────────────────────────────────────────

class SourceConnectionBase(BaseModel):
    db_type: str = "MSSQL"
    host: str
    port: int = 1433
    database_name: str
    username: str
    password: str
    driver: str = "ODBC Driver 17 for SQL Server"
    extra_params: Optional[str] = None
    is_active: bool = True

class SourceConnectionCreate(SourceConnectionBase):
    pass

class SourceConnectionSchema(BaseModel):
    id: int
    company_id: int
    db_type: str
    host: str
    port: int
    database_name: str
    username: str
    driver: str
    is_active: bool
    last_tested_at: Optional[datetime] = None
    last_test_status: Optional[str] = None
    last_test_message: Optional[str] = None
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True


# ─── Destination Connection ───────────────────────────────────────────────────

class DestConnectionBase(BaseModel):
    host: str = "localhost"
    port: int = 5433
    database_name: str
    username: str = "postgres"
    password: str
    is_active: bool = True

class DestConnectionCreate(DestConnectionBase):
    pass

class DestConnectionSchema(BaseModel):
    id: int
    company_id: int
    host: str
    port: int
    database_name: str
    username: str
    is_active: bool
    last_tested_at: Optional[datetime] = None
    last_test_status: Optional[str] = None
    last_test_message: Optional[str] = None
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True


# ─── Table Selection ──────────────────────────────────────────────────────────

class TableSelectionBase(BaseModel):
    table_schema: str = "dbo"
    table_name: str
    is_selected: bool = False
    extraction_order: int = 0
    custom_query: Optional[str] = None
    date_column: Optional[str] = None
    control_column: Optional[str] = None
    control_column_type: str = "DATE"
    description: Optional[str] = None

class TableSelectionCreate(TableSelectionBase):
    source_connection_id: int

class TableSelectionSchema(TableSelectionBase):
    id: int
    company_id: int
    source_connection_id: int
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class TableSelectionBulkUpdate(BaseModel):
    """Para actualizar múltiples tablas seleccionadas a la vez"""
    source_connection_id: int
    selections: List[dict]


# ─── Column Filter ────────────────────────────────────────────────────────────

class ColumnFilterBase(BaseModel):
    column_name: str
    operator: str  # =, >, <, >=, <=, LIKE, IN, BETWEEN, IS NULL, IS NOT NULL
    filter_value: Optional[str] = None
    filter_value2: Optional[str] = None
    is_active: bool = True

class ColumnFilterCreate(ColumnFilterBase):
    table_selection_id: int

class ColumnFilterSchema(ColumnFilterBase):
    id: int
    table_selection_id: int
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class ColumnFilterBulkUpdate(BaseModel):
    """Para guardar todos los filtros de una tabla de una vez"""
    table_selection_id: int
    filters: List[ColumnFilterBase]


# ─── Migration Control ────────────────────────────────────────────────────────

class MigrationControlSchema(BaseModel):
    id: int
    company_id: int
    source_table: str
    control_column: Optional[str] = None
    last_migrated_value: Optional[str] = None
    total_migrated: int = 0
    last_run_at: Optional[datetime] = None
    last_run_status: Optional[str] = None
    last_run_message: Optional[str] = None
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True


# ─── Final Destination Connection (Contabilidad) ─────────────────────────────

class FinalDestConnectionBase(BaseModel):
    db_type: str = "POSTGRESQL"
    host: str = "localhost"
    port: int = 5432
    database_name: str
    username: str = "postgres"
    password: str
    target_table: Optional[str] = None
    target_schema: str = "public"
    is_active: bool = True

class FinalDestConnectionCreate(FinalDestConnectionBase):
    pass

class FinalDestConnectionSchema(BaseModel):
    id: int
    company_id: int
    db_type: str
    host: str
    port: int
    database_name: str
    username: str
    target_table: Optional[str] = None
    target_schema: str = "public"
    is_active: bool
    last_tested_at: Optional[datetime] = None
    last_test_status: Optional[str] = None
    last_test_message: Optional[str] = None
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class FinalTableSelectionBulkUpdate(BaseModel):
    """Para actualizar tablas destino seleccionadas"""
    final_dest_connection_id: int
    selections: List[dict]


# ─── Catálogos Contables ──────────────────────────────────────────────────────

class CatCuentaContableBase(BaseModel):
    codigo: str
    descripcion: str
    tipo: Optional[str] = None
    nivel: int = 1
    moneda: str = "MN"
    is_active: bool = True
    company_id: Optional[int] = None

class CatCuentaContableCreate(CatCuentaContableBase):
    pass

class CatCuentaContableSchema(CatCuentaContableBase):
    id: int
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True


class CatCuentaPresupuestoBase(BaseModel):
    codigo: str
    descripcion: str
    is_active: bool = True
    company_id: Optional[int] = None

class CatCuentaPresupuestoCreate(CatCuentaPresupuestoBase):
    pass

class CatCuentaPresupuestoSchema(CatCuentaPresupuestoBase):
    id: int
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True


class CatCentroCostoBase(BaseModel):
    codigo: str
    descripcion: str
    is_active: bool = True
    company_id: Optional[int] = None

class CatCentroCostoCreate(CatCentroCostoBase):
    pass

class CatCentroCostoSchema(CatCentroCostoBase):
    id: int
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True


class CatTipoAnaliticaBase(BaseModel):
    codigo: str
    descripcion: str
    is_active: bool = True
    company_id: Optional[int] = None

class CatTipoAnaliticaCreate(CatTipoAnaliticaBase):
    pass

class CatTipoAnaliticaSchema(CatTipoAnaliticaBase):
    id: int
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True


class CatProductoBase(BaseModel):
    codigo: str
    descripcion: str
    unidad: Optional[str] = None
    is_active: bool = True
    company_id: Optional[int] = None

class CatProductoCreate(CatProductoBase):
    pass

class CatProductoSchema(CatProductoBase):
    id: int
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True


class CatTipoMovimientoBase(BaseModel):
    codigo: str
    descripcion: str
    is_active: bool = True
    company_id: Optional[int] = None

class CatTipoMovimientoCreate(CatTipoMovimientoBase):
    pass

class CatTipoMovimientoSchema(CatTipoMovimientoBase):
    id: int
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True


# ─── Mapeo Contable ───────────────────────────────────────────────────────────

class MapeoLineaAsientoBase(BaseModel):
    orden: int = 0
    nombre_linea: Optional[str] = None
    mapeo_detalle: Optional[dict] = None
    condicion_aplicacion: Optional[str] = None
    nivel: str = "DETALLE"
    is_active: bool = True

class MapeoLineaAsientoCreate(MapeoLineaAsientoBase):
    subcategoria_id: int

class MapeoLineaAsientoSchema(MapeoLineaAsientoBase):
    id: int
    subcategoria_id: int
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True


class MapeoSubcategoriaBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    tabla_origen: Optional[str] = None
    codigo_origen: Optional[str] = None
    clave_asiento: Optional[str] = None
    mapeo_cabecera: Optional[dict] = None
    tabla_destino_detalle: Optional[str] = None
    tabla_destino_cabecera: Optional[str] = None
    col_destino_nasiento: Optional[str] = None
    col_destino_nidlin: Optional[str] = None
    generate_headers: bool = True
    generate_details: bool = True
    schema_destino: Optional[str] = "public"
    filter_rules: Optional[List[dict]] = None
    is_active: bool = True

class MapeoSubcategoriaCreate(MapeoSubcategoriaBase):
    categoria_id: int

class MapeoSubcategoriaUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    tabla_origen: Optional[str] = None
    codigo_origen: Optional[str] = None
    clave_asiento: Optional[str] = None
    mapeo_cabecera: Optional[dict] = None
    tabla_destino_detalle: Optional[str] = None
    tabla_destino_cabecera: Optional[str] = None
    col_destino_nasiento: Optional[str] = None
    col_destino_nidlin: Optional[str] = None
    generate_headers: Optional[bool] = None
    generate_details: Optional[bool] = None
    schema_destino: Optional[str] = None
    filter_rules: Optional[List[dict]] = None
    is_active: Optional[bool] = None
    categoria_id: Optional[int] = None

class MapeoSubcategoriaSchema(MapeoSubcategoriaBase):
    id: int
    categoria_id: int
    company_id: Optional[int] = None
    lineas_asiento: List[MapeoLineaAsientoSchema] = []
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True


class MapeoCategoriaBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    is_active: bool = True

class MapeoCategoriaCreate(MapeoCategoriaBase):
    company_id: int

class MapeoCategoriaSchema(MapeoCategoriaBase):
    id: int
    company_id: int
    subcategorias: List[MapeoSubcategoriaSchema] = []
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True


# ─── Account Mapping (legacy) ────────────────────────────────────────────────

class AccountMappingBase(BaseModel):
    source_account_code: str
    source_account_name: Optional[str] = None
    dest_account_code: str
    dest_cost_center: Optional[str] = None
    is_active: bool = True
    company_id: Optional[int] = None

class AccountMappingCreate(AccountMappingBase):
    pass

class AccountMapping(AccountMappingBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    class Config:
        from_attributes = True


# ─── Document Mapping (legacy) ───────────────────────────────────────────────

class DocumentMappingBase(BaseModel):
    source_doc_type: str
    dest_doc_type: str
    description: Optional[str] = None
    is_active: bool = True
    company_id: Optional[int] = None

class DocumentMappingCreate(DocumentMappingBase):
    pass

class DocumentMapping(DocumentMappingBase):
    id: int
    class Config:
        from_attributes = True
