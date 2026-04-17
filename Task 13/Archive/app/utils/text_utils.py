import re
from collections import Counter

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "he",
    "in", "is", "it", "its", "of", "on", "that", "the", "to", "was", "were", "will",
    "with", "this", "these", "those", "or", "if", "not", "can", "could", "should",
    "would", "may", "might", "do", "does", "did", "you", "your", "we", "our", "they",
    "their", "about", "into", "than", "then", "them", "such", "also", "using", "used",
}


def normalize_text(text):
    text = text.replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def split_sentences(text):
    cleaned = normalize_text(text)
    if not cleaned:
        return []
    parts = re.split(r"(?<=[.!?])\s+", cleaned)
    return [part.strip() for part in parts if len(part.strip()) > 25]


def extract_keywords(text, limit=12):
    words = re.findall(r"[A-Za-z][A-Za-z0-9\-]{2,}", text.lower())
    filtered = [w for w in words if w not in STOPWORDS]
    ranked = Counter(filtered).most_common(limit * 2)

    keywords = []
    for word, _ in ranked:
        if word not in keywords:
            keywords.append(word)
        if len(keywords) >= limit:
            break
    return keywords


def keyword_overlap_score(text, query):
    text_words = set(re.findall(r"[A-Za-z][A-Za-z0-9\-]{2,}", text.lower()))
    query_words = set(re.findall(r"[A-Za-z][A-Za-z0-9\-]{2,}", query.lower()))

    if not text_words or not query_words:
        return 0.0

    query_words = {w for w in query_words if w not in STOPWORDS}
    if not query_words:
        return 0.0

    overlap = len(text_words.intersection(query_words))
    return overlap / max(1, len(query_words))
