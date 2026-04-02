"""
PDF text extraction using PyMuPDF (fitz).
Extracts text with layout preservation and document metadata.
"""
import fitz  # PyMuPDF
import time
import os
from models.schemas import ExtractionResult, DocumentMetadata


def extract_pdf(file_path: str) -> ExtractionResult:
    """Extract text and metadata from a PDF file."""
    start_time = time.time()

    try:
        doc = fitz.open(file_path)

        # Extract text from all pages with full layout preservation
        pages_text = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            # "layout" mode preserves the physical positioning of text (columns, tables, etc.)
            # This ensures the "pointer position" matches the original PDF look.
            text = page.get_text("layout")
            if text.strip():
                pages_text.append(f"--- Page {page_num + 1} ---\n{text}")

        full_text = "\n\n".join(pages_text)

        # Extract metadata
        meta = doc.metadata
        metadata = DocumentMetadata(
            title=meta.get("title", "") or os.path.basename(file_path),
            author=meta.get("author", "") or "Unknown",
            creation_date=meta.get("creationDate", ""),
            modification_date=meta.get("modDate", ""),
            page_count=len(doc),
            word_count=len(full_text.split()) if full_text else 0,
            character_count=len(full_text),
            file_type="PDF",
            extra={
                "producer": meta.get("producer", ""),
                "creator": meta.get("creator", ""),
                "subject": meta.get("subject", ""),
                "keywords": meta.get("keywords", ""),
                "format": meta.get("format", ""),
                "encryption": doc.is_encrypted,
            }
        )

        doc.close()

        elapsed = (time.time() - start_time) * 1000

        if not full_text.strip():
            return ExtractionResult(
                raw_text="",
                metadata=metadata,
                success=False,
                error_message="No extractable text found in PDF. The document may contain only images — try uploading as an image for OCR processing.",
                extraction_time_ms=elapsed,
            )

        return ExtractionResult(
            raw_text=full_text,
            metadata=metadata,
            success=True,
            extraction_time_ms=elapsed,
        )

    except Exception as e:
        elapsed = (time.time() - start_time) * 1000
        return ExtractionResult(
            raw_text="",
            metadata=DocumentMetadata(file_type="PDF"),
            success=False,
            error_message=f"PDF extraction failed: {str(e)}",
            extraction_time_ms=elapsed,
        )
