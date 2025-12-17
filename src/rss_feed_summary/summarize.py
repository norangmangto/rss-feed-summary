from typing import List, Dict
from bs4 import BeautifulSoup
import re
from collections import Counter


def clean_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator=" ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_sentences(text: str) -> List[str]:
    """Split text into sentences."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if len(s.strip()) > 20]


def score_sentences(sentences: List[str]) -> List[tuple]:
    """Score sentences based on word frequency (simple extractive summarization)."""
    # Tokenize and count word frequency
    words = []
    for sent in sentences:
        words.extend(re.findall(r"\b\w{4,}\b", sent.lower()))
    
    word_freq = Counter(words)
    
    # Score each sentence
    scored = []
    for i, sent in enumerate(sentences):
        sent_words = re.findall(r"\b\w{4,}\b", sent.lower())
        score = sum(word_freq.get(w, 0) for w in sent_words) / (len(sent_words) or 1)
        scored.append((score, i, sent))
    
    return sorted(scored, key=lambda x: (-x[0], x[1]))


def summarize_items(items: List[Dict], max_sentences: int = 3) -> List[Dict]:
    summarized = []
    for item in items:
        # Use full content if available, otherwise summary
        content = item.get("content", "") or item.get("summary", "")
        text = clean_text(content)
        
        if not text:
            summarized.append({**item, "summary": ""})
            continue
        
        sentences = extract_sentences(text)
        
        if len(sentences) <= max_sentences:
            short = " ".join(sentences)
        else:
            # Score and select top sentences
            scored = score_sentences(sentences)
            top_sentences = sorted(scored[:max_sentences], key=lambda x: x[1])
            short = " ".join(s[2] for s in top_sentences)
        
        summarized.append({**item, "summary": short})
    return summarized