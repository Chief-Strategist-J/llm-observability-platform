import fitz
from typing import List
from io import BytesIO
import gc

class PDFProcessor:
    def extract_text(self, pdf_bytes: bytes) -> str:
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            text: str = ""
            
            total_pages: int = len(doc)
            
            for page_num in range(total_pages):
                page = doc[page_num]
                page_text: str = page.get_text()
                text += page_text + "\n"
                
                if page_num % 50 == 0:
                    gc.collect()
            
            doc.close()
            gc.collect()
            
            return text.strip()
        except Exception as e:
            raise Exception(f"PDF extraction failed: {str(e)}")
    
    def chunk_text(self, text: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
        if not text.strip():
            return []
            
        words: List[str] = text.split()
        chunks: List[str] = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk_words: List[str] = words[i:i + chunk_size]
            chunk: str = " ".join(chunk_words)
            
            if chunk.strip():
                chunks.append(chunk.strip())
        
        return chunks
