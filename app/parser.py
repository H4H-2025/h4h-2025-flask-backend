from werkzeug.datastructures import FileStorage
import fitz  
from docx import Document
import os
import logging
from typing import Optional
import tempfile

logger = logging.getLogger(__name__)

def parse_pdf(file: FileStorage) -> Optional[str]:
    pdf_document = None
    try:
        pdf_data = file.read()
        if not pdf_data:
            raise ValueError("Empty PDF file")
            
        pdf_document = fitz.open("pdf", pdf_data)
        if pdf_document.page_count == 0:
            raise ValueError("PDF has no pages")
            
        text_parts = []
        for page_num in range(pdf_document.page_count):
            page = pdf_document[page_num]
            text = page.get_text()
            if text:
                text_parts.append(text)
                
        return "\n".join(text_parts) if text_parts else None
        
    except Exception as e:
        logger.error(f"Error parsing PDF {file.filename}: {str(e)}")
        return None
    finally:
        if pdf_document:
            pdf_document.close()
        file.seek(0)  

def parse_docx(file: FileStorage) -> Optional[str]:
    try:
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as temp_file:
            file.save(temp_file.name)
            doc = Document(temp_file.name)
            
            text_parts = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():  
                    text_parts.append(paragraph.text)
                    
            return "\n".join(text_parts) if text_parts else None
            
    except Exception as e:
        logger.error(f"Error parsing DOCX {file.filename}: {str(e)}")
        return None
    finally:
        if 'temp_file' in locals():
            os.unlink(temp_file.name)
        file.seek(0)  

def parse_document(file: FileStorage) -> Optional[str]:
    if not file or not file.filename:
        raise ValueError("No file provided")
    
    try:
        file_extension = file.filename.rsplit('.', 1)[1].lower()
    except IndexError:
        raise ValueError("Invalid filename format")
    
    parser_map = {
        'pdf': parse_pdf,
        'docx': parse_docx,
        'doc': parse_docx
    }
    
    parser = parser_map.get(file_extension)
    if not parser:
        raise ValueError(f"Unsupported file type: {file_extension}")
        
    return parser(file)