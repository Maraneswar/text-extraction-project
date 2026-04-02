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

LANGUAGE = "english"


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
    Generate an extractive summary of the given text.

    Args:
        text: The input text to summarize.
        sentence_count: Number of sentences in the summary (default from config).
        algorithm: Summarization algorithm to use (default from config).

    Returns:
        SummaryResult with the summary and statistics.
    """
    if sentence_count is None:
        sentence_count = SUMMARY_SENTENCE_COUNT
    if algorithm is None:
        algorithm = SUMMARY_ALGORITHM

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
