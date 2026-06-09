from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from backend.app.api.api import api_router
from backend.app.core.database import dest_engine
from sqlalchemy import text
import os

import traceback

app = FastAPI(title="SistemaMigConta - Interfaz de Integración Contable")

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
    from backend.app.core.scheduler import start_scheduler
    start_scheduler()

@app.on_event("shutdown")
def on_shutdown():
    from backend.app.core.scheduler import scheduler
    if scheduler.running:
        scheduler.shutdown()

@app.get("/", response_class=HTMLResponse)
async def read_dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def read_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/usuarios", response_class=HTMLResponse)
async def read_usuarios(request: Request):
    return templates.TemplateResponse("usuarios.html", {"request": request})

@app.get("/config", response_class=HTMLResponse)
async def read_config(request: Request):
    return templates.TemplateResponse("config.html", {"request": request})

@app.get("/logs", response_class=HTMLResponse)
async def read_logs(request: Request):
    return templates.TemplateResponse("logs.html", {"request": request})

@app.get("/companies", response_class=HTMLResponse)
async def read_companies(request: Request):
    return templates.TemplateResponse("companies.html", {"request": request})

@app.get("/companies/{company_id}", response_class=HTMLResponse)
async def read_company_detail(request: Request, company_id: int):
    return templates.TemplateResponse("company_detail.html", {"request": request})

@app.get("/automatizaciones", response_class=HTMLResponse)
async def read_automatizaciones(request: Request):
    return templates.TemplateResponse("automatizaciones.html", {"request": request})

@app.get("/etl-realtime", response_class=HTMLResponse)
async def read_etl_realtime(request: Request):
    return templates.TemplateResponse("realtime_etl.html", {"request": request})


@app.get("/catalogos", response_class=HTMLResponse)
async def read_catalogos(request: Request):
    return templates.TemplateResponse("catalogos.html", {"request": request})

@app.get("/mapeo", response_class=HTMLResponse)
async def read_mapeo(request: Request):
    return templates.TemplateResponse("mapeo.html", {"request": request})

@app.get("/mapeo/{subcategoria_id}", response_class=HTMLResponse)
async def read_mapeo_editor(request: Request, subcategoria_id: int):
    return templates.TemplateResponse("mapeo_editor.html", {"request": request})

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

