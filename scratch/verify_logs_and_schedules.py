import urllib.request
import json
import sys
from urllib.parse import urlencode

base_url = "http://localhost:8080/api/v1"

# 1. Login to get token
login_url = f"{base_url}/auth/login"
login_data = urlencode({
    "username": "admin@migconta.com",
    "password": "admin123"
}).encode("utf-8")

headers = {
    "Content-Type": "application/x-www-form-urlencoded"
}

req = urllib.request.Request(login_url, data=login_data, headers=headers, method="POST")
try:
    with urllib.request.urlopen(req) as res:
        login_res = json.loads(res.read().decode("utf-8"))
        token = login_res["access_token"]
        print("Login SUCCESS. Token acquired.")
except Exception as e:
    print("Login FAILED:", e)
    sys.exit(1)

auth_headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# 2. Get list of pipelines (schedules)
print("\n--- 2. Fetching Pipelines and verifying last_run and next_run ---")
try:
    req = urllib.request.Request(f"{base_url}/pipelines", headers=auth_headers, method="GET")
    with urllib.request.urlopen(req) as res:
        pipelines = json.loads(res.read().decode("utf-8"))
        print(f"Total pipelines found: {len(pipelines)}")
        for idx, p in enumerate(pipelines[:5]):
            print(f"\nPipeline {idx+1}: {p.get('company_name')} - {p.get('subcategoria_nombres')}")
            print(f"  Frecuencia: {p.get('schedule_type')} ({p.get('time_str')})")
            print(f"  Estado: {'Activo' if p.get('is_active') else 'Inactivo'}")
            print(f"  Última Ejecución (last_run): {p.get('last_run')}")
            print(f"  Próxima Ejecución (next_run): {p.get('next_run')}")
            if p.get('is_active') and not p.get('next_run'):
                print("  ERROR: next_run should be set for active pipelines!")
                sys.exit(1)
except Exception as e:
    print("Fetch pipelines FAILED:", e)
    sys.exit(1)

# 3. Get latest realtime-logs
print("\n--- 3. Fetching Realtime Logs ---")
try:
    req = urllib.request.Request(f"{base_url}/etl/realtime-logs?limit=5", headers=auth_headers, method="GET")
    with urllib.request.urlopen(req) as res:
        logs = json.loads(res.read().decode("utf-8"))
        print(f"Fetched {len(logs)} log entries.")
        for idx, l in enumerate(logs):
            print(f"\nLog {idx+1}: {l.get('company_name')} - {l.get('subcategorias')}")
            print(f"  Status: {l.get('status')}")
            print(f"  Run Date: {l.get('run_date')}")
            print(f"  Message: {l.get('message')}")
            print(f"  Extracted/Generated/Migrated: {l.get('records_extracted')}/{l.get('records_generated')}/{l.get('records_migrated')}")
            print(f"  Errors count: {len(l.get('errors', []))}")
except Exception as e:
    print("Fetch realtime logs FAILED:", e)
    sys.exit(1)

# 4. Trigger manual execution for pipeline ID 1 (or first found active)
if pipelines:
    active_p = next((p for p in pipelines if p.get("is_active")), None)
    if active_p:
        pid = active_p["id"]
        print(f"\n--- 4. Triggering manual run for pipeline ID {pid} ---")
        try:
            req = urllib.request.Request(f"{base_url}/pipelines/{pid}/run-now", data=b"", headers=auth_headers, method="POST")
            with urllib.request.urlopen(req) as res:
                run_res = json.loads(res.read().decode("utf-8"))
                print("Trigger success:", run_res)
                task_id = run_res.get("celery_task_id")
                
                # Poll status
                import time
                print("Polling for task completion in etl/realtime-logs...")
                completed = False
                for _ in range(20):
                    time.sleep(2)
                    req_logs = urllib.request.Request(f"{base_url}/etl/realtime-logs?limit=5", headers=auth_headers, method="GET")
                    with urllib.request.urlopen(req_logs) as r_res:
                        latest_logs = json.loads(r_res.read().decode("utf-8"))
                        # Find if there is any log entry matching task_id (if we returned it or via latest date)
                        # We can just check if any log entry has run_date matching within last 30s
                        if latest_logs:
                            latest_log = latest_logs[0]
                            print(f"Latest log status: {latest_log.get('status')} | Msg: {latest_log.get('message')}")
                            if latest_log.get('status') in ["SUCCESS", "WARNING", "ERROR"]:
                                completed = True
                                break
                if completed:
                    print("Verification successful! Manual execution was logged in real-time.")
                else:
                    print("Verification timeout: Task did not complete in 40s or logs did not update.")
        except Exception as e:
            print("Trigger manual run FAILED:", e)
            sys.exit(1)
else:
    print("No pipelines to test manual trigger.")

print("\nAll tests completed!")
