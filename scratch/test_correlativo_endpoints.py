import requests

def test_correlativo_sync():
    base_url = "http://localhost:8080/api/v1"
    
    # 1. Fetch subcategories to select one for testing
    res = requests.get(f"{base_url}/mapeo/subcategorias")
    assert res.status_code == 200
    subcats = res.json()
    if not subcats:
        print("No subcategories found in database.")
        return
        
    sub = subcats[0]
    sub_id = sub["id"]
    company_id = 4  # Yelave Industrias S.A.C or any active company
    
    # Clean up existing correlativo for this combo if exists
    # List first
    res_list = requests.get(f"{base_url}/etl/correlativos?company_id={company_id}&subcategoria_id={sub_id}&periodo=2099&mes=12")
    if res_list.status_code == 200:
        for item in res_list.json():
            requests.delete(f"{base_url}/etl/correlativos/{item['id']}")
            
    # Save original subcategory values
    orig_period_col = sub.get("col_origen_periodo")
    orig_mes_col = sub.get("col_origen_mes")
    
    print(f"Original subcategory {sub_id} col_origen_periodo: {orig_period_col}, col_origen_mes: {orig_mes_col}")
    
    # 2. Create correlativo with custom col_origen_periodo / col_origen_mes
    create_payload = {
        "company_id": company_id,
        "subcategoria_id": sub_id,
        "periodo": "2099",
        "mes": "12",
        "asiento_inicial": 10,
        "col_origen_periodo": "TEST_CPER_SYNC",
        "col_origen_mes": "TEST_CMES_SYNC"
    }
    
    create_res = requests.post(f"{base_url}/etl/correlativos", json=create_payload)
    assert create_res.status_code == 200, f"Failed to create correlativo: {create_res.text}"
    created_id = create_res.json()["id"]
    print(f"Created correlativo with ID {created_id}")
    
    # 3. Retrieve subcategory to verify columns were synchronized
    sub_res = requests.get(f"{base_url}/mapeo/subcategorias/{sub_id}")
    assert sub_res.status_code == 200
    sub_updated = sub_res.json()
    assert sub_updated["col_origen_periodo"] == "TEST_CPER_SYNC", "col_origen_periodo did not sync"
    assert sub_updated["col_origen_mes"] == "TEST_CMES_SYNC", "col_origen_mes did not sync"
    print("Verified subcategory Period/Month columns were synchronized on POST.")
    
    # 4. Update correlativo with different columns
    update_payload = {
        "asiento_inicial": 25,
        "asiento_actual": 24,
        "col_origen_periodo": "TEST_CPER_SYNC2",
        "col_origen_mes": "TEST_CMES_SYNC2"
    }
    update_res = requests.put(f"{base_url}/etl/correlativos/{created_id}", json=update_payload)
    assert update_res.status_code == 200, f"Failed to update: {update_res.text}"
    
    # 5. Retrieve subcategory to verify columns were synchronized again
    sub_res = requests.get(f"{base_url}/mapeo/subcategorias/{sub_id}")
    assert sub_res.status_code == 200
    sub_updated2 = sub_res.json()
    assert sub_updated2["col_origen_periodo"] == "TEST_CPER_SYNC2", "col_origen_periodo did not sync on PUT"
    assert sub_updated2["col_origen_mes"] == "TEST_CMES_SYNC2", "col_origen_mes did not sync on PUT"
    print("Verified subcategory Period/Month columns were synchronized on PUT.")
    
    # 6. Retrieve correlativos list to check if columns are returned
    list_res = requests.get(f"{base_url}/etl/correlativos?company_id={company_id}")
    assert list_res.status_code == 200
    list_items = list_res.json()
    found_item = next((item for item in list_items if item["id"] == created_id), None)
    assert found_item is not None
    assert found_item["col_origen_periodo"] == "TEST_CPER_SYNC2"
    assert found_item["col_origen_mes"] == "TEST_CMES_SYNC2"
    print("Verified list_correlativos returns col_origen_periodo and col_origen_mes.")
    
    # Cleanup
    del_res = requests.delete(f"{base_url}/etl/correlativos/{created_id}")
    assert del_res.status_code == 200
    
    # Restore original subcategory columns
    restore_res = requests.put(f"{base_url}/mapeo/subcategorias/{sub_id}", json={
        "col_origen_periodo": orig_period_col,
        "col_origen_mes": orig_mes_col
    })
    assert restore_res.status_code == 200
    print("Cleaned up and restored original subcategory configuration.")
    print("CORRELATIVO ENDPOINTS SYNC TESTS PASSED!")


def test_correlativo_bulk_year():
    base_url = "http://localhost:8080/api/v1"
    
    # 1. Fetch subcategories
    res = requests.get(f"{base_url}/mapeo/subcategorias")
    assert res.status_code == 200
    subcats = res.json()
    if not subcats:
        print("No subcategories found for bulk test.")
        return
        
    sub = subcats[0]
    sub_id = sub["id"]
    company_id = 4
    
    # Clean up existing correlativos for this period "2098" if any
    res_list = requests.get(f"{base_url}/etl/correlativos?company_id={company_id}&subcategoria_id={sub_id}&periodo=2098")
    if res_list.status_code == 200:
        for item in res_list.json():
            requests.delete(f"{base_url}/etl/correlativos/{item['id']}")
            
    # Original subcategory values
    orig_period_col = sub.get("col_origen_periodo")
    orig_mes_col = sub.get("col_origen_mes")
    
    # 2. POST with bulk_year = True
    bulk_payload = {
        "company_id": company_id,
        "subcategoria_id": sub_id,
        "periodo": "2098",
        "asiento_inicial": 5,
        "col_origen_periodo": "TEST_CPER_BULK",
        "col_origen_mes": "TEST_CMES_BULK",
        "bulk_year": True
    }
    
    bulk_res = requests.post(f"{base_url}/etl/correlativos", json=bulk_payload)
    assert bulk_res.status_code == 200, f"Bulk creation failed: {bulk_res.text}"
    print("Bulk creation response:", bulk_res.json())
    
    # 3. Retrieve and assert all 12 months were created
    res_list = requests.get(f"{base_url}/etl/correlativos?company_id={company_id}&subcategoria_id={sub_id}&periodo=2098")
    assert res_list.status_code == 200
    items = res_list.json()
    assert len(items) == 12, f"Expected 12 correlativos, got {len(items)}"
    
    # Check that col_origen_periodo was synchronized in MapeoSubcategoria
    sub_res = requests.get(f"{base_url}/mapeo/subcategorias/{sub_id}")
    assert sub_res.status_code == 200
    sub_updated = sub_res.json()
    assert sub_updated["col_origen_periodo"] == "TEST_CPER_BULK"
    assert sub_updated["col_origen_mes"] == "TEST_CMES_BULK"
    print("Verified all 12 months were successfully created/updated in a single transaction.")
    
    # Cleanup
    for item in items:
        requests.delete(f"{base_url}/etl/correlativos/{item['id']}")
        
    requests.put(f"{base_url}/mapeo/subcategorias/{sub_id}", json={
        "col_origen_periodo": orig_period_col,
        "col_origen_mes": orig_mes_col
    })
    print("Cleaned up bulk test.")
    print("BULK YEAR ENDPOINT TEST PASSED!")

if __name__ == "__main__":
    test_correlativo_sync()
    test_correlativo_bulk_year()
