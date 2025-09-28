from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import uuid
from services.pdf_processor import PDFProcessor
from services.embedding_service import EmbeddingService
from services.qdrant_service import QdrantService
from core.models import Document

router: APIRouter = APIRouter(prefix="/upload", tags=["upload"])

@router.post("/pdf")
async def upload_pdf(file: UploadFile = File(...)) -> JSONResponse:
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")
    
    try:
        pdf_bytes: bytes = await file.read()
        
        processor: PDFProcessor = PDFProcessor()
        text: str = processor.extract_text(pdf_bytes)
        chunks: list[str] = processor.chunk_text(text)
        
        embedding_service: EmbeddingService = EmbeddingService()
        embeddings: list[list[float]] = embedding_service.embed_batch(chunks)
        
        documents: list[Document] = []
        for i, chunk in enumerate(chunks):
            doc: Document = Document(
                id=f"{file.filename}_{i}",
                text=chunk,
                metadata={"filename": file.filename, "chunk": i}
            )
            documents.append(doc)
        
        qdrant_service: QdrantService = QdrantService()
        success: bool = qdrant_service.upsert_documents(documents, embeddings)
        
        if success:
            return JSONResponse({
                "message": "PDF processed successfully",
                "chunks": len(chunks),
                "filename": file.filename
            })
        else:
            raise HTTPException(status_code=500, detail="Failed to store embeddings")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
