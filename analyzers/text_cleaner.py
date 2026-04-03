"""
Intelligent text cleaner using Gemini to format raw OCR and PDF extractions perfectly.
"""
import time
import config

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


def clean_format_text(raw_text: str) -> str:
    """Pass raw extracted text through Gemini to clean formatting and add markdown structure without missing words."""
    if not config.is_gemini_available() or not GEMINI_AVAILABLE:
        return raw_text
        
    # Skip if text is extremely short
    if len(raw_text.strip()) < 50:
        return raw_text

    try:
        genai.configure(api_key=config.GEMINI_API_KEY)
        model = genai.GenerativeModel(config.GEMINI_MODEL_NAME)
        
        prompt = (
            "You are a master document formatting assistant. Your task is to clean up and perfectly format the raw extracted text below into a structured and topic-wise format.\n\n"
            "CRITICAL INSTRUCTIONS:\n"
            "1. You MUST preserve EVERY SINGLE WORD and detail from the original text. Do not summarize, skip, or rephrase anything. No information loss is acceptable.\n"
            "2. Organize all content logically into structured, thematic topics (topic-wise). Apply bold markdown headers (e.g. **Contact Information**, **Experience**, **Summary**, or other relevant topics) and use proper bullet points.\n"
            "3. Fix arbitrary broken line-breaks (typical OCR artifacts) and stitch sentences back together naturally.\n"
            "4. Return ONLY the perfectly formatted text. Do not include any JSON wrapping or conversational preamble.\n\n"
            "RAW TEXT:\n"
        )
        
        # We don't use JSON response here, we just want plain formatted text
        response = model.generate_content(prompt + raw_text)
        
        if response.text and len(response.text.strip()) > 0:
            return response.text.strip()
            
    except Exception as e:
        print(f"Intelligent formatting failed, falling back to raw: {e}")
        
    return raw_text
