import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import DestSessionLocal
from backend.app.models.models import TipoCambio
from fastapi.testclient import TestClient
from backend.app.main import app

def test_endpoints():
    db = DestSessionLocal()
    client = TestClient(app)
    test_date = "2026-12-31"
    
    try:
        # Pre-cleanup in case a previous run crashed
        tc_old = db.query(TipoCambio).filter(TipoCambio.fecha == test_date).first()
        if tc_old:
            db.delete(tc_old)
            db.commit()

        # 1. Test POST (Insert)
        print("Testing POST (Insert)...")
        payload = {"fecha": test_date, "compra": 3.854, "venta": 3.879}
        response = client.post("/api/v1/tipo-cambio", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.json()["message"] == "Tipo de cambio registrado de manera manual"
        print("[OK] Manual insert successful.")

        # Verify insertion in DB
        db.expire_all()
        tc = db.query(TipoCambio).filter(TipoCambio.fecha == test_date).first()
        assert tc is not None, "Record not found in database!"
        assert abs(float(tc.compra) - 3.854) < 1e-4, f"Expected 3.854, got {tc.compra}"
        assert tc.source == "Manual", f"Expected 'Manual', got {tc.source}"
        print("[OK] Database verification successful.")

        # 2. Test POST (Update)
        print("Testing POST (Update)...")
        payload = {"fecha": test_date, "compra": 3.900, "venta": 3.910}
        response = client.post("/api/v1/tipo-cambio", json=payload)
        assert response.status_code == 200
        
        # Verify update in DB
        db.expire_all()
        tc = db.query(TipoCambio).filter(TipoCambio.fecha == test_date).first()
        assert abs(float(tc.compra) - 3.900) < 1e-4, f"Expected 3.900, got {tc.compra}"
        assert abs(float(tc.venta) - 3.910) < 1e-4, f"Expected 3.910, got {tc.venta}"
        print("[OK] Manual update successful.")

        # 3. Test DELETE
        print("Testing DELETE...")
        response = client.delete(f"/api/v1/tipo-cambio/{test_date}")
        assert response.status_code == 200
        assert response.json()["message"] == "Tipo de cambio eliminado"
        print("[OK] Manual delete successful.")

        # Verify deletion in DB
        db.expire_all()
        tc = db.query(TipoCambio).filter(TipoCambio.fecha == test_date).first()
        assert tc is None, "Record still exists in database after deletion!"
        print("[OK] Database deletion verification successful.")

        print("\nALL API TESTS PASSED SUCCESSFULLY!")

    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        
        # Cleanup
        try:
            db.rollback()
            tc_cleanup = db.query(TipoCambio).filter(TipoCambio.fecha == test_date).first()
            if tc_cleanup:
                db.delete(tc_cleanup)
                db.commit()
        except Exception:
            pass
    finally:
        db.close()

if __name__ == "__main__":
    test_endpoints()
