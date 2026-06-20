from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import Optional
from app.database import get_db
from app.models import Job, Transaction, JobSummary
from app.schemas import JobResponse, JobStatusResponse, JobListResponse, JobResultsResponse
import uuid

router = APIRouter(prefix="/jobs", tags=["jobs"])


from app.worker.tasks import process_csv_job

@router.post("/upload", response_model=JobResponse, status_code=201)
async def upload_job(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")
    
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file.")
        
    row_count_raw = content.count(b'\n')
    if not content.endswith(b'\n') and content:
        row_count_raw += 1
        

    if row_count_raw > 0:
        row_count_raw -= 1
        
    job = Job(
        filename=file.filename,
        row_count_raw=row_count_raw,
        file_content=content,
        status="pending"
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    

    process_csv_job.delay(str(job.id))
    
    return job

@router.get("/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Job).options(selectinload(Job.summary)).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
        
    summary_dict = None
    if job.status == "completed" and job.summary:
        summary_dict = {
            "total_spend_inr": float(job.summary.total_spend_inr) if job.summary.total_spend_inr else None,
            "total_spend_usd": float(job.summary.total_spend_usd) if job.summary.total_spend_usd else None,
            "top_merchants": job.summary.top_merchants,
            "anomaly_count": job.summary.anomaly_count,
            "narrative": job.summary.narrative,
            "risk_level": job.summary.risk_level
        }
        
    return JobStatusResponse(
        job_id=job.id,
        status=job.status,
        created_at=job.created_at,
        completed_at=job.completed_at,
        summary=summary_dict
    )

@router.get("/{job_id}/results", response_model=JobResultsResponse)
async def get_job_results(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Job).options(selectinload(Job.transactions), selectinload(Job.summary)).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
        
    if job.status != "completed":
        raise HTTPException(status_code=400, detail=f"Job is not completed yet. Current status: {job.status}")
        
    anomalies = []
    category_breakdown = {}
    
    for t in job.transactions:
        if t.is_anomaly:
            anomalies.append({
                "txn_id": t.txn_id,
                "amount": float(t.amount),
                "reasons": t.anomaly_reasons
            })
            
        cat = t.category
        if cat not in category_breakdown:
            category_breakdown[cat] = 0.0
        category_breakdown[cat] += float(t.amount)
        
    return JobResultsResponse(
        job_id=job.id,
        status=job.status,
        transactions=job.transactions,
        anomalies=anomalies,
        category_breakdown=category_breakdown,
        summary=job.summary
    )

@router.get("", response_model=list[JobListResponse])
async def list_jobs(status: Optional[str] = Query(None), db: AsyncSession = Depends(get_db)):
    query = select(Job)
    if status:
        query = query.where(Job.status == status)
    query = query.order_by(Job.created_at.desc())
    
    result = await db.execute(query)
    jobs = result.scalars().all()
    
    return jobs
