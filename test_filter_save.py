import requests
import json

BASE_URL = "http://localhost:8000/api/v1"
SUBCATEGORIA_ID = 1  # Verify with an existing subcategory ID

def test_filter_save():
    print(f"Testing filter persistence for subcategory {SUBCATEGORIA_ID}")
    
    # 1. Get original subcategory
    try:
        r = requests.get(f"{BASE_URL}/mapeo/subcategorias/{SUBCATEGORIA_ID}")
        r.raise_for_status()
        sub = r.json()
        print(f"Original subcategory name: {sub.get('nombre')}")
        print(f"Original filter_rules: {sub.get('filter_rules')}")
    except Exception as e:
        print(f"Error getting subcategory: {e}")
        return

    # 2. Update with new filter rule
    test_filter = [{"column": "coddoc", "operator": "=", "value": "TEST_999"}]
    print(f"\nSending PUT request with filter_rules: {test_filter}")
    
    try:
        r_put = requests.put(
            f"{BASE_URL}/mapeo/subcategorias/{SUBCATEGORIA_ID}",
            json={"filter_rules": test_filter}
        )
        r_put.raise_for_status()
        updated = r_put.json()
        print(f"Response logic filter_rules: {updated.get('filter_rules')}")
    except Exception as e:
        print(f"Error updating subcategory: {e}")
        return
        
    # 3. Verify it was actually saved by getting it again
    try:
        r_get = requests.get(f"{BASE_URL}/mapeo/subcategorias/{SUBCATEGORIA_ID}")
        r_get.raise_for_status()
        final_sub = r_get.json()
        final_filters = final_sub.get('filter_rules')
        print(f"\nVerified from DB filter_rules: {final_filters}")
        
        if final_filters == test_filter:
            print("SUCCESS: filter_rules were saved and retrieved correctly!")
        else:
            print("FAILURE: filter_rules do not match what was sent.")
            
    except Exception as e:
        print(f"Error verifying subcategory: {e}")

if __name__ == "__main__":
    test_filter_save()
