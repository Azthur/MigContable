from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from backend.app.api.api import api_router
from backend.app.core.database import dest_engine
from sqlalchemy import text
import os

import traceback

app = FastAPI(title="SistemaMigConta - Interfaz de Integración Contable")


# ── Middleware: Prevent browser from caching ANY API response ──────────────
class NoCacheAPIMiddleware(BaseHTTPMiddleware):
    """
    Forces Cache-Control: no-store on all /api/ responses so the browser
    never serves stale data from its HTTP cache.
    """
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

app.add_middleware(NoCacheAPIMiddleware)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import sys
    import traceback
    from fastapi.responses import PlainTextResponse
    
    # Try to write traceback to a file to guarantee we see it
    try:
        with open(r"C:\tmp\error_dump.txt", "w", encoding="utf-8") as f:
            f.write(f"GLOBAL EXCEPTION CAUGHT for {request.url}\n")
            f.write(traceback.format_exc())
    except Exception:
        pass
        
    print(f"GLOBAL EXCEPTION CAUGHT for {request.url}:", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    
    return PlainTextResponse(str(exc), status_code=500)

# Mount Static Files
static_path = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_path):
    os.makedirs(static_path)
app.mount("/static", StaticFiles(directory=static_path), name="static")

# Templates
templates_path = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_path)

app.include_router(api_router, prefix="/api/v1")

@app.on_event("startup")
def on_startup():
    # Dynamic DDL check for etl_realtime_logs.subcategorias
    try:
        from backend.app.core.database import dest_engine
        from sqlalchemy import text
        with dest_engine.connect() as conn:
            conn.execute(text("SELECT subcategorias FROM etl_realtime_logs LIMIT 1"))
    except Exception:
        try:
            with dest_engine.begin() as conn:
                conn.execute(text("ALTER TABLE etl_realtime_logs ADD COLUMN subcategorias TEXT"))
                print("Added column subcategorias to etl_realtime_logs table.")
        except Exception as e_ddl:
            print(f"Error adding column to etl_realtime_logs table: {e_ddl}")

    from backend.app.core.scheduler import start_scheduler
    start_scheduler()

@app.on_event("shutdown")
def on_shutdown():
    # from backend.app.core.scheduler import scheduler
    # if scheduler.running:
    #     scheduler.shutdown()
    pass

@app.get("/", response_class=HTMLResponse)
async def read_dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/login", response_class=HTMLResponse)
async def read_login(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")

@app.get("/usuarios", response_class=HTMLResponse)
async def read_usuarios(request: Request):
    return templates.TemplateResponse(request=request, name="usuarios.html")

@app.get("/config", response_class=HTMLResponse)
async def read_config(request: Request):
    return templates.TemplateResponse(request=request, name="config.html")

@app.get("/logs", response_class=HTMLResponse)
async def read_logs(request: Request):
    return templates.TemplateResponse(request=request, name="logs.html")

@app.get("/companies", response_class=HTMLResponse)
async def read_companies(request: Request):
    return templates.TemplateResponse(request=request, name="companies.html")

@app.get("/companies/{company_id}", response_class=HTMLResponse)
async def read_company_detail(request: Request, company_id: int):
    return templates.TemplateResponse(request=request, name="company_detail.html")

@app.get("/automatizaciones", response_class=HTMLResponse)
async def read_automatizaciones(request: Request):
    return templates.TemplateResponse(request=request, name="automatizaciones.html")

@app.get("/etl-realtime", response_class=HTMLResponse)
async def read_etl_realtime(request: Request):
    return templates.TemplateResponse(request=request, name="realtime_etl.html")


@app.get("/tipo-cambio", response_class=HTMLResponse)
async def read_tipo_cambio(request: Request):
    return templates.TemplateResponse(request=request, name="tipo_cambio.html")


@app.get("/catalogos", response_class=HTMLResponse)
async def read_catalogos(request: Request):
    return templates.TemplateResponse(request=request, name="catalogos.html")

@app.get("/mapeo", response_class=HTMLResponse)
async def read_mapeo(request: Request):
    return templates.TemplateResponse(request=request, name="mapeo.html")

@app.get("/mapeo/{subcategoria_id}", response_class=HTMLResponse)
async def read_mapeo_editor(request: Request, subcategoria_id: int):
    return templates.TemplateResponse(request=request, name="mapeo_editor.html")

@app.get("/health")
def health_check():
    return {"Status": "Active", "Message": "SistemaMigConta API is running"}

@app.get("/api/v1/db-status")
def db_status():
    try:
        with dest_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "connected", "message": "PostgreSQL conectado correctamente"}
    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "error", "message": str(e)})

