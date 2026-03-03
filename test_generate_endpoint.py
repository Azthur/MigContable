import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from backend.app.core.database import DestSessionLocal
from backend.app.api.endpoints.mapeo import generate_to_cf_diariol

db = DestSessionLocal()

def test_generation():
    print("Testing generate_to_cf_diariol endpoint...")
    body = {
        "company_id": 1,
        "clear_previous": True,
        "filters": []
    }
    
    try:
        res = generate_to_cf_diariol(body, db)
        print("Result:", res)
    except Exception as e:
        print("Exception caught:", e)

if __name__ == "__main__":
    test_generation()
