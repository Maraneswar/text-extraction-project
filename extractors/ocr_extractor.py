"""
Image OCR extraction using EasyOCR (primary) and Tesseract (fallback).
Includes advanced image preprocessing for maximum accuracy.
"""
import time
import os
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from models.schemas import ExtractionResult, DocumentMetadata
import config

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# --- OCR Engine Detection ---

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False


# Global reader instance for EasyOCR (lazy loaded)
_EASY_READER = None

def get_easyocr_reader():
    """Get or create the EasyOCR reader instance."""
    global _EASY_READER
    if _EASY_READER is None and EASYOCR_AVAILABLE:
        try:
            # Initialize with configured languages and GPU setting
            _EASY_READER = easyocr.Reader(config.EASYOCR_LANGS, gpu=config.EASYOCR_GPU)
        except Exception as e:
            print(f"Error initializing EasyOCR: {e}")
            return None
    return _EASY_READER


def _configure_tesseract():
    """Configure tesseract path from config."""
    if config.TESSERACT_CMD and TESSERACT_AVAILABLE:
        pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_CMD
        return True
    elif TESSERACT_AVAILABLE:
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False
    return False


def _preprocess_image(image: Image.Image) -> Image.Image:
    """Preprocess image for maximum OCR accuracy."""
    # 1. Convert to grayscale
    if image.mode != "L":
        image = image.convert("L")

    # 2. Dynamic Contrast / Lighting correction
    image = ImageOps.autocontrast(image)

    # 3. Resize to optimal DPI (approx 300)
    width, height = image.size
    if width < 1500 or height < 1500:
        scale = max(1800 / width, 1800 / height, 2.0)
        new_size = (int(width * scale), int(height * scale))
        image = image.resize(new_size, Image.Resampling.LANCZOS)

    # 4. Sharpening (Unsharp Mask equivalent)
    image = image.filter(ImageFilter.SHARPEN)
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.8)

    # 5. Denoising
    image = image.filter(ImageFilter.MedianFilter(size=3))

    return image


def _reconstruct_from_boxes(results: list) -> str:
    """ Reconstruct text layout from bounding boxes.
        Sort by top, then group by 'lines' based on y-coordinate.
    """
    if not results:
        return ""

    # Sort results by top y-coordinate
    results.sort(key=lambda x: x[0][0][1])

    lines = []
    if results:
        current_line = [results[0]]
        for i in range(1, len(results)):
            # If the current block's mid-y is within the previous block's height range
            prev_box = results[i-1][0]
            curr_box = results[i][0]
            
            prev_y_center = (prev_box[0][1] + prev_box[2][1]) / 2
            curr_y_center = (curr_box[0][1] + curr_box[2][1]) / 2
            
            # Threshold for 'same line' is approx 1/3 of the box height
            height = prev_box[2][1] - prev_box[0][1]
            if abs(curr_y_center - prev_y_center) < (height * 0.5):
                current_line.append(results[i])
            else:
                lines.append(current_line)
                current_line = [results[i]]
        lines.append(current_line)

    final_text = []
    for line in lines:
        # Sort each line by left x-coordinate
        line.sort(key=lambda x: x[0][0][0])
        line_text = []
        for i, res in enumerate(line):
            # Add relative spacing based on horizontal gap
            if i > 0:
                prev_right = line[i-1][0][1][0]
                curr_left = res[0][0][0]
                gap = curr_left - prev_right
                # If gap is significant, add spaces
                char_width = (res[0][1][0] - res[0][0][0]) / (len(res[1]) or 1)
                num_spaces = int(gap / (char_width * 1.5))
                line_text.append(" " * max(1, num_spaces))
            
            line_text.append(res[1])
        final_text.append(" ".join(line_text))

    return "\n".join(final_text)


def extract_image_gemini(file_path: str) -> ExtractionResult:
    """Extract text from an image using Gemini 1.5 Flash for perfect layout alignment."""
    if not config.GEMINI_API_KEY:
        return ExtractionResult(success=False, error_message="Gemini API Key missing", raw_text="", metadata=DocumentMetadata())

    start_time = time.time()
    try:
        genai.configure(api_key=config.GEMINI_API_KEY)
        model = genai.GenerativeModel(config.GEMINI_MODEL_NAME)
        
        image = Image.open(file_path)
        
        # Prompt for perfect extraction with layout preservation
        prompt = (
            "Perform OCR on this image. Extract EVERY bit of text correctly. "
            "Maintain the original layout, columns, and spacing exactly as they appear. "
            "Do not add any explanations, markdown, or commentary. Output only the extracted text."
        )
        
        response = model.generate_content([prompt, image])
        text = response.text.strip()
        
        if text:
            elapsed = (time.time() - start_time) * 1000
            metadata = DocumentMetadata(
                title=os.path.basename(file_path),
                page_count=1,
                word_count=len(text.split()),
                character_count=len(text),
                file_type="Image (Gemini AI)",
                extra={
                    "image_width": image.width,
                    "image_height": image.height,
                    "ocr_engine": "Gemini 1.5 Flash",
                    "accuracy": "Perfect (Vision-Language Model)"
                }
            )
            return ExtractionResult(
                raw_text=text,
                metadata=metadata,
                success=True,
                extraction_time_ms=elapsed
            )
    except Exception as e:
        print(f"Gemini OCR failed: {e}")
    
    return ExtractionResult(success=False, error_message="Gemini failed", raw_text="", metadata=DocumentMetadata())


def extract_image(file_path: str) -> ExtractionResult:
    """Extract text from an image using the best available OCR engine (Gemini -> EasyOCR -> Tesseract)."""
    start_time = time.time()
    
    # 0. Check for Gemini (Best quality, layout aware)
    if GEMINI_AVAILABLE and config.is_gemini_available():
        result = extract_image_gemini(file_path)
        if result.success:
            return result

    # 1. Check for EasyOCR (Preferred local)
    if EASYOCR_AVAILABLE:
        try:
            reader = get_easyocr_reader()
            if reader:
                # Get original dimensions for metadata
                with Image.open(file_path) as img:
                    original_size = img.size

                # EasyOCR works well with both original and preprocessed images
                # We'll use a slightly preprocessed version for consistency
                # Perform OCR with layout awareness
                # Adjusting thresholds for better numeric and tabular capture
                results = reader.readtext(
                    file_path, 
                    detail=1, 
                    paragraph=False, # We want individual boxes for layout reconstruction
                    width_ths=0.7,   # Better for long numbers/strings
                    height_ths=0.7,
                    contrast_ths=0.3
                )
                
                # Reconstruct full layout from bounding boxes
                text = _reconstruct_from_boxes(results)
                
                if text.strip():
                    elapsed = (time.time() - start_time) * 1000
                    metadata = DocumentMetadata(
                        title=os.path.basename(file_path),
                        page_count=1,
                        word_count=len(text.split()),
                        character_count=len(text),
                        file_type="Image (EasyOCR)",
                        extra={
                            "image_width": original_size[0],
                            "image_height": original_size[1],
                            "ocr_engine": "EasyOCR",
                            "accuracy": "High (Deep Learning)"
                        }
                    )
                    return ExtractionResult(
                        raw_text=text.strip(),
                        metadata=metadata,
                        success=True,
                        extraction_time_ms=elapsed
                    )
        except Exception as e:
            print(f"EasyOCR extraction failed, falling back to Tesseract: {e}")

    # 2. Fallback to Tesseract
    if TESSERACT_AVAILABLE and _configure_tesseract():
        try:
            image = Image.open(file_path)
            original_size = image.size
            processed_image = _preprocess_image(image)
            
            custom_config = f"--oem 3 --psm 6 -l {config.TESSERACT_LANG}"
            text = pytesseract.image_to_string(processed_image, config=custom_config)
            
            # Confidence
            try:
                data = pytesseract.image_to_data(processed_image, config=custom_config, output_type=pytesseract.Output.DICT)
                confidences = [int(c) for c in data["conf"] if int(c) > 0]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            except Exception:
                avg_confidence = 0

            elapsed = (time.time() - start_time) * 1000
            if text.strip():
                metadata = DocumentMetadata(
                    title=os.path.basename(file_path),
                    page_count=1,
                    word_count=len(text.split()),
                    character_count=len(text),
                    file_type="Image (Tesseract)",
                    extra={
                        "image_width": original_size[0],
                        "image_height": original_size[1],
                        "ocr_confidence": round(avg_confidence, 2),
                        "ocr_engine": "Tesseract"
                    }
                )
                return ExtractionResult(
                    raw_text=text.strip(),
                    metadata=metadata,
                    success=True,
                    extraction_time_ms=elapsed
                )
        except Exception as e:
            print(f"Tesseract extraction failed: {e}")

    # 3. Failure cases
    elapsed = (time.time() - start_time) * 1000
    
    if not EASYOCR_AVAILABLE and not TESSERACT_AVAILABLE:
        error_msg = "No OCR libraries installed. Please run 'pip install easyocr'."
    elif not EASYOCR_AVAILABLE and TESSERACT_AVAILABLE:
        error_msg = "EasyOCR is not installed, and Tesseract binary was not found or failed. Please run 'pip install easyocr' for best results."
    elif EASYOCR_AVAILABLE and not TESSERACT_AVAILABLE:
        error_msg = "EasyOCR failed to extract text, and Tesseract is not installed."
    else:
        error_msg = "OCR extraction failed. Both EasyOCR and Tesseract engines were unable to extract text from this image."
    
    return ExtractionResult(
        raw_text="",
        metadata=DocumentMetadata(file_type="Image (OCR)"),
        success=False,
        error_message=error_msg,
        extraction_time_ms=elapsed,
    )
