"""
Named Entity Recognition using spaCy.
Extracts persons, organizations, dates, monetary amounts, locations, and more.
Also uses regex patterns for additional entity types.
"""
import re
from collections import Counter
from typing import List, Dict
from models.schemas import Entity, EntityResult
from config import SPACY_MODEL, NER_ENTITY_TYPES

# Try to load spaCy model
try:
    import spacy
    nlp = spacy.load(SPACY_MODEL)
    SPACY_AVAILABLE = True
except (ImportError, OSError):
    SPACY_AVAILABLE = False
    nlp = None

# Entity label descriptions
LABEL_DESCRIPTIONS = {
    "PERSON": "Person name",
    "ORG": "Organization",
    "GPE": "Country / City / State",
    "DATE": "Date or period",
    "MONEY": "Monetary value",
    "TIME": "Time expression",
    "PERCENT": "Percentage",
    "EVENT": "Named event",
    "PRODUCT": "Product name",
    "LAW": "Law or regulation",
    "NORP": "Nationality / Group",
    "FAC": "Facility / Building",
    "LOC": "Non-GPE location",
    "WORK_OF_ART": "Title of work",
    "LANGUAGE": "Language name",
    "CARDINAL": "Number",
    "ORDINAL": "Ordinal number",
    "QUANTITY": "Measurement",
    "EMAIL": "Email address",
    "PHONE": "Phone number",
    "URL": "Web URL",
}

# Regex patterns for additional entity types
REGEX_PATTERNS = {
    "EMAIL": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "PHONE": r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}',
    "URL": r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w\-._~:/?#\[\]@!$&\'()*+,;=%]*',
}


def _extract_regex_entities(text: str) -> List[Entity]:
    """Extract entities using regex patterns."""
    entities = []
    for label, pattern in REGEX_PATTERNS.items():
        matches = re.findall(pattern, text)
        if matches:
            counted = Counter(matches)
            for match_text, count in counted.most_common():
                entities.append(Entity(
                    text=match_text,
                    label=label,
                    label_description=LABEL_DESCRIPTIONS.get(label, label),
                    count=count,
                ))
    return entities


def _extract_spacy_entities(text: str) -> List[Entity]:
    """Extract entities using spaCy NER."""
    if not SPACY_AVAILABLE or nlp is None:
        return []

    # Process text (handle long texts by chunking)
    max_length = 100000
    if len(text) > max_length:
        text = text[:max_length]

    doc = nlp(text)

    # Collect and deduplicate entities
    entity_map: Dict[str, Dict] = {}

    for ent in doc.ents:
        if ent.label_ not in NER_ENTITY_TYPES:
            continue

        clean_text = ent.text.strip()
        if not clean_text or len(clean_text) < 2:
            continue

        key = f"{ent.label_}:{clean_text.lower()}"
        if key in entity_map:
            entity_map[key]["count"] += 1
            entity_map[key]["positions"].append(ent.start_char)
        else:
            entity_map[key] = {
                "text": clean_text,
                "label": ent.label_,
                "label_description": LABEL_DESCRIPTIONS.get(ent.label_, ent.label_),
                "count": 1,
                "positions": [ent.start_char],
            }

    # Convert to Entity objects and sort by count
    entities = [
        Entity(**data)
        for data in sorted(entity_map.values(), key=lambda x: x["count"], reverse=True)
    ]

    return entities


def extract_entities(text: str) -> EntityResult:
    """
    Extract named entities from text using spaCy and regex patterns.

    Args:
        text: The input text to analyze.

    Returns:
        EntityResult with all found entities and statistics.
    """
    if not text.strip():
        return EntityResult(entities=[], entity_counts={}, total_entities=0)

    # Get entities from both sources
    spacy_entities = _extract_spacy_entities(text)
    regex_entities = _extract_regex_entities(text)

    # Combine (spaCy entities first, then regex)
    all_entities = spacy_entities + regex_entities

    # Count by category
    entity_counts: Dict[str, int] = {}
    for ent in all_entities:
        entity_counts[ent.label] = entity_counts.get(ent.label, 0) + ent.count

    return EntityResult(
        entities=all_entities,
        entity_counts=entity_counts,
        total_entities=sum(ent.count for ent in all_entities),
    )
