import pytest
import asyncio
from app.services.rag_service import RAGService

@pytest.fixture
async def rag_service():
    
    service = RAGService()
    yield service

@pytest.mark.asyncio
async def test_add_documents(rag_service):
    """Test adding documents to RAG system"""
    documents = ["This is a test document about AI.", "Another document about machine learning."]
    metadata = [{"source": "test1"}, {"source": "test2"}]
    
    result = await rag_service.add_documents(documents, metadata)
    assert result == True

@pytest.mark.asyncio
async def test_query_documents(rag_service):
    """Test querying documents"""
    # First add some documents
    documents = ["Python is a programming language.", "Machine learning uses algorithms."]
    await rag_service.add_documents(documents)
    
    # Query the documents
    result = await rag_service.query_documents("What is Python?")
    
    assert "answer" in result
    assert "sources" in result
    assert "confidence" in result
    assert isinstance(result["sources"], list)

@pytest.mark.asyncio
async def test_get_document_stats(rag_service):
    """Test getting document statistics"""
    stats = await rag_service.get_document_stats()
    assert "total_documents" in stats