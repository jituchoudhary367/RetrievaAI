"""
prompts/templates.py

Module-level prompt-rendering functions for every LLM interaction in the
RAG pipeline.

All functions return a fully-rendered string ready to pass to the LLM.
No external templating library is required — standard Python f-strings are
sufficient and avoid adding a dependency.

Functions exported (exact names required by the symbol contract):
  render_system_prompt()
  render_qa_prompt(query, context)
  render_rag_prompt(query, context, citations_required)
  render_summarization_prompt(text)
  render_query_rewrite_prompt(query, history)
  render_judge_prompt(question, answer, context)
  render_decomposition_prompt(query)          ← used by query_decomposer.py
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

def render_system_prompt() -> str:
    """Return the base system prompt for the RAG assistant."""
    return (
        "You are a knowledgeable, precise, and helpful AI assistant. "
        "You answer questions based only on the provided context. "
        "When you use information from the context, you cite the source by "
        "referring to the chunk ID or document title provided. "
        "If the context does not contain enough information to answer the "
        "question accurately, say so clearly rather than speculating. "
        "Be concise and factual. Avoid hallucination."
    )


# ---------------------------------------------------------------------------
# QA prompt (simple, no citation requirement)
# ---------------------------------------------------------------------------

def render_qa_prompt(query: str, context: str) -> str:
    """
    Render a straightforward QA prompt.

    Parameters
    ----------
    query:   The user's question.
    context: Retrieved context passages.
    """
    return (
        f"Context:\n{context}\n\n"
        f"Question: {query}\n\n"
        "Answer the question using only the information provided in the context. "
        "Be concise and accurate."
    )


# ---------------------------------------------------------------------------
# RAG prompt (with optional citation enforcement)
# ---------------------------------------------------------------------------

def render_rag_prompt(
    query: str,
    context: str,
    citations_required: bool = True,
) -> str:
    """
    Render the primary RAG generation prompt.

    When *citations_required* is True, the model is instructed to include
    inline citations in the form [source: <chunk_id>].
    """
    citation_instruction = (
        "For every factual claim, include an inline citation citing the exact document name and page number. "
        "Use the format [Document Name, Page X] based on the context provided below. If you cannot cite a claim, omit it."
        if citations_required
        else "You do not need to cite sources explicitly."
    )

    return (
        f"You are an elite Information Architect and Document Synthesizer. Your core task is to extract, simplify, and beautifully format information from the provided text to answer the user's query.\n\n"
        f"[CRITICAL INSTRUCTIONS]\n"
        f"- ZERO FLUFF: Never start with conversational filler (e.g., \"Sure, here is...\", \"Based on the text...\"). Start directly with the answer.\n"
        f"- HIGH VISUAL DENSITY: Every line must deliver maximum actionable data in the fewest possible words.\n"
        f"- EXTREME SCANNABILITY: The user must be able to absorb the entire answer in under 5 seconds by skimming.\n"
        f"- USE ONLY THE PROVIDED CONTEXT. Do not invent information over.\n"
        f"- {citation_instruction}\n\n"
        f"[VISUAL FORMATTING RULES]\n"
        f"1. 🎯 THE LEAD: The very first sentence must be a bold, high-level direct answer or summary.\n"
        f"2. 🏷️ STRUCTURAL HEADERS: Divide different concepts using distinct Markdown headers (##) accompanied by a single functional emoji.\n"
        f"3. ⚡ THE \"BOLD-FIRST\" LISTS: All lists must use bullet points. The first 2 to 4 words of every single bullet point MUST be in **bold**, followed by a colon (e.g., \"* **Secure Access**: Description goes here.\").\n"
        f"4. ✂️ SHORT SENTENCES: Keep sentences punchy and strictly under 15 words. Break long sentences into multiple bullet points.\n\n"
        f"[EXECUTION TEMPLATE STRUCTURE]\n"
        f"## 🎯 [Core Summary Title]\n"
        f"[Provide a crisp 1-2 sentence executive overview here]\n\n"
        f"## 🛠️ [Primary Dimension / Key Elements]\n"
        f"* **[First Key Concept]**: [High-impact, concise explanatory phrase]\n"
        f"* **[Second Key Concept]**: [High-impact, concise explanatory phrase]\n\n"
        f"## 📋 [Action Items / Technical Requirements]\n"
        f"* **[Action Focus]**: [Clear, short detail starting with a strong verb]\n"
        f"* **[System Constraint]**: [Clear, short detail starting with a strong verb]\n\n"
        f"=== CONTEXT START ===\n{context}\n=== CONTEXT END ===\n\n"
        f"Question: {query}\n\n"
        "Answer:"
    )


# ---------------------------------------------------------------------------
# Summarization prompt
# ---------------------------------------------------------------------------

def render_summarization_prompt(text: str) -> str:
    """
    Render a prompt that asks the model to produce a concise summary of *text*.
    Used by the conversation summarization path in ``services/conversation.py``.
    """
    return (
        "Please produce a concise summary of the following conversation or "
        "document. Preserve key facts, decisions, and action items. "
        "Output only the summary — no preamble.\n\n"
        f"=== TEXT ===\n{text}\n=== END TEXT ===\n\n"
        "Summary:"
    )


# ---------------------------------------------------------------------------
# Query rewrite prompt
# ---------------------------------------------------------------------------

def render_query_rewrite_prompt(query: str, history: str) -> str:
    """
    Render a prompt that asks the model to rewrite *query* in the context of
    the conversation *history* so that it is self-contained.
    """
    return (
        "Given the conversation history below and a follow-up question, "
        "rewrite the follow-up question so it is fully self-contained and "
        "can be understood without the conversation history. "
        "Output ONLY the rewritten question — nothing else.\n\n"
        f"Conversation history:\n{history}\n\n"
        f"Follow-up question: {query}\n\n"
        "Rewritten question:"
    )


# ---------------------------------------------------------------------------
# Judge / evaluation prompt
# ---------------------------------------------------------------------------

def render_judge_prompt(question: str, answer: str, context: str) -> str:
    """
    Render an LLM-as-judge prompt to evaluate whether *answer* is grounded
    in *context* and correctly addresses *question*.

    Expected model output: a structured assessment (PASS/FAIL + brief reason).
    """
    return (
        "You are an impartial judge evaluating the quality of an AI-generated "
        "answer against the provided reference context.\n\n"
        f"Question:\n{question}\n\n"
        f"Reference context:\n{context}\n\n"
        f"Answer to evaluate:\n{answer}\n\n"
        "Evaluate the answer on two criteria:\n"
        "1. GROUNDEDNESS — Is every claim in the answer supported by the context?\n"
        "2. CORRECTNESS — Does the answer correctly address the question?\n\n"
        "Respond in this exact format:\n"
        "GROUNDEDNESS: PASS|FAIL\n"
        "CORRECTNESS: PASS|FAIL\n"
        "REASON: <one sentence>\n"
        "OVERALL: PASS|FAIL"
    )


# ---------------------------------------------------------------------------
# Query decomposition prompt
# ---------------------------------------------------------------------------

def render_decomposition_prompt(query: str) -> str:
    """
    Render a prompt that asks the model to decompose a compound *query* into
    a list of simpler, independent sub-queries.

    Expected model output: a numbered list of sub-queries (one per line).
    If the query is already simple, the model should output the original query
    as the sole item.
    """
    return (
        "You are a query decomposition assistant. Analyse the following "
        "question and, if it is compound (contains multiple distinct "
        "information needs), decompose it into a numbered list of simpler, "
        "self-contained sub-queries. If the question is already simple, "
        "output it unchanged as item 1.\n\n"
        "Rules:\n"
        "- Output ONLY the numbered list — no preamble or explanation.\n"
        "- Each sub-query must be a complete, standalone question.\n"
        "- Maximum 5 sub-queries.\n\n"
        f"Question: {query}\n\n"
        "Sub-queries:"
    )


__all__ = [
    "render_system_prompt",
    "render_qa_prompt",
    "render_rag_prompt",
    "render_summarization_prompt",
    "render_query_rewrite_prompt",
    "render_judge_prompt",
    "render_decomposition_prompt",
]
