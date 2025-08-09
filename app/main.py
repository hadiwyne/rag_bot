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