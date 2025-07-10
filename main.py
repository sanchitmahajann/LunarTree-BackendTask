import os
import uuid
import json
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
from datetime import datetime

# Simple configuration
DATABASE_FILE = "jobs.db"
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI(
    title="PDF Processing API",
    description="Simple PDF processing with GitHub integration",
    version="1.0.0"
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

@app.get("/")
async def root():
    return {"message": "PDF Processing API", "docs": "/docs"}

# Import processing functions
from pdf_processor import process_pdf_file

@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...)):
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

    # Insert initial job record
    conn = sqlite3.connect(DATABASE_FILE)
    conn.execute(
        "INSERT INTO jobs (job_id, original_filename, status, timestamp) VALUES (?, ?, ?, ?)",
        (job_id, file.filename, "processing", timestamp)
    )
    conn.commit()
    conn.close()

    # Process PDF
    try:
        org_username, members = process_pdf_file(str(file_path))
        
        # Update job record
        conn = sqlite3.connect(DATABASE_FILE)
        conn.execute(
            """UPDATE jobs 
               SET extracted_company_username = ?, github_members = ?, status = ? 
               WHERE job_id = ?""",
            (org_username, json.dumps(members) if members else None, "completed", job_id)
        )
        conn.commit()
        conn.close()
        
    except Exception as e:
        # Update job as failed
        conn = sqlite3.connect(DATABASE_FILE)
        conn.execute("UPDATE jobs SET status = ? WHERE job_id = ?", ("failed", job_id))
        conn.commit()
        conn.close()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
    
    finally:
        # Clean up file
        if file_path.exists():
            file_path.unlink()

    return {"job_id": job_id, "status": "completed"}

@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str):
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "job_id": row[0],
        "original_filename": row[1],
        "extracted_company_username": row[2],
        "github_members": json.loads(row[3]) if row[3] else None,
        "status": row[4],
        "timestamp": row[5]
    } 