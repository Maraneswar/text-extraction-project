import os
import shutil
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- File Upload Settings ---
MAX_FILE_SIZE_MB = 50
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_EXTENSIONS = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "tiff": "image/tiff",
    "bmp": "image/bmp",
    "webp": "image/webp",
}

# --- OCR Configuration ---
# EasyOCR settings
EASYOCR_LANGS = ["en"]  # Languages to support
EASYOCR_GPU = False      # Set to True if NVIDIA GPU is available and CUDA is installed

# Keep Tesseract as fallback if needed, but prioritize EasyOCR for accuracy
def find_tesseract():
    """Auto-detect Tesseract installation path on Windows."""
    import shutil
    tesseract_in_path = shutil.which("tesseract")
    if tesseract_in_path:
        return tesseract_in_path

    common_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Users\{}\AppData\Local\Tesseract-OCR\tesseract.exe".format(os.getenv("USERNAME", "")),
    ]
    for path in common_paths:
        if os.path.isfile(path):
            return path
    return None

TESSERACT_CMD = find_tesseract()
TESSERACT_LANG = "eng"

def check_ocr_availability():
    """Check if any OCR engine is available."""
    try:
        import easyocr
        return "available"
    except ImportError:
        if TESSERACT_CMD:
            return "tesseract-only"
        return "not-found"

# --- Summarization Settings ---
SUMMARY_SENTENCE_COUNT = 5
SUMMARY_ALGORITHM = "lex-rank"  # Options: lex-rank, lsa, luhn, edmundson

# --- NER Settings ---
SPACY_MODEL = "en_core_web_sm"
NER_ENTITY_TYPES = ["PERSON", "ORG", "DATE", "MONEY", "GPE", "EVENT", "PRODUCT", "LAW", "NORP"]

# --- Sentiment Settings ---
SENTIMENT_THRESHOLDS = {
    "positive": 0.05,
    "negative": -0.05,
}

# --- Gemini AI Configuration ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# API access key for external clients
API_ACCESS_KEY = (
    os.getenv("API_ACCESS_KEY") or
    os.getenv("VALID_API_KEY") or
    os.getenv("API_KEY") or
    "alldocex-test-key-2024"  # Default key for the Endpoint Tester
)

def is_api_key_valid(key: str) -> bool:
    return bool(API_ACCESS_KEY and key and key.strip() == API_ACCESS_KEY)

# Flag to check if Gemini is configured
def is_gemini_available():
    return bool(GEMINI_API_KEY)
