from typing import List, Dict
from bs4 import BeautifulSoup
import re


def clean_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator=" ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def summarize_items(items: List[Dict], max_sentences: int = 2) -> List[Dict]:
    summarized = []
    for item in items:
        text = clean_text(item.get("summary", ""))
        # naive sentence split
        sentences = re.split(r"(?<=[.!?])\s+", text)
        short = " ".join(sentences[:max_sentences]).strip()
        summarized.append({**item, "summary": short})
    return summarized