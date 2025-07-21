import json
from fastapi import HTTPException
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from app.models.db_models import DocumentChunk
import logging

logger = logging.getLogger(__name__)

async def search_neon_chunks(query_embedding: list, user_id: int, pdf_ids: list = None, top_n: int = 5):
    """Searches NeonDB for similar documents using vector similarity with the <=> operator."""
    try:
        from app.core.database import NeonAsyncSessionLocal
        
        async with NeonAsyncSessionLocal() as neon_db:
            try:
                # Simple approach: use <=> operator for cosine similarity
                query = f"""
                    SELECT id, chunk_text, document_metadata 
                    FROM document_chunks
                    ORDER BY embedding <=> ARRAY{str(query_embedding)}::vector
                    LIMIT {top_n * 3}
                """
                
                result = await neon_db.execute(text(query))
                chunks = result.fetchall()
                await neon_db.commit()  # Explicitly commit successful transaction
                logger.info(f"Vector search successful, retrieved {len(chunks)} chunks")
                
            except Exception as e:
                await neon_db.rollback()  # Explicitly rollback failed transaction
                logger.error(f"Vector search query failed: {str(e)}")
                return []  # Return empty results on failure
            
            # Process results
            filtered_chunks = []
            for chunk in chunks:
                try:
                    metadata = json.loads(chunk.document_metadata)
                    chunk_user_id = metadata.get('user_id')
                    chunk_pdf_id = metadata.get('pdf_document_id')
                    
                    # Match string representations for consistent comparison
                    if chunk_user_id != str(user_id):
                        continue
                        
                    if pdf_ids and chunk_pdf_id not in [str(pdf_id) for pdf_id in pdf_ids]:
                        continue
                    
                    # Extract a meaningful preview from the larger text
                    document_text = chunk.chunk_text
                    preview_text = document_text[:1000] + "..." if len(document_text) > 1000 else document_text
                    
                    filtered_chunks.append({
                        'text': preview_text,
                        'metadata': metadata
                    })
                    
                    if len(filtered_chunks) >= top_n:
                        break
                        
                except Exception as e:
                    logger.error(f"Error processing chunk metadata: {str(e)}")
            
            # Format results with source information
            return [f"[Source: {chunk['metadata'].get('filename', 'Unknown')}]\n{chunk['text']}" 
                   for chunk in filtered_chunks]
                   
    except Exception as e:
        logger.error(f"Error searching NeonDB documents: {str(e)}", exc_info=True)
        return []