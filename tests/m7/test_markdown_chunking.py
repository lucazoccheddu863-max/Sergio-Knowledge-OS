"""Tests for retrieval-friendly Markdown section chunking."""
from __future__ import annotations

from skos.m7.runtime.markdown_chunking import MarkdownSectionChunking


def test_headings_remain_attached_to_section_content() -> None:
    chunks = MarkdownSectionChunking().chunk(
        "# Title\n\nIntro text.\n\n## Milestones\n\n- M7.1 done\n- M7.2 done"
    )

    assert len(chunks) == 2
    assert chunks[0].text == "# Title\n\nIntro text."
    assert chunks[1].text == "## Milestones\n\n- M7.1 done\n- M7.2 done"


def test_plain_markdown_without_headings_keeps_paragraph_behavior() -> None:
    chunks = MarkdownSectionChunking().chunk("First paragraph.\n\nSecond paragraph.")

    assert [chunk.text for chunk in chunks] == ["First paragraph.", "Second paragraph."]
