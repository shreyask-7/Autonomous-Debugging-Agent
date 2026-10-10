from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlmodel import SQLModel, create_engine
from app.config import settings
from app.models.schemas import AgentRun, AgentStep 

engine = create_engine(settings.DATABASE_URL, echo=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
  print("Initializing Database...")
  SQLModel.metadata.create_all(engine)
  yield
  print("Shutting down...")

app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

@app.get("/health")
def health_check():
  return {"status": "healthy", "service": settings.PROJECT_NAME}