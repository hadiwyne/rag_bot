import os
import tempfile
from typing import List, Optional
import PyPDF2
import docx
from fastapi import UploadFile, HTTPException
from app.core.config import settings
from app.core.security import SecurityService

class DocumentService:
    ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.txt'}
    MAX_FILE_SIZE = settings.max_document_size_mb * 1024 * 1024  # Convert MB to bytes

    @staticmethod
    async def process_upload_file(file: UploadFile) -> dict:
        try:
            if not DocumentService._validate_file(file):
                raise HTTPException(status_code=400, detail="Invalid file type or size.")
            
            cotnent = await file.read()

            file_extension = os.path.splitext(file.filename)[1].lower()

            if file_extension == '.pdf':
                text = DocumentService._extract_text_from_pdf(cotnent)
            elif file_extension == '.docx':
                text = DocumentService._extract_text_from_docx(cotnent)
            elif file_extension == '.txt':
                text = cotnent.decode('utf-8')
            else:
                raise HTTPException(status_code=400, detail="Unsupported file type.")
            
            secure_filename = SecurityService.secure_filename(file.filename)

            return{
                "filename": secure_filename,
                "content": text,
                "size": len(cotnent),
                "type": file_extension
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")