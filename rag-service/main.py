from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from api.routes import upload_pdf, search_rag
from core.config import settings

app: FastAPI = FastAPI(
    title="RAG Service", 
    version="1.0.0",
    timeout=300
)

app.include_router(upload_pdf.router)
app.include_router(search_rag.router)

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
