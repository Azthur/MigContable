import sys
import os
print(f"CWD: {os.getcwd()}")
print(f"Sys Path: {sys.path}")

try:
    import backend.app.api.endpoints.etl as etl
    print(f"ETL File: {etl.__file__}")
except ImportError as e:
    print(f"Import Error: {e}")

try:
    import backend
    print(f"Backend Package: {backend.__file__}")
except:
    pass
