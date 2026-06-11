import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import DestSessionLocal
from backend.app.models.models import ScheduledTask
from backend.app.core.scheduler import scheduler, start_scheduler

def test_scheduler_toggle():
    db = DestSessionLocal()
    try:
        # 1. Create a dummy task
        print("Creating dummy scheduled task...")
        task = ScheduledTask(
            company_id=None,
            task_type="TEST_TOGGLE",
            schedule_type="MINUTES",
            time_str="10",
            is_active=True
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        print(f"Task created with ID: {task.id}, is_active: {task.is_active}")
        
        # Start scheduler and load active tasks
        start_scheduler()
        
        # Check if job is in scheduler
        job_id = f"task_{task.id}"
        job = scheduler.get_job(job_id)
        assert job is not None, "Active task was not scheduled!"
        print(f"[OK] Job {job_id} successfully scheduled. Next run: {job.next_run_time}")
        
        # 2. Deactivate the task
        print("Deactivating scheduled task...")
        task.is_active = False
        db.commit()
        
        # Reload scheduler
        start_scheduler()
        
        # Check if job is removed
        job = scheduler.get_job(job_id)
        assert job is None, "Inactive task was not removed from scheduler!"
        print(f"[OK] Job {job_id} successfully removed from scheduler.")
        
        # 3. Clean up
        print("Cleaning up dummy task...")
        db.delete(task)
        db.commit()
        print("Dummy task deleted.")
        
        print("\nALL TESTS PASSED SUCCESSFULLY!")
        
    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        
        # Cleanup if task was created
        try:
            db.rollback()
            t = db.query(ScheduledTask).filter(ScheduledTask.task_type == "TEST_TOGGLE").first()
            if t:
                db.delete(t)
                db.commit()
                print("Cleaned up after failure.")
        except Exception:
            pass
    finally:
        db.close()

if __name__ == "__main__":
    test_scheduler_toggle()
