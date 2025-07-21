from fastapi import HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
import time
import json
from app.services import neon_service, tavily_service, gemini_service, embedding_service
from app.models.chat_models import ChatRequest
from app.models import db_models
import logging
from typing import Optional

logger = logging.getLogger(__name__)
_anonymous_message_counts = {}

async def chat_stream_handler(
    chat_req: ChatRequest, 
    request: Request, 
    db: Session, 
    current_user: Optional[db_models.User],
    anonymous_session_id: Optional[str] = None
) -> StreamingResponse:
    """Handles the chat stream logic for both authenticated and anonymous users."""
    query = chat_req.query
    start_time = time.time()
    session_id = chat_req.session_id
    
    # Create or get chat session
    if current_user:
        # Authenticated user flow (existing code)
        if session_id:
            session_result = await db.execute(
                select(db_models.ChatSession).filter(
                    db_models.ChatSession.id == session_id, 
                    db_models.ChatSession.user_id == current_user.id
                )
            )
            chat_session = session_result.scalar_one_or_none()
            if not chat_session:
                raise HTTPException(status_code=404, detail="Chat session not found or not owned by user")
            chat_session_id = session_id
            
            # Retrieve PDFs associated with this session
            session_pdfs_result = await db.execute(
                select(db_models.ChatSessionPDF.pdf_document_id).where(
                    db_models.ChatSessionPDF.chat_session_id == chat_session_id
                )
            )
            context_pdfs = [pdf_id for pdf_id, in session_pdfs_result]
        else:
            # Create new session for authenticated user
            chat_session = db_models.ChatSession(user_id=current_user.id)
            db.add(chat_session)
            await db.commit()
            await db.refresh(chat_session)
            chat_session_id = chat_session.id
            context_pdfs = []
    else:
        # Anonymous user flow
        chat_session_id = f"anon_{anonymous_session_id}"
        context_pdfs = []
        
        # For anonymous users, no need to store in DB, just track in memory or Redis
        # You could use a lightweight Redis or in-memory store to track anonymous sessions
        
    # Continue with the existing code...
    chat_history_str = await get_chat_history_str(db, chat_session_id) if current_user else ""
    
    # PDF context processing
    pdf_context = ""
    if current_user and context_pdfs:
        # Only authenticated users can access PDFs
        try:
            query_embedding = embedding_service.get_embedding(query)
            
            # Pass user_id and pdf_ids to ensure proper filtering
            retrieved_chunks = await neon_service.search_neon_chunks(
                query_embedding=query_embedding,
                user_id=current_user.id,
                pdf_ids=context_pdfs,
                top_n=5
            )
            
            if retrieved_chunks:
                pdf_context = "Here are the most relevant sections from your documents:\n\n" + \
                            "\n\n".join(retrieved_chunks)
            else:
                pdf_context = "No relevant information found in the specified documents."
                
        except Exception as e:
            logger.error(f"Error retrieving PDF context: {str(e)}", exc_info=True)
            pdf_context = "Error retrieving PDF context from your documents."
    
    # Search context if requested
    tavily_context = ""
    if chat_req.isSearchMode:
        tavily_info = tavily_service.fetch_tavily_data(query)
        tavily_context = json.dumps(tavily_info) if isinstance(tavily_info, dict) else str(tavily_info)
        if not tavily_context:
            tavily_context = "No additional web info found."

    prompt = f"""
    You are a helpful assistant. Answer the user's question based on the provided information.

    {chat_req.isSearchMode and f'''
    **Web Search Results:**
    {tavily_context}
    ''' or ''}

    **Document Context:**
    {pdf_context}

    **Chat History:**
    {chat_history_str}

    **User Question:** {query}

    Instructions:
    1. Maintain the conversation flow by referring to previous exchanges when relevant.
    3. When including code snippets:
    - Use triple backticks with the language name for syntax highlighting (```python, ```javascript, etc.)
    - Ensure code is properly indented and follows best practices
    - Add brief comments explaining key parts of the code
    - For React code, use ```jsx for proper syntax highlighting
    4. Provide clear explanations and examples to help the user understand the topic.
    5. Provide Code examples when possible to help the user implement the solution.
    6. If you need more information, ask the user for clarification.
    7. If you need to search the web for more information, let the user know."""

    print(prompt)
    async def sse_generator():
        
        current_count = 0
        if not current_user and anonymous_session_id:
            current_count = await get_anonymous_message_count(anonymous_session_id)

        # Send metadata with session ID first
        metadata = {
            "search": tavily_context, 
            "duration": time.time() - start_time, 
            "chat_session_id": chat_session_id if current_user else None,
            "anonymous": current_user is None,
            "message_count": current_count if not current_user else None
        }
        yield f"data: {json.dumps({'type': 'metadata', 'data': metadata})}\n\n"

        full_answer = ""

        # Stream the model response
        async for chunk in gemini_service.generate_response_with_gemini_streaming(prompt):
            if await request.is_disconnected():
                logger.info("Client disconnected, stopping stream.")
                break
            
            # Parse the chunk and extract text
            try:
                chunk_data = json.loads(chunk.removeprefix("data: ").removesuffix("\n\n"))
                chunk_text = chunk_data.get('text', '')
                full_answer += chunk_text
                
                # Send chunk as SSE
                yield f"data: {json.dumps({'type': 'content', 'text': chunk_text})}\n\n"
            except Exception as e:
                logger.error(f"Error processing chunk: {e}")
                continue

        # Save messages for authenticated users only
        if current_user:
            # Save the messages to the database (existing code)
            user_message = db_models.ChatMessage(
                session_id=chat_session_id, 
                user_id=current_user.id, 
                content=query, 
                is_user_message=True
            )

            search_data_str = tavily_context if chat_req.isSearchMode else None

            bot_message = db_models.ChatMessage(
                session_id=chat_session_id, 
                user_id=None, 
                content=full_answer, 
                is_user_message=False,
                search_data=search_data_str
            )
            db.add_all([user_message, bot_message])
            await db.commit()
        
        # Send completion notification
        yield f"data: {json.dumps({'type': 'end'})}\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")

async def get_chat_history_str(db: Session, chat_session_id: int) -> str:
    """Retrieves and formats chat history as a string."""

    from sqlalchemy import select as sqlalchemy_select
    chat_history = []
    if chat_session_id:
        query = sqlalchemy_select(db_models.ChatMessage).where(
            db_models.ChatMessage.session_id == chat_session_id
        ).order_by(db_models.ChatMessage.created_at.desc()).limit(10)
        
        # Execute the query
        messages_result = await db.execute(query)
        messages = messages_result.scalars().all()
        messages = list(reversed(messages))
        
        for msg in messages:
            role = "user" if msg.is_user_message else "assistant"
            chat_history.append(f"{role}: {msg.content}")
    
    return "\n".join(chat_history) if chat_history else "No previous messages in this chat."


async def get_anonymous_message_count(anonymous_session_id: str) -> int:
    """Track and return the number of messages sent by an anonymous user."""
    global _anonymous_message_counts
    
    current_count = _anonymous_message_counts.get(anonymous_session_id, 0)
    _anonymous_message_counts[anonymous_session_id] = current_count + 1
    
    return current_count