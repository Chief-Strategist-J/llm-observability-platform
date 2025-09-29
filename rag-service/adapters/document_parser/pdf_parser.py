import fitz  # PyMuPDF
from typing import AsyncIterator
from core.ports.document_parser import DocumentParserPort

class PDFParser(DocumentParserPort):
    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    async def parse(self, file_bytes: bytes) -> str:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text = "\n\n".join(page.get_text() for page in doc)
        doc.close()
        return text

    async def chunk(self, text: str) -> AsyncIterator[str]:
        words = text.split()
        step = self.chunk_size - self.overlap
        for i in range(0, len(words), step):
            chunk = " ".join(words[i:i + self.chunk_size])
            if len(chunk) > 50:
                yield chunk
