from __future__ import annotations

import uuid
from collections.abc import Generator

from fastapi import Depends, FastAPI, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models import Workflow
from app.schemas import WorkflowCreate, WorkflowResponse

app = FastAPI(title=settings.app_name)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def to_workflow_response(workflow: Workflow) -> WorkflowResponse:
    steps = workflow.config_json.get("steps", []) if isinstance(workflow.config_json, dict) else []
    return WorkflowResponse(
        id=workflow.id,
        name=workflow.name,
        base_url=workflow.base_url,
        steps=steps,
        latency_threshold_ms=workflow.latency_threshold_ms,
        created_at=workflow.created_at,
    )


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/workflows", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED, tags=["workflows"])
def create_workflow(payload: WorkflowCreate, db: Session = Depends(get_db)) -> WorkflowResponse:
    workflow = Workflow(
        name=payload.name,
        base_url=payload.base_url,
        config_json=payload.model_dump(),
        latency_threshold_ms=payload.latency_threshold_ms,
    )
    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    return to_workflow_response(workflow)


@app.get("/workflows", response_model=list[WorkflowResponse], tags=["workflows"])
def list_workflows(db: Session = Depends(get_db)) -> list[WorkflowResponse]:
    workflows = db.query(Workflow).order_by(Workflow.created_at.desc()).all()
    return [to_workflow_response(workflow) for workflow in workflows]


@app.get("/workflows/{workflow_id}", response_model=WorkflowResponse, tags=["workflows"])
def get_workflow(workflow_id: uuid.UUID, db: Session = Depends(get_db)) -> WorkflowResponse:
    workflow = db.get(Workflow, workflow_id)
    if workflow is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    return to_workflow_response(workflow)


@app.delete("/workflows/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["workflows"])
def delete_workflow(workflow_id: uuid.UUID, db: Session = Depends(get_db)) -> Response:
    workflow = db.get(Workflow, workflow_id)
    if workflow is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    db.delete(workflow)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
