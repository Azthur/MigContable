from fastapi import APIRouter
from backend.app.api.endpoints import config, etl, logs, companies, catalogos, mapeo, tipo_cambio, catalogs

api_router = APIRouter()
api_router.include_router(config.router, prefix="/config", tags=["Configuration"])
api_router.include_router(etl.router, prefix="/etl", tags=["ETL Operations"])
api_router.include_router(logs.router, prefix="/logs", tags=["Logs"])
api_router.include_router(companies.router, prefix="/companies", tags=["Companies"])
api_router.include_router(catalogos.router, prefix="/catalogos", tags=["Catálogos Contables"])
api_router.include_router(mapeo.router, prefix="/mapeo", tags=["Mapeo Contable"])
api_router.include_router(tipo_cambio.router, prefix="/tipo-cambio", tags=["Tipo de Cambio"])
api_router.include_router(catalogs.router, prefix="/catalogs", tags=["Catálogos Dinámicos"])
