"""
prompts/__init__.py

Flat re-export surface for the prompts package.

Allows callers to write:
    from prompts import render_rag_prompt
instead of:
    from prompts.templates import render_rag_prompt
"""

from __future__ import annotations

from prompts.templates import (
    render_system_prompt,
    render_qa_prompt,
    render_rag_prompt,
    render_summarization_prompt,
    render_query_rewrite_prompt,
    render_judge_prompt,
    render_decomposition_prompt,
)

from prompts.grading import (
    render_relevance_grading_prompt,
    parse_grading_response,
)

__all__ = [
    "render_system_prompt",
    "render_qa_prompt",
    "render_rag_prompt",
    "render_summarization_prompt",
    "render_query_rewrite_prompt",
    "render_judge_prompt",
    "render_decomposition_prompt",
    "render_relevance_grading_prompt",
    "parse_grading_response",
]
