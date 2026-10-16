from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List

from app.models.database import get_session
from app.models.schemas import AgentRun, AgentStep

router = APIRouter(prefix="/api/v1/runs", tags=["Agent Telemetry"])

@router.get("/", response_model=List[AgentRun])
def get_all_runs(skip: int = 0, limit: int = 50, db: Session = Depends(get_session)):
    statement = select(AgentRun).order_by(AgentRun.created_at.desc()).offset(skip).limit(limit)
    return db.exec(statement).all()

@router.get("/{run_id}", response_model=AgentRun)
def get_run_details(run_id: int, db: Session = Depends(get_session)):
    run = db.get(AgentRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run

@router.get("/{run_id}/steps", response_model=List[AgentStep])
def get_run_steps(run_id: int, db: Session = Depends(get_session)):
    statement = select(AgentStep).where(AgentStep.run_id == run_id).order_by(AgentStep.step_number.asc())
    steps = db.exec(statement).all()
    if not steps:
        raise HTTPException(status_code=404, detail="No steps found for this run")
    return steps