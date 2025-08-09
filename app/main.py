from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from typing import List
import uvicorn
from app.core.config import settings
from app.core.security import SecurityService
from app.services.rag_service import RAGService
from app.services.document_service import DocumentService
from app.services.aws_service import AWSService
from app.models.query import QueryRequest, QueryResponse
from app.models.document import DocumentResponse

app = FastAPI(
    title=settings.app_name,
    description="Enterprise RAG System for Abdul Hadi's Portfolio",
    version="1.0.0"
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

rag_service = RAGService()
document_service = DocumentService()
aws_service = AWSService()

@app.on_event("startup")
async def startup_event():
    await aws_service.setup_infrastructure()

@app.get("/")
async def root():
    return{
        "message": "Welcome to the Enterprise RAG System API",
        "version": "1.0.0",
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    aws_health = await aws_service.get_service_health()
    doc_status = await rag_service.get_document_status()

    return {
        "status": "healthy",
        "services": {
            "rag": "healthy",
            "aws": aws_health,
            "documents": doc_status
        }
    }

@app.post("/auth/token")
async def create_token(username: str, password: str):
    if username == "demo" and password == "demo123": #dummy credentials
        token = SecurityService.create_access_token({"sub": username})
        return {"access_token": token, "token_type": "bearer"}
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials"
    )

@app.post("/documents/upload", response_model=DocumentResponse)
@limiter.limit("5/minute")
async def upload_document(
    request: any,
    file: UploadFile = File(...),
    token: str = Depends(security)
):
    try:
        SecurityService.verify_token(token.credentials)
        document_data = await document_service.process_upload_file(file)

        if not document_service.validate_document_content(document_data["text"]):
            raise HTTPException(
                status_code=400,
                detail="Document content is not valid"
            )
        
        success = await rag_service.add_document(
            [document_data["text"]],
            [{"filename": document_data["filename"], "type": document_data["type"]}]
        )

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to add document to RAG system"
            )
        
        await aws_service.store_document(
            document_data["filename"],
            document_data["text"],
            {"original_filename": document_data["original_filename"]}
        )

        return DocumentResponse(
            id=document_data["filename"],
            filename=document_data["original_filename"],
            size=document_data["size"],
            type=document_data["type"],
            status="processed"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    
@app.post("/query", response_model=QueryResponse)
@limiter.limit("10/minute")
async def query_documents(
    request: any,
    query_request: QueryRequest,
    token: str = Depends(security)
):
    try:
        SecurityService.verify_token(token.credentials)

        result = await rag_service.query_documents(
            query_request.question,
            k=query_request.max_results
        )

        return QueryResponse(
            question=query_request.question,
            answer=result["answer"],
            sources=result["sources"],
            confidence=result["confidence"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    
@app.get("/documents")
@limiter.limit("20/minute")
async def list_documents(
    request: any,
    token: str = Depends(security)
):
    
    try:
        SecurityService.verify_token(token.credentials)

        documents = await aws_service.list_documents()

        return {"documents": documents, "count": len(documents)}
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)