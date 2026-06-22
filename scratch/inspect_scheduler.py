import os
from celery import Celery
from celery.beat import Scheduler, ScheduleEntry
from backend.app.celery_app import celery
from backend.app.celery_tasks.beat_scanner import parse_schedule, DatabaseScheduler

print("Initializing DatabaseScheduler mock...")
scheduler = DatabaseScheduler(app=celery)
scheduler.setup_schedule()

print("\n--- Current Schedule Entries in Scheduler ---")
for name, entry in scheduler.schedule.items():
    print(f"\nTask: {name}")
    print(f"  Task function: {entry.task}")
    print(f"  Schedule: {entry.schedule}")
    print(f"  Last Run At: {entry.last_run_at}")
    print(f"  Total Run Count: {entry.total_run_count}")
    
    # Check is_due
    is_due, next_time_to_run = entry.is_due()
    print(f"  Is Due Now?: {is_due}")
    print(f"  Next time to run (delay in seconds): {next_time_to_run}")
