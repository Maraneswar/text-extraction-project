"""
Intelligent Document Processing System
FastAPI backend with async document processing.
"""
import os
import uuid
import time
import asyncio
from typing import Dict
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from config import UPLOAD_DIR, STATIC_DIR, MAX_FILE_SIZE_BYTES, ALLOWED_EXTENSIONS
from models.schemas import (
    UploadResponse, ProcessingResult, TaskStatus,
    ExtractionResult, DocumentMetadata,
)
from extractors.pdf_extractor import extract_pdf
from extractors.docx_extractor import extract_docx
from extractors.ocr_extractor import extract_image
from extractors.url_extractor import extract_url
from analyzers.summarizer import summarize_text
from analyzers.ner_extractor import extract_entities
from analyzers.sentiment import analyze_sentiment

# --- App Setup ---
app = FastAPI(
    title="Alldocex - Intelligent Document Processing",
    description="Extract, analyse, and summarize content from PDF, DOCX, and image files using AI.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory task store
tasks: Dict[str, ProcessingResult] = {}

# --- Utility Functions ---

def _human_readable_size(size_bytes: int) -> str:
    """Convert bytes to human readable string."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def _get_file_type(filename: str) -> str:
    """Determine file type from extension."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext == "pdf":
        return "pdf"
    elif ext == "docx":
        return "docx"
    elif ext in ("png", "jpg", "jpeg", "tiff", "bmp", "webp"):
        return "image"
    return "unknown"


def _process_document(file_path: str, file_type: str, task_id: str):
    """
    Process a document: extract text, then run all analyzers.
    This runs in a thread pool to avoid blocking the event loop.
    """
    start_time = time.time()
    task = tasks[task_id]
    task.status = TaskStatus.PROCESSING

    try:
        # Step 1: Extract text based on file type
        if file_type == "pdf":
            extraction = extract_pdf(file_path)
        elif file_type == "docx":
            extraction = extract_docx(file_path)
        elif file_type == "image":
            extraction = extract_image(file_path)
        elif file_type == "url":
            # file_path is the URL string here
            extraction = extract_url(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

        task.extraction = extraction

        if not extraction.success or not extraction.raw_text.strip():
            task.status = TaskStatus.COMPLETED
            task.error_message = extraction.error_message or "No text could be extracted."
            task.processing_time_ms = (time.time() - start_time) * 1000
            return

        raw_text = extraction.raw_text

        # Step 2: Summarization
        try:
            task.summary = summarize_text(raw_text)
        except Exception as e:
            print(f"Summarization error: {e}")

        # Step 3: Named Entity Recognition
        try:
            task.entities = extract_entities(raw_text)
        except Exception as e:
            print(f"NER error: {e}")

        # Step 4: Sentiment Analysis
        try:
            task.sentiment = analyze_sentiment(raw_text)
        except Exception as e:
            print(f"Sentiment error: {e}")

        task.status = TaskStatus.COMPLETED
        task.processing_time_ms = (time.time() - start_time) * 1000

    except Exception as e:
        task.status = TaskStatus.ERROR
        task.error_message = str(e)
        task.processing_time_ms = (time.time() - start_time) * 1000

    finally:
        # Clean up uploaded file
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass


# --- API Endpoints ---

@app.post("/api/upload", response_model=ProcessingResult)
async def upload_and_process(file: UploadFile = File(...)):
    """
    Upload a document and start processing.
    Supports PDF, DOCX, PNG, JPG, JPEG, TIFF, BMP, WEBP.
    """
    # Validate file extension
    filename = file.filename or "unknown"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: .{ext}. Supported: {', '.join(ALLOWED_EXTENSIONS.keys())}"
        )

    # Read file content
    content = await file.read()
    file_size = len(content)

    # Validate file size
    if file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE_BYTES // (1024*1024)}MB"
        )

    if file_size == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded.")

    # Save file
    file_id = str(uuid.uuid4())[:8]
    safe_filename = f"{file_id}_{filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    with open(file_path, "wb") as f:
        f.write(content)

    # Determine file type
    file_type = _get_file_type(filename)

    # Create task
    task = ProcessingResult.create_pending(
        file_id=file_id,
        filename=filename,
        file_type=file_type,
    )
    tasks[file_id] = task

    # Start async processing in a thread
    asyncio.get_event_loop().run_in_executor(
        None, _process_document, file_path, file_type, file_id
    )

    return task


@app.post("/api/extract/url", response_model=ProcessingResult)
async def extract_from_url(data: Dict[str, str]):
    """
    Extract content from a web URL and process it.
    """
    url = data.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="URL is required.")
    
    if not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="Invalid URL format. Must start with http:// or https://")

    # Create task
    file_id = str(uuid.uuid4())[:8]
    # For URLs, we use the domain as the "filename"
    filename = url.split('/')[2] if '//' in url else url.split('/')[0]
    
    task = ProcessingResult.create_pending(
        file_id=file_id,
        filename=filename,
        file_type="url",
    )
    tasks[file_id] = task

    # Start async processing in a thread
    asyncio.get_event_loop().run_in_executor(
        None, _process_document, url, "url", file_id
    )

    return task


@app.get("/api/status/{task_id}")
async def get_task_status(task_id: str):
    """Get the processing status and results for a task."""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found.")
    return tasks[task_id]


@app.get("/api/download/{task_id}")
async def download_results(task_id: str):
    """Download the extracted text as a .txt file."""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found.")
    
    task = tasks[task_id]
    if not task.extraction or not task.extraction.raw_text:
        raise HTTPException(status_code=400, detail="No text available for download.")
    
    # Create temporary file path
    filename = f"extracted_{task.filename}.txt"
    temp_path = os.path.join(UPLOAD_DIR, filename)
    
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(task.extraction.raw_text)
            
        return FileResponse(
            temp_path, 
            filename=filename, 
            media_type="text/plain",
            background=None # Note: ideally we'd use BackgroundTask to delete this file later
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate download: {str(e)}")


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    from config import check_ocr_availability

    # Check OCR status
    ocr_status = check_ocr_availability()

    # Check spaCy
    try:
        import spacy
        spacy.load("en_core_web_sm")
        spacy_status = "available"
    except Exception:
        spacy_status = "not available"

    return {
        "status": "healthy",
        "ocr": ocr_status,
        "tesseract": "available" if ocr_status in ("available", "tesseract-only") else "not found",
        "spacy": spacy_status,
        "version": "1.1.0",
    }


# --- Static Files ---

# Serve the main page
@app.get("/")
async def serve_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse({"message": "Alldocex API is running. Frontend not found."})


# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


if __name__ == "__main__":
    import uvicorn
    print("\n🚀 Alldocex - Intelligent Document Processing System")
    print("📄 Open http://localhost:7860 in your browser\n")
    uvicorn.run(app, host="0.0.0.0", port=7860)
