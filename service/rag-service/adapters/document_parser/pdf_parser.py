"""PDF document parser for RAG service.

This module provides PDF parsing capabilities using PyMuPDF (fitz).

"""

from collections.abc import AsyncIterator

import fitz  # PyMuPDF

from ...core.ports.document_parser import DocumentParserPort


class PDFParser(DocumentParserPort):
    """
    PDF document parser implementation.
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        """Initialize PDF parser.

        Args:
            chunk_size: Maximum number of words per chunk
            overlap: Number of overlapping words between chunks

        """
        self.chunk_size = chunk_size
        self.overlap = overlap

    async def parse(self, file_bytes: bytes) -> str:
        """Parse PDF document from bytes.

        Args:
            file_bytes: PDF file content as bytes

        Returns:
            Extracted text content from PDF

        """
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text = "\n\n".join(page.get_text() for page in doc)
        doc.close()
        return text

    async def chunk(self, text: str) -> AsyncIterator[str]:
        """Split text into chunks for processing.

        Args:
            text: Text content to chunk

        Yields:
            Text chunks of specified size with overlap

        """
        words = text.split()
        step = self.chunk_size - self.overlap
        for i in range(0, len(words), step):
            chunk = " ".join(words[i : i + self.chunk_size])
            if len(chunk) > 50:
                yield chunk
