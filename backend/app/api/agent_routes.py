from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.agent_schema import (
    AgentHealthResponse,
    AgentCreateSessionRequest,
    AgentSessionResponse,
    AgentChatRequest,
    AgentChatResponse,
    SituationReportRequest,
    UserRole,
)
from app.agent.orchestrator import agent_orchestrator
from app.agent.tools import situation_report_tool
from app.db.database import get_agent_session

router = APIRouter(prefix="/agent", tags=["Phase 6 — AI Decision-Support Agent"])


@router.get("/health", response_model=AgentHealthResponse, summary="Agent & Tool Health Check")
async def agent_health():
    return AgentHealthResponse(**agent_orchestrator.get_health_info())


@router.post("/sessions", response_model=AgentSessionResponse, summary="Create New Agent Session")
async def create_session(req: AgentCreateSessionRequest):
    ctx = req.location_context.model_dump(exclude_none=True) if req.location_context else {}
    sess = agent_orchestrator.start_session(
        role=req.role, user_id=req.user_id, location_context=ctx
    )
    return AgentSessionResponse(**sess)


@router.get("/sessions/{session_id}", response_model=AgentSessionResponse, summary="Retrieve Authorized Session History")
async def get_session_history(
    session_id: str,
    role: UserRole = Query("citizen"),
    user_id: Optional[str] = Query(None),
):
    sess = get_agent_session(session_id)
    if not sess:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )
    if sess["user_role"] != role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Role mismatch for requested session.",
        )
    if sess.get("user_id") and user_id and sess["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized access to another user's session.",
        )
    return AgentSessionResponse(
        session_id=sess["session_id"],
        role=sess["user_role"],
        user_id=sess.get("user_id"),
        location_context=sess.get("location_context", {}),
        messages=sess.get("messages", []),
        created_at=sess["created_at"],
        updated_at=sess["updated_at"],
    )


@router.post("/chat", response_model=AgentChatResponse, summary="Chat with GeoSense Decision-Support Agent")
async def chat_with_agent(req: AgentChatRequest):
    ctx = req.location_context.model_dump(exclude_none=True) if req.location_context else None
    try:
        res = await agent_orchestrator.chat(
            message=req.message,
            session_id=req.session_id,
            role=req.role,
            user_id=req.user_id,
            location_context=ctx,
        )
        return AgentChatResponse(**res)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/situation-report", summary="Generate Authorized District Situation Report")
async def generate_situation_report(req: SituationReportRequest):
    if req.role == "citizen":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Situation reports are restricted to Field Officers and Authorities.",
        )
    return await situation_report_tool(
        region_id=req.region_id,
        latitude=req.latitude,
        longitude=req.longitude,
        role=req.role,
    )
