import re
try:
    import spacy
    _SPACY_AVAILABLE = True
    try:
        _NLP = spacy.load("en_core_web_sm")
    except Exception:
        _NLP = None
except Exception:
    _SPACY_AVAILABLE = False
    _NLP = None

# Common Android error patterns
ERROR_PATTERNS = {
    "NullPointerException": re.compile(r"\bNullPointerException\b"),
    "OutOfMemoryError": re.compile(r"\bOutOfMemoryError\b"),
    "NetworkOnMainThreadException": re.compile(r"\bNetworkOnMainThreadException\b"),
}

def regex_find_errors(text: str):
    found = []
    for name, pattern in ERROR_PATTERNS.items():
        if pattern.search(text):
            found.append(name)
    return found

def extract_entities(text: str):
    if not _SPACY_AVAILABLE or _NLP is None:
        return []
    doc = _NLP(text)
    return [(ent.text, ent.label_) for ent in doc.ents]

def analyze_with_regex_and_spacy(log_text: str) -> str:
    errors = regex_find_errors(log_text)
    entities = extract_entities(log_text)
    parts = []
    if errors:
        parts.append("Detected error types: " + ", ".join(errors))
    else:
        parts.append("No standard error types detected.")
    if entities:
        ents = ", ".join(f"{t} ({l})" for t, l in entities[:50])
        parts.append("Extracted entities: " + ents)
    else:
        parts.append("No entities extracted (spaCy unavailable or no entities found).")
    return "\n".join(parts)
