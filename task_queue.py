import asyncio
import sqlite3
import json
import time
import random
from pathlib import Path
from typing import Dict, Any
from pdf_processor import process_pdf_file

# Global task queue and worker status
task_queue = asyncio.Queue()
worker_running = False

async def add_task_to_queue(job_id: str, file_path: str, original_filename: str):
    """Add a task to the processing queue."""
    task = {
        "job_id": job_id,
        "file_path": file_path,
        "original_filename": original_filename,
        "timestamp": time.time()
    }
    await task_queue.put(task)
    print(f"Task {job_id} added to queue")

async def process_task(task: Dict[str, Any]):
    """Process a single task from the queue."""
    job_id = task["job_id"]
    file_path = task["file_path"]
    
    print(f"Starting processing for job {job_id}")
    
    try:
        # Update status to processing
        update_job_status(job_id, "processing")
        
        # Simulate long processing time (30-300 seconds)
        delay = random.randint(30, 300)
        print(f"Simulating {delay} second delay for job {job_id}")
        await asyncio.sleep(delay)
        
        # Actual PDF processing
        org_username, members = process_pdf_file(file_path)
        
        # Update database with results
        conn = sqlite3.connect("jobs.db")
        conn.execute(
            """UPDATE jobs 
               SET extracted_company_username = ?, github_members = ?, status = ? 
               WHERE job_id = ?""",
            (org_username, json.dumps(members) if members else None, "completed", job_id)
        )
        conn.commit()
        conn.close()
        
        print(f"Job {job_id} completed successfully")
        
    except Exception as e:
        print(f"Job {job_id} failed: {str(e)}")
        # Update job status to failed
        update_job_status(job_id, "failed")
        
    finally:
        # Clean up file
        file_path_obj = Path(file_path)
        if file_path_obj.exists():
            file_path_obj.unlink()
            print(f"Cleaned up file for job {job_id}")

def update_job_status(job_id: str, status: str):
    """Update job status in database."""
    conn = sqlite3.connect("jobs.db")
    conn.execute("UPDATE jobs SET status = ? WHERE job_id = ?", (status, job_id))
    conn.commit()
    conn.close()

async def task_worker():
    """Background worker that processes tasks from the queue."""
    global worker_running
    worker_running = True
    print("Task worker started")
    
    while worker_running:
        try:
            # Wait for a task with timeout
            task = await asyncio.wait_for(task_queue.get(), timeout=1.0)
            await process_task(task)
            task_queue.task_done()
            
        except asyncio.TimeoutError:
            # No tasks available, continue loop
            continue
        except Exception as e:
            print(f"Worker error: {str(e)}")
            continue

async def start_worker():
    """Start the background worker."""
    asyncio.create_task(task_worker())

async def stop_worker():
    """Stop the background worker."""
    global worker_running
    worker_running = False 