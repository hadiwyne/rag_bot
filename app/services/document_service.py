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

    @staticmethod
    def _validate_file(file: UploadFile) -> bool:
        if not file.filename:
            return False
        
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in DocumentService.ALLOWED_EXTENSIONS:
            return False
    
        return True
    
    @staticmethod
    def _extract_pdf_text(content: bytes) -> str:
        try:
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                tmp_file.write(content)
                tmp_file_path = tmp_file.name
            
            text = ""
            with open(tmp_file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            
            # Clean up
            os.unlink(tmp_file_path)
            
            return text.strip()
        except Exception as e:
            raise Exception(f"Error extracting PDF text: {str(e)}")
    @staticmethod
    def _extract_docx_text(content: bytes) -> str:
        try:
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                tmp_file.write(content)
                tmp_file_path = tmp_file.name

            doc = docx.Document(tmp_file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"

            os.unlink(tmp_file_path)

            return text.strip()
        except Exception as e:
            raise Exception(f"Error extracting DOCX text: {str(e)}")
        
    @staticmethod
    def validate_document_content(text:str) -> bool:
        if not text or len(text.strip()) < 10:
            return False
        
        suspicious_patterns =['<script', 'javascript', 'eval(', 'exec(']
        text_lower = text.lower()

        for pattern in suspicious_patterns:
            if pattern in text_lower:
                return False
            

        return True