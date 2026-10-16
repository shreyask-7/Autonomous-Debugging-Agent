import json
import asyncio
import os
import subprocess
import shutil
import uuid

from typing import List
from uuid import UUID
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlmodel import SQLModel, Session, select

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.zipkin.json import ZipkinExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource

from app.config import settings
from app.models.database import engine, get_session
from app.models.schemas import AgentRun, AgentStep, CreateRunRequests, RunResponse
from app.engine.loop import AgentRuntime

resource = Resource.create({
  "service.name": "autonomous-debugger-api"
})
trace.set_tracer_provider(TracerProvider(resource=resource))
zipkin_exporter = ZipkinExporter(endpoint="http://localhost:9411/api/v2/spans")
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(zipkin_exporter))

@asynccontextmanager
async def lifespan(app: FastAPI):
  print("Initializing Database...")
  SQLModel.metadata.create_all(engine)
  yield
  print("Shutting down...")

app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

FastAPIInstrumentor.instrument_app(app)

app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

@app.get("/health")
def health_check():
  return {"status": "healthy", "service": settings.PROJECT_NAME}

@app.post("/api/runs", response_model=RunResponse, status_code=status.HTTP_201_CREATED)
def create_run(request: CreateRunRequests, db: Session = Depends(get_session)):
  if request.repo_path.startswith("http://") or request.repo_path.startswith("https://"):
      run_uuid = uuid.uuid4()
      workspace_dir = Path(f"./workspaces/run_{run_uuid}").resolve()
      workspace_dir.mkdir(parents=True, exist_ok=True)
      
      try:
          print(f"Cloning {request.repo_path} into {workspace_dir}...")
          subprocess.run(
              ["git", "clone", request.repo_path, str(workspace_dir)], 
              check=True, capture_output=True, text=True
          )
          target_path = workspace_dir
      except subprocess.CalledProcessError as e:
          shutil.rmtree(workspace_dir, ignore_errors=True)
          raise HTTPException(status_code=400, detail=f"Failed to clone repository: {e.stderr}")
  else:
      BASE_DIR = Path(__file__).resolve().parent.parent
      target_path = (BASE_DIR / request.repo_path).resolve()

  run = AgentRun(
      repo_name=str(target_path),
      issue_description=request.issue_description
  )
  db.add(run)
  db.commit()
  db.refresh(run)
  return run

@app.get("/api/runs", response_model=List[RunResponse])
def list_runs(db: Session = Depends(get_session)):
  runs = db.exec(select(AgentRun).order_by(AgentRun.created_at.desc())).all()
  return runs

@app.get("/api/runs/{run_id}", response_model=RunResponse)
def get_run(run_id: UUID, db: Session = Depends(get_session)):
  run = db.get(AgentRun, run_id)
  if not run:
    raise HTTPException(status_code=404, detail="Run not found")
  return run

@app.get("/api/runs/{run_id}/stream")
async def stream_run(run_id: UUID, db: Session = Depends(get_session)):
  run = db.get(AgentRun, run_id)
  if not run:
      raise HTTPException(status_code=404, detail="Run not found")

  async def event_generator():
      agent = AgentRuntime(
          run_id=run_id,
          db=db
      )

      async for step in agent.run_stream():
          payload = json.dumps(step)
          yield f"data: {payload}\n\n"
          await asyncio.sleep(0.05)

  return StreamingResponse(
      event_generator(),
      media_type="text/event-stream",
      headers={
          "Cache-Control": "no-cache",
          "Connection": "keep-alive",
          "Content-Type": "text/event-stream"
      } 
  )