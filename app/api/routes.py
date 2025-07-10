import json
import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime

from app.database.base import get_session, Job
from app.models.job import Job as JobModel
from app.services.pdf_service import PDFService
from app.core.config import settings

router = APIRouter()

@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_session)
):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Generate unique job ID
    job_id = str(uuid.uuid4())
    
    # Save file
    file_path = settings.UPLOAD_DIR / f"{job_id}.pdf"
    try:
        content = await file.read()
        file_path.write_bytes(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Create job record
    job = Job(
        job_id=job_id,
        original_filename=file.filename,
        status="processing",
        timestamp=datetime.utcnow()
    )
    
    db.add(job)
    await db.commit()

    # Process PDF in background
    try:
        org_username, members = await PDFService.process_pdf(file_path)
        
        # Update job record
        stmt = update(Job).where(Job.job_id == job_id).values(
            extracted_company_username=org_username,
            github_members=json.dumps(members) if members else None,
            status="completed"
        )
        await db.execute(stmt)
        await db.commit()
    except Exception as e:
        # Update job status to failed
        stmt = update(Job).where(Job.job_id == job_id).values(status="failed")
        await db.execute(stmt)
        await db.commit()
        
        # Clean up file
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")

    # Clean up file after processing
    file_path.unlink(missing_ok=True)
    
    return {"job_id": job_id, "status": "processing"}

@router.get("/jobs/{job_id}")
async def get_job_status(
    job_id: str,
    db: AsyncSession = Depends(get_session)
):
    stmt = select(Job).where(Job.job_id == job_id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "job_id": job.job_id,
        "status": job.status,
        "original_filename": job.original_filename,
        "extracted_company_username": job.extracted_company_username,
        "github_members": json.loads(job.github_members) if job.github_members else None,
        "timestamp": job.timestamp
    } 