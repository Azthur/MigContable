from backend.app.core.database import DestSessionLocal
from backend.app.api.endpoints.mapeo import get_helper_data

db = DestSessionLocal()
try:
    # Test for sub_id = 2
    res2 = get_helper_data(2, db)
    print("Result Sub 2:", res2)
    
    # Test for sub_id = 4
    res4 = get_helper_data(4, db)
    print("Result Sub 4:", res4)
except Exception as e:
    print("Execution Error:", e)
finally:
    db.close()
