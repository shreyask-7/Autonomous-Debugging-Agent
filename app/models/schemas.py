from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from enum import Enum
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON

class RunStatus(str, Enum):
  PENDING = "PENDING"
  RUNNING = "RUNNING"
  SUCCESS = "SUCCESS"
  FAILED = "FAILED"

class StepType(str, Enum):
  PLANNING = "PLANNING"
  TOOL_EXECUTION = "TOOL_EXECUTION"
  VERDICT = "VERDICT"

class AgentRun(SQLModel, table = True):
  __tablename__ = "agent_runs"

  id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
  repo_name: str
  issue_description: str
  status: RunStatus = Field(default=RunStatus.PENDING)
  iterations: int = Field(default=0)
  created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
  completed_at: Optional[datetime] = None

  steps: List["AgentStep"] = Relationship(back_populates="run")

class AgentStep(SQLModel, table = True):
  __tablename__ = "agent_steps"

  id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
  run_id: UUID = Field(foreign_key="agent_runs.id", index=True)
  step_number: int
  step_type: StepType
  tool_name: Optional[str] = None
  tool_input: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON, nullable=True))
  tool_output: Optional[str] = None
  duration_ms: Optional[int] = None
  created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

  run: Optional["AgentRun"] = Relationship(back_populates="steps")

