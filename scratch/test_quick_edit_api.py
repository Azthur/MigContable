import requests

def test_api_quick_edit():
    base_url = "http://localhost:8080/api/v1"
    
    # 1. Fetch subcategories
    res = requests.get(f"{base_url}/mapeo/subcategorias")
    assert res.status_code == 200, f"Failed listing subcategories: {res.text}"
    subcats = res.json()
    if not subcats:
        print("No subcategories found in database.")
        return
        
    sub = subcats[0]
    sub_id = sub["id"]
    print(f"Selected subcategory ID {sub_id} ({sub['nombre']}) for testing.")
    
    # Keep original values to restore them later
    orig_period = sub.get("col_origen_periodo")
    orig_mes = sub.get("col_origen_mes")
    orig_asiento = sub.get("asiento_inicial")
    orig_rules = sub.get("filter_rules")
    
    # 2. Update via PUT
    test_payload = {
        "asiento_inicial": (orig_asiento or 1) + 1,
        "filter_rules": orig_rules or [],
        "col_origen_periodo": "TEST_PERIOD_COL",
        "col_origen_mes": "TEST_MONTH_COL"
    }
    
    print(f"Sending PUT payload: {test_payload}")
    put_res = requests.put(f"{base_url}/mapeo/subcategorias/{sub_id}", json=test_payload)
    assert put_res.status_code == 200, f"PUT update failed: {put_res.text}"
    
    updated_data = put_res.json()
    print("PUT response received successfully.")
    assert updated_data["col_origen_periodo"] == "TEST_PERIOD_COL", f"Expected col_origen_periodo to be 'TEST_PERIOD_COL', got {updated_data['col_origen_periodo']}"
    assert updated_data["col_origen_mes"] == "TEST_MONTH_COL", f"Expected col_origen_mes to be 'TEST_MONTH_COL', got {updated_data['col_origen_mes']}"
    assert updated_data["asiento_inicial"] == test_payload["asiento_inicial"], f"Expected asiento_inicial to be {test_payload['asiento_inicial']}, got {updated_data['asiento_inicial']}"
    print("Asserted API response matches payload.")
    
    # 3. Fetch again to verify persistence
    get_res = requests.get(f"{base_url}/mapeo/subcategorias/{sub_id}")
    assert get_res.status_code == 200
    fetched_data = get_res.json()
    assert fetched_data["col_origen_periodo"] == "TEST_PERIOD_COL"
    assert fetched_data["col_origen_mes"] == "TEST_MONTH_COL"
    print("Verified values are successfully persisted in DB and returned by GET.")
    
    # 4. Restore original values
    restore_payload = {
        "asiento_inicial": orig_asiento,
        "filter_rules": orig_rules,
        "col_origen_periodo": orig_period,
        "col_origen_mes": orig_mes
    }
    restore_res = requests.put(f"{base_url}/mapeo/subcategorias/{sub_id}", json=restore_payload)
    assert restore_res.status_code == 200
    print("Restored original subcategory configuration successfully.")
    print("ALL TESTS PASSED!")

if __name__ == "__main__":
    test_api_quick_edit()
