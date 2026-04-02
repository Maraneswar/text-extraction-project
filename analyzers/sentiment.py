"""
Sentiment analysis using NLTK's VADER (Valence Aware Dictionary and sEntiment Reasoner).
Provides both overall and sentence-level sentiment analysis.
"""
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.tokenize import sent_tokenize
from models.schemas import SentimentResult, SentimentBreakdown
from config import SENTIMENT_THRESHOLDS
from typing import List

# Download required NLTK data
try:
    nltk.data.find("sentiment/vader_lexicon.zip")
except LookupError:
    nltk.download("vader_lexicon", quiet=True)

try:
    nltk.data.find("tokenizers/punkt_tab")
except LookupError:
    nltk.download("punkt_tab", quiet=True)

# Initialize analyzer
sia = SentimentIntensityAnalyzer()


def _get_sentiment_label(compound: float) -> str:
    """Convert compound score to human-readable label."""
    if compound >= 0.5:
        return "Very Positive"
    elif compound >= SENTIMENT_THRESHOLDS["positive"]:
        return "Positive"
    elif compound <= -0.5:
        return "Very Negative"
    elif compound <= SENTIMENT_THRESHOLDS["negative"]:
        return "Negative"
    else:
        return "Neutral"


def analyze_sentiment(text: str) -> SentimentResult:
    """
    Perform sentiment analysis on the given text.

    Returns overall sentiment scores and sentence-level breakdown.

    Args:
        text: The input text to analyze.

    Returns:
        SentimentResult with overall and per-sentence sentiment analysis.
    """
    if not text.strip():
        return SentimentResult(
            overall_compound=0.0,
            overall_positive=0.0,
            overall_negative=0.0,
            overall_neutral=1.0,
            overall_label="Neutral",
            sentence_breakdown=[],
            confidence=0.0,
        )

    # Overall sentiment
    overall_scores = sia.polarity_scores(text)

    # Sentence-level breakdown
    sentences = sent_tokenize(text)
    sentence_breakdown: List[SentimentBreakdown] = []

    # Limit to first 50 sentences for performance
    for sent in sentences[:50]:
        sent = sent.strip()
        if not sent or len(sent) < 5:
            continue

        scores = sia.polarity_scores(sent)
        sentence_breakdown.append(SentimentBreakdown(
            text=sent[:200],  # Truncate very long sentences
            compound=round(scores["compound"], 4),
            positive=round(scores["pos"], 4),
            negative=round(scores["neg"], 4),
            neutral=round(scores["neu"], 4),
            label=_get_sentiment_label(scores["compound"]),
        ))

    # Calculate confidence based on consistency of sentence sentiments
    if sentence_breakdown:
        compounds = [sb.compound for sb in sentence_breakdown]
        avg_magnitude = sum(abs(c) for c in compounds) / len(compounds)
        confidence = min(avg_magnitude * 2, 1.0)  # Scale to 0-1
    else:
        confidence = abs(overall_scores["compound"])

    return SentimentResult(
        overall_compound=round(overall_scores["compound"], 4),
        overall_positive=round(overall_scores["pos"], 4),
        overall_negative=round(overall_scores["neg"], 4),
        overall_neutral=round(overall_scores["neu"], 4),
        overall_label=_get_sentiment_label(overall_scores["compound"]),
        sentence_breakdown=sentence_breakdown,
        confidence=round(confidence, 4),
    )
