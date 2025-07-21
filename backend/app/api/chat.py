from typing import Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
import time
import json
from sqlalchemy import select, delete  # Add proper imports
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.chat_models import ChatRequest
from app.services import neon_service, tavily_service, gemini_service, embedding_service
from app.models import db_models
from app.api import auth # Import your auth dependency/function
from app.services import chat_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/stream", response_class=StreamingResponse)
async def chat_stream_endpoint(
    chat_req: ChatRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[db_models.User] = Depends(auth.get_optional_current_user)
):
    """Chat stream endpoint that works for both authenticated and anonymous users."""
    # Check anonymous message limit if user is not authenticated
    if not current_user:
        # Get anonymous session from cookies or create one
        anonymous_session_id = request.cookies.get("anonymous_session_id")
        
        if not anonymous_session_id:
            # First message from this anonymous user
            anonymous_session_id = str(uuid.uuid4())
        else:
            # Check message count for this anonymous session
            message_count = await chat_service.get_anonymous_message_count(db, anonymous_session_id)
            if message_count >= 3:
                # Limit reached, return 403 error
                raise HTTPException(
                    status_code=403,
                    detail="Message limit reached for anonymous users. Please sign in to continue chatting."
                )
    
    response = await chat_service.chat_stream_handler(chat_req, request, db, current_user, anonymous_session_id if not current_user else None)
    
    # If anonymous user, set cookie with session ID
    if not current_user:
        response.set_cookie(
            key="anonymous_session_id",
            value=anonymous_session_id,
            httponly=True,
            max_age=60*60*24*7,  # 1 week
            samesite="lax"
        )
    
    return response


@router.get("/sessions", response_model=list[dict]) 
async def list_chat_sessions(db: Session = Depends(get_db), current_user: db_models.User = Depends(auth.get_current_user)):
    """Lists all chat sessions for the current user."""
    # Use a join with GROUP BY to efficiently get session counts in a single query
    from sqlalchemy import func
    
    query = select(
        db_models.ChatSession.id,
        db_models.ChatSession.name,
        db_models.ChatSession.created_at,
        func.count(db_models.ChatMessage.id).label('message_count')
    ).outerjoin(
        db_models.ChatMessage, 
        db_models.ChatSession.id == db_models.ChatMessage.session_id
    ).where(
        db_models.ChatSession.user_id == current_user.id
    ).group_by(
        db_models.ChatSession.id
    ).order_by(db_models.ChatSession.created_at.desc())
    
    result = await db.execute(query)
    sessions = result.all()
    
    return [{
        "id": session.id,
        "name": session.name,
        "created_at": session.created_at,
        "message_count": session.message_count
    } for session in sessions]

@router.post("/sessions", response_model=dict)
async def create_chat_session(
    session_data: dict,
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(auth.get_current_user)
):
    """Creates a new chat session."""
    # Create a new session with optional name from request data
    name = session_data.get("name", "New Chat")
    
    # Create the session
    chat_session = db_models.ChatSession(
        user_id=current_user.id,
        name=name
    )
    db.add(chat_session)
    await db.commit()
    await db.refresh(chat_session)
    
    return {
        "id": chat_session.id,
        "name": chat_session.name,
        "created_at": chat_session.created_at,
        "message_count": 0
    }

@router.get("/sessions/{session_id}", response_model=dict) 
async def get_chat_session(session_id: int, db: Session = Depends(get_db), current_user: db_models.User = Depends(auth.get_current_user)):
    """Gets details of a specific chat session including messages."""
    # Use selectinload to eagerly load the messages
    query = select(db_models.ChatSession).where(
        db_models.ChatSession.id == session_id,
        db_models.ChatSession.user_id == current_user.id
    )
    result = await db.execute(query)
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    # Explicitly load messages to avoid lazy loading issues
    messages_query = select(db_models.ChatMessage).where(
        db_models.ChatMessage.session_id == session_id
    ).order_by(db_models.ChatMessage.created_at)
    messages_result = await db.execute(messages_query)
    messages = messages_result.scalars().all()

    return {
        "id": session.id,
        "name": session.name,
        "created_at": session.created_at,
        "messages": [{
            "id": msg.id,
            "content": msg.content,
            "is_user_message": msg.is_user_message,
            "created_at": msg.created_at,
            "searchData": msg.search_data 
        } for msg in messages]
    }

@router.put("/sessions/{session_id}", response_model=dict) 
async def update_chat_session(
    session_id: int,
    session_data: dict,
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(auth.get_current_user)
):
    """Updates chat session properties (e.g., name)."""
    query = select(db_models.ChatSession).where(
        db_models.ChatSession.id == session_id,
        db_models.ChatSession.user_id == current_user.id
    )
    result = await db.execute(query)
    session = result.scalar_one_or_none() # Get single scalar result or None

    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    if "name" in session_data:
        session.name = session_data["name"]

    await db.commit() # Async commit

    return {"id": session.id, "name": session.name, "created_at": session.created_at}

@router.delete("/sessions/{session_id}", response_model=dict)
async def delete_chat_session(session_id: int, db: Session = Depends(get_db), current_user: db_models.User = Depends(auth.get_current_user)):
    """Deletes a chat session and all its messages."""
    query = select(db_models.ChatSession).where(
        db_models.ChatSession.id == session_id,
        db_models.ChatSession.user_id == current_user.id
    )
    result = await db.execute(query)
    session = result.scalar_one_or_none() # Get single scalar result or None

    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    # Delete all messages in the session - Async delete
    delete_messages = delete(db_models.ChatMessage).where(
        db_models.ChatMessage.session_id == session_id
    )
    await db.execute(delete_messages)

    # Delete session-PDF associations if you added those - Async delete
    delete_pdf_assoc = delete(db_models.ChatSessionPDF).where(
        db_models.ChatSessionPDF.chat_session_id == session_id
    )
    await db.execute(delete_pdf_assoc)

    # Delete the session itself
    await db.delete(session)
    await db.commit() # Async commit

    return {"message": "Chat session and all associated messages deleted successfully"}