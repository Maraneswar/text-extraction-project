"""
Extractive text summarization using sumy library.
Uses LexRank algorithm by default for graph-based sentence ranking.
"""
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lex_rank import LexRankSummarizer
from sumy.summarizers.lsa import LsaSummarizer
from sumy.summarizers.luhn import LuhnSummarizer
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words
from models.schemas import SummaryResult
from config import SUMMARY_SENTENCE_COUNT, SUMMARY_ALGORITHM
import config
import time

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

LANGUAGE = "english"


def summarize_with_gemini(text: str) -> SummaryResult:
    """Generate high-quality summary and key highlights using Gemini AI."""
    if not config.is_gemini_available():
        return None

    start_time = time.time()
    try:
        genai.configure(api_key=config.GEMINI_API_KEY)
        model = genai.GenerativeModel(config.GEMINI_MODEL_NAME)
        
        prompt = (
            "You are an expert document analyst. Read the following text and create a highly synthesized, unique abstractive summary.\n"
            "CRITICAL INSTRUCTIONS:\n"
            "1. Do NOT just copy/paste or extract sentences verbatim from the text. Synthesize the meaning into your own words.\n"
            "2. Provide a unique, high-level overview of the entire document's core message or purpose.\n"
            "3. Structure the summary with thematic topics (e.g., **Key Themes**, **Major Findings**, **Core Assertions**, or document-specific domains like **Experience** for resumes).\n"
            "4. For each topic, provide concise insights, not just a list of extracted facts.\n"
            "5. Synthesize 3 to 7 truly unique, critical 'key points' that represent the ultimate takeaways of the document for the key_points array.\n"
            "Respond strictly in JSON format:\n"
            '{"summary": "**Topic 1**\\n- Insightful summary point 1...\\n\\n**Topic 2**\\n- Insightful summary point 2...", "key_points": ["**CORE TAKEAWAY**: synthesized point", ...]}'
        )
        
        response = model.generate_content(f"{prompt}\n\nText: {text}", generation_config={"response_mime_type": "application/json"})
        import json
        data = json.loads(response.text)
        
        summary = data.get("summary", "")
        key_points = data.get("key_points", [])
        
        if summary:
            elapsed = (time.time() - start_time) * 1000
            compression_ratio = len(summary) / len(text) if len(text) > 0 else 1.0
            
            return SummaryResult(
                summary=summary,
                key_points=key_points,
                original_length=len(text),
                summary_length=len(summary),
                compression_ratio=round(compression_ratio, 4),
                sentence_count=len(key_points), # Using key_points count as surrogate
                algorithm="Gemini AI (Abstractive)"
            )
    except Exception as e:
        print(f"Gemini summarization failed: {e}")
    
    return None


def _get_summarizer(algorithm: str):
    """Get the appropriate summarizer based on algorithm name."""
    stemmer = Stemmer(LANGUAGE)

    if algorithm == "lsa":
        summarizer = LsaSummarizer(stemmer)
    elif algorithm == "luhn":
        summarizer = LuhnSummarizer(stemmer)
    else:  # default to lex-rank
        summarizer = LexRankSummarizer(stemmer)

    summarizer.stop_words = get_stop_words(LANGUAGE)
    return summarizer


def summarize_text(text: str, sentence_count: int = None, algorithm: str = None) -> SummaryResult:
    """
    Generate an extractive or abstractive summary of the given text.
    Prioritizes Gemini if available.
    """
    if sentence_count is None:
        sentence_count = SUMMARY_SENTENCE_COUNT
    if algorithm is None:
        algorithm = SUMMARY_ALGORITHM

    # 0. Try Gemini (Superior abstractive quality)
    if GEMINI_AVAILABLE and config.is_gemini_available():
        gemini_result = summarize_with_gemini(text)
        if gemini_result:
            return gemini_result

    # Handle short texts
    sentences_in_text = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]
    if len(sentences_in_text) <= sentence_count:
        # Text is already short enough
        clean_text = " ".join(text.split())
        return SummaryResult(
            summary=clean_text,
            original_length=len(text),
            summary_length=len(clean_text),
            compression_ratio=1.0,
            sentence_count=len(sentences_in_text),
            algorithm=algorithm,
        )

    try:
        # Parse the text
        parser = PlaintextParser.from_string(text, Tokenizer(LANGUAGE))
        summarizer = _get_summarizer(algorithm)

        # Generate summary
        summary_sentences = summarizer(parser.document, sentence_count)
        summary = " ".join(str(sentence) for sentence in summary_sentences)

        if not summary.strip():
            # Fallback: return first N sentences
            summary = ". ".join(sentences_in_text[:sentence_count]) + "."

        compression_ratio = len(summary) / len(text) if len(text) > 0 else 1.0

        return SummaryResult(
            summary=summary,
            original_length=len(text),
            summary_length=len(summary),
            compression_ratio=round(compression_ratio, 4),
            sentence_count=sentence_count,
            algorithm=algorithm,
        )

    except Exception as e:
        # Fallback: return first few sentences
        fallback = ". ".join(sentences_in_text[:sentence_count]) + "."
        return SummaryResult(
            summary=fallback,
            original_length=len(text),
            summary_length=len(fallback),
            compression_ratio=round(len(fallback) / len(text), 4) if len(text) > 0 else 1.0,
            sentence_count=sentence_count,
            algorithm=f"{algorithm} (fallback)",
        )
