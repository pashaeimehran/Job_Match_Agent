import pytest

from src.extraction.cleaning import clean_job_text


def test_clean_job_text_strips_html_and_normalizes_whitespace() -> None:
    raw = "<h1>AI Engineer</h1><p>Python&nbsp;  and   RAG</p><p>Apply now</p>"

    cleaned = clean_job_text(raw)

    assert "<h1>" not in cleaned
    assert "AI Engineer" in cleaned
    assert "Python and RAG" in cleaned
    assert "Apply now" not in cleaned


def test_clean_job_text_rejects_non_string() -> None:
    with pytest.raises(TypeError):
        clean_job_text(123)  # type: ignore[arg-type]
