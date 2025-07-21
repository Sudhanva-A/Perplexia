from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services import pdf_service
from app.models import db_models
from sqlalchemy import select, delete
from app.api import auth
import logging

router = APIRouter()

logger = logging.getLogger(__name__)

@router.post("/upload", response_model=dict)
async def upload_pdf_for_user(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db), 
    current_user: db_models.User = Depends(auth.get_current_user)
):
    """Uploads a PDF and associates it with the logged-in user."""
    # File validation
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
        
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:
        # Read the file once to check size
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(status_code=400, detail="File too large (max 10MB)")
        
        # Reset file pointer
        await file.seek(0)
        
        # Process the PDF
        return await pdf_service.process_pdf_and_store(file, current_user.id, db)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in upload_pdf_for_user: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to upload PDF: {str(e)}")

# Add endpoints for listing PDFs, deleting PDFs, adding/removing from chats, etc.
# Example:
@router.get("/list", response_model=list[dict])
async def list_user_pdfs(
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(auth.get_current_user)
):
    """List user PDFs endpoint - now calling the handler."""
    return await pdf_service.list_user_pdfs_handler(current_user, db) 

@router.post("/sessions/{session_id}/add_pdf/{pdf_id}", response_model=dict)
async def add_pdf_to_session(
    session_id: int,
    pdf_id: int,
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(auth.get_current_user)
):
    """Adds a PDF to a chat session context."""
    # Verify the session belongs to the user
    session_result = await db.execute( # Async DB query
        select(db_models.ChatSession)
        .filter(db_models.ChatSession.id == session_id, db_models.ChatSession.user_id == current_user.id)
    )
    session = session_result.scalar_one_or_none() # Get single scalar result or None

    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    # Verify the PDF belongs to the user
    pdf_result = await db.execute( # Async DB query
        select(db_models.PDFDocument)
        .filter(db_models.PDFDocument.id == pdf_id, db_models.PDFDocument.user_id == current_user.id)
    )
    pdf = pdf_result.scalar_one_or_none() # Get single scalar result or None

    if not pdf:
        raise HTTPException(status_code=404, detail="PDF document not found")

    # Check if association already exists
    existing_result = await db.execute( # Async DB query
        select(db_models.ChatSessionPDF)
        .filter(db_models.ChatSessionPDF.chat_session_id == session_id, db_models.ChatSessionPDF.pdf_document_id == pdf_id)
    )
    existing = existing_result.scalar_one_or_none() # Get single scalar result or None

    if existing:
        return {"message": "PDF already added to this session"}

    # Create the association
    session_pdf = db_models.ChatSessionPDF(chat_session_id=session_id, pdf_document_id=pdf_id)
    db.add(session_pdf)
    await db.commit() # Async commit

    return {"message": "PDF added to chat session successfully"}

@router.delete("/sessions/{session_id}/remove_pdf/{pdf_id}", response_model=dict)
async def remove_pdf_from_session(
    session_id: int,
    pdf_id: int,
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(auth.get_current_user)
):
    """Removes a PDF from a chat session context."""
    # Verify the session belongs to the user
    session_result = await db.execute(
        select(db_models.ChatSession)
        .filter(db_models.ChatSession.id == session_id, db_models.ChatSession.user_id == current_user.id)
    )
    session = session_result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    try:
        # First find the association
        assoc_result = await db.execute(
            select(db_models.ChatSessionPDF)
            .filter(
                db_models.ChatSessionPDF.chat_session_id == session_id,
                db_models.ChatSessionPDF.pdf_document_id == pdf_id
            )
        )
        assoc = assoc_result.scalar_one_or_none()
        
        # Check if association exists
        if not assoc:
            raise HTTPException(status_code=404, detail="PDF not associated with this session")
        
        # Delete the association by object rather than using a delete statement
        await db.delete(assoc)
        await db.commit()
        
        return {"message": "PDF removed from chat session successfully"}
            
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error removing PDF from session: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error removing PDF: {str(e)}")

@router.get("/sessions/{session_id}/pdfs", response_model=list[dict])
async def list_session_pdfs(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(auth.get_current_user)
):
    """Lists all PDFs associated with a chat session."""
    # Verify the session belongs to the user
    session_result = await db.execute( # Async DB query
        select(db_models.ChatSession)
        .filter(db_models.ChatSession.id == session_id, db_models.ChatSession.user_id == current_user.id)
    )
    session = session_result.scalar_one_or_none() # Get single scalar result or None
    if not session:
       raise HTTPException(status_code=404, detail="Chat session not found")

    # Get all PDFs associated with the session - Async query with join
    pdfs_result = await db.execute(
        select(db_models.PDFDocument).
        join(db_models.ChatSessionPDF,
             db_models.ChatSessionPDF.pdf_document_id == db_models.PDFDocument.id).
        filter(db_models.ChatSessionPDF.chat_session_id == session_id)
    )
    pdfs = pdfs_result.scalars().all() # Get scalar results

    return [{
        "id": pdf.id,
        "filename": pdf.filename,
        "upload_date": pdf.upload_date
    } for pdf in pdfs]