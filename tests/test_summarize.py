import pytest
from rss_feed_summary.summarize import clean_text, extract_sentences, score_sentences, summarize_items


def test_clean_text_strips_html():
    assert clean_text("<p>Hello <b>world</b></p>") == "Hello world"


def test_clean_text_collapses_whitespace():
    assert clean_text("<p>foo   bar</p>") == "foo bar"


def test_clean_text_empty():
    assert clean_text("") == ""


def test_extract_sentences_splits_on_punctuation():
    text = "This is one sentence. This is another sentence! And a third one here."
    sentences = extract_sentences(text)
    assert len(sentences) == 3


def test_extract_sentences_filters_short():
    text = "Ok. This sentence is long enough to pass the filter threshold."
    sentences = extract_sentences(text)
    assert all(len(s) > 20 for s in sentences)
    assert not any(s == "Ok." for s in sentences)


def test_score_sentences_returns_all():
    sentences = ["The quick brown fox jumps.", "Lazy dogs sleep all day.", "Foxes are quick animals."]
    scored = score_sentences(sentences)
    assert len(scored) == 3


def test_score_sentences_higher_freq_ranks_first():
    # "python" appears in all three; the sentence with most high-freq words should score highest
    sentences = [
        "Python is a great python programming language for python developers.",
        "Java is also a programming language.",
        "Ruby exists.",
    ]
    scored = score_sentences(sentences)
    # First result should be the python-heavy sentence
    assert "Python" in scored[0][2] or "python" in scored[0][2]


def test_summarize_items_truncates_to_max_sentences():
    item = {
        "content": (
            "First sentence is here and long enough. "
            "Second sentence is here and long enough. "
            "Third sentence is here and long enough. "
            "Fourth sentence is here and long enough."
        ),
        "summary": "",
    }
    result = summarize_items([item], max_sentences=2)
    summary = result[0]["summary"]
    # Should contain at most 2 sentences (split on ". ")
    parts = [s for s in summary.split(". ") if s]
    assert len(parts) <= 2


def test_summarize_items_empty_content_returns_empty_summary():
    item = {"content": "", "summary": ""}
    result = summarize_items([item])
    assert result[0]["summary"] == ""


def test_summarize_items_short_content_kept_whole():
    item = {
        "content": "Only one sentence here that is long enough.",
        "summary": "",
    }
    result = summarize_items([item], max_sentences=3)
    assert result[0]["summary"] == "Only one sentence here that is long enough."


def test_summarize_items_falls_back_to_summary_field():
    item = {
        "content": "",
        "summary": "<p>Fallback content that is long enough to be a sentence.</p>",
    }
    result = summarize_items([item])
    assert "Fallback content" in result[0]["summary"]


def test_summarize_items_preserves_other_fields():
    item = {"title": "Test", "link": "https://example.com", "content": "", "summary": ""}
    result = summarize_items([item])
    assert result[0]["title"] == "Test"
    assert result[0]["link"] == "https://example.com"
