import os
import uuid
import json
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
from datetime import datetime

# Import task queue system
from task_queue import add_task_to_queue, start_worker, stop_worker

# Simple configuration
DATABASE_FILE = "jobs.db"
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI(
    title="PDF Processing API - Async Queue",
    description="Async PDF processing with queue system and GitHub integration",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
def init_db():
    conn = sqlite3.connect(DATABASE_FILE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            original_filename TEXT NOT NULL,
            extracted_company_username TEXT,
            github_members TEXT,
            status TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

@app.on_event("startup")
async def startup_event():
    init_db()
    await start_worker()  # Start the background worker
    print("Application started with background task worker")

@app.on_event("shutdown")
async def shutdown_event():
    await stop_worker()  # Stop the background worker
    print("Background task worker stopped")

@app.get("/")
async def root():
    return {
        "message": "PDF Processing API - Async Queue", 
        "docs": "/docs",
        "queue_info": "Tasks are processed asynchronously in background"
    }

@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload PDF for async processing.
    Returns immediately with job_id while processing happens in background.
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Generate job ID
    job_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()
    
    # Save file temporarily
    file_path = UPLOAD_DIR / f"{job_id}.pdf"
    try:
        content = await file.read()
        with open(file_path, 'wb') as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Insert initial job record with "queued" status
    conn = sqlite3.connect(DATABASE_FILE)
    conn.execute(
        "INSERT INTO jobs (job_id, original_filename, status, timestamp) VALUES (?, ?, ?, ?)",
        (job_id, file.filename, "queued", timestamp)
    )
    conn.commit()
    conn.close()

    # Add task to queue for background processing
    await add_task_to_queue(job_id, str(file_path), file.filename)

    # Return immediately with job ID
    return {
        "job_id": job_id, 
        "status": "queued",
        "message": "PDF uploaded successfully. Processing will begin shortly.",
        "estimated_processing_time": "30-300 seconds"
    }

@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str):
    """
    Get job status and results.
    Status can be: 'queued', 'processing', 'completed', 'failed'
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_data = {
        "job_id": row[0],
        "original_filename": row[1],
        "extracted_company_username": row[2],
        "github_members": json.loads(row[3]) if row[3] else None,
        "status": row[4],
        "timestamp": row[5]
    }
    
    # Add helpful messages based on status
    if job_data["status"] == "queued":
        job_data["message"] = "Job is waiting in queue to be processed"
    elif job_data["status"] == "processing":
        job_data["message"] = "Job is currently being processed (this may take 30-300 seconds)"
    elif job_data["status"] == "completed":
        job_data["message"] = "Job completed successfully"
    elif job_data["status"] == "failed":
        job_data["message"] = "Job processing failed"
    
    return job_data

@app.get("/api/queue/status")
async def get_queue_status():
    """Get current queue status and statistics."""
    from task_queue import task_queue, worker_running
    
    # Count jobs by status
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.execute("""
        SELECT status, COUNT(*) as count 
        FROM jobs 
        GROUP BY status
    """)
    status_counts = dict(cursor.fetchall())
    conn.close()
    
    return {
        "worker_running": worker_running,
        "queue_size": task_queue.qsize(),
        "job_statistics": status_counts,
        "total_jobs": sum(status_counts.values())
    } 