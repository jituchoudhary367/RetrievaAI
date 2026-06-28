"""
pipeline/chunker.py

Splits pre-processed document text into overlapping ``Chunk`` objects ready
for embedding and indexing.

Four strategies, all subclassing ``BaseChunker``:
  RecursiveChunker  — split on progressively finer separators
  MarkdownChunker   — split on Markdown headings then fall back to recursive
  ASTChunker        — split Python source on top-level function/class nodes
  SemanticChunker   — group sentences by embedding similarity (requires
                      sentence-transformers; graceful no-op fallback)

``Chunker`` is the public facade: it selects the concrete implementation
based on ``ChunkingSettings.strategy`` or the caller-supplied ``source_type``.
"""

from __future__ import annotations

import ast
import logging
import re
from abc import ABC, abstractmethod
from typing import List, Optional, Sequence

from app.config import ChunkingStrategy, get_settings
from app.models import Chunk

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Token-counting helpers
# ---------------------------------------------------------------------------

def _approx_token_count(text: str) -> int:
    """Approximate token count: ~4 chars per token (GPT-style)."""
    return max(1, len(text) // 4)


def _exact_token_count(text: str, model: str = "cl100k_base") -> int:
    """Exact token count via tiktoken.  Falls back to approximate."""
    try:
        import tiktoken  # noqa: PLC0415
        enc = tiktoken.get_encoding(model)
        return len(enc.encode(text))
    except ImportError:
        return _approx_token_count(text)
    except Exception:  # noqa: BLE001
        return _approx_token_count(text)


# ---------------------------------------------------------------------------
# Base chunker
# ---------------------------------------------------------------------------

class BaseChunker(ABC):
    """Abstract base for all chunking strategies."""

    def __init__(
        self,
        chunk_size: int,
        chunk_overlap: int,
        min_chunk_size: int,
        use_exact_tokens: bool = False,
    ) -> None:
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        self.use_exact_tokens = use_exact_tokens

    @abstractmethod
    def split(self, text: str) -> List[str]:
        """Split *text* into a list of raw string chunks."""
        ...

    def _count_tokens(self, text: str) -> int:
        return (
            _exact_token_count(text)
            if self.use_exact_tokens
            else _approx_token_count(text)
        )

    # Utility: create chunks with overlap from a flat list of segments
    def _merge_with_overlap(self, segments: List[str]) -> List[str]:
        """
        Given a list of text segments, merge them into chunks of up to
        ``chunk_size`` tokens, then slide the window by
        ``chunk_size - chunk_overlap`` tokens.
        """
        chunks: List[str] = []
        current_parts: List[str] = []
        current_size = 0

        for seg in segments:
            seg_size = self._count_tokens(seg)
            if current_size + seg_size > self.chunk_size and current_parts:
                chunks.append(" ".join(current_parts))
                # Keep overlap: drop segments from the front until we are
                # within the overlap budget
                while current_parts and current_size > self.chunk_overlap:
                    dropped = current_parts.pop(0)
                    current_size -= self._count_tokens(dropped)
            current_parts.append(seg)
            current_size += seg_size

        if current_parts:
            chunks.append(" ".join(current_parts))

        return chunks


# ---------------------------------------------------------------------------
# Recursive chunker
# ---------------------------------------------------------------------------

class RecursiveChunker(BaseChunker):
    """
    Splits on progressively finer separators until chunks fit in
    ``chunk_size`` tokens.

    Separator order: paragraph → sentence → word.
    """

    _SEPARATORS: Sequence[str] = ["\n\n", "\n", ". ", " ", ""]

    def split(self, text: str) -> List[str]:
        return self._recursive_split(text, list(self._SEPARATORS))

    def _recursive_split(self, text: str, separators: List[str]) -> List[str]:
        if self._count_tokens(text) <= self.chunk_size:
            return [text] if text.strip() else []

        sep = separators[0] if separators else ""
        remaining_seps = separators[1:]

        if sep == "":
            # Hard character split as last resort
            step = self.chunk_size * 4  # approximate bytes
            stride = step - self.chunk_overlap * 4
            parts = [text[i : i + step] for i in range(0, len(text), max(1, stride))]
            return [p for p in parts if p.strip()]

        parts = text.split(sep)
        # Recurse if any part still exceeds chunk_size
        result: List[str] = []
        for part in parts:
            if self._count_tokens(part) > self.chunk_size and remaining_seps:
                result.extend(self._recursive_split(part, remaining_seps))
            elif part.strip():
                result.append(part)

        return self._merge_with_overlap(result)


# ---------------------------------------------------------------------------
# Markdown chunker
# ---------------------------------------------------------------------------

class MarkdownChunker(BaseChunker):
    """
    Splits on ATX Markdown headings (#, ##, …), then applies recursive
    splitting within sections that are still too large.
    """

    _HEADING_RE = re.compile(r"^(#{1,6})\s+.+", re.MULTILINE)

    def split(self, text: str) -> List[str]:
        positions = [m.start() for m in self._HEADING_RE.finditer(text)]
        if not positions:
            return RecursiveChunker(
                self.chunk_size, self.chunk_overlap,
                self.min_chunk_size, self.use_exact_tokens
            ).split(text)

        sections: List[str] = []
        for i, pos in enumerate(positions):
            end = positions[i + 1] if i + 1 < len(positions) else len(text)
            sections.append(text[pos:end])

        # Prepend any content before the first heading
        if positions[0] > 0:
            sections.insert(0, text[: positions[0]])

        result: List[str] = []
        recursive = RecursiveChunker(
            self.chunk_size, self.chunk_overlap,
            self.min_chunk_size, self.use_exact_tokens
        )
        for section in sections:
            if self._count_tokens(section) > self.chunk_size:
                result.extend(recursive.split(section))
            elif section.strip():
                result.append(section)

        return result


# ---------------------------------------------------------------------------
# AST chunker
# ---------------------------------------------------------------------------

class ASTChunker(BaseChunker):
    """
    Splits Python source code on top-level ``FunctionDef``, ``AsyncFunctionDef``,
    and ``ClassDef`` nodes.  Falls back to ``RecursiveChunker`` for non-Python
    text or parse failures.
    """

    def split(self, text: str) -> List[str]:
        try:
            tree = ast.parse(text)
        except SyntaxError:
            logger.debug("AST parse failed; falling back to RecursiveChunker.")
            return RecursiveChunker(
                self.chunk_size, self.chunk_overlap,
                self.min_chunk_size, self.use_exact_tokens
            ).split(text)

        lines = text.splitlines(keepends=True)
        top_level = [
            node for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            and not any(
                isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                for parent in ast.walk(tree)
                if node in ast.walk(parent) and parent is not node
            )
        ]

        if not top_level:
            return RecursiveChunker(
                self.chunk_size, self.chunk_overlap,
                self.min_chunk_size, self.use_exact_tokens
            ).split(text)

        # Sort by line number
        top_level.sort(key=lambda n: n.lineno)

        segments: List[str] = []
        prev_end = 1
        for node in top_level:
            # Any code between this node and the previous top-level node
            if node.lineno > prev_end:
                between = "".join(lines[prev_end - 1 : node.lineno - 1]).strip()
                if between:
                    segments.append(between)
            end_lineno = getattr(node, "end_lineno", node.lineno)
            node_text = "".join(lines[node.lineno - 1 : end_lineno]).strip()
            if node_text:
                segments.append(node_text)
            prev_end = end_lineno + 1

        # Trailing module-level code
        if prev_end <= len(lines):
            trailing = "".join(lines[prev_end - 1 :]).strip()
            if trailing:
                segments.append(trailing)

        # Merge large segments recursively
        recursive = RecursiveChunker(
            self.chunk_size, self.chunk_overlap,
            self.min_chunk_size, self.use_exact_tokens
        )
        result: List[str] = []
        for seg in segments:
            if self._count_tokens(seg) > self.chunk_size:
                result.extend(recursive.split(seg))
            elif seg.strip():
                result.append(seg)

        return result


# ---------------------------------------------------------------------------
# Semantic chunker
# ---------------------------------------------------------------------------

class SemanticChunker(BaseChunker):
    """
    Groups sentences into chunks based on embedding cosine similarity.

    Requires ``sentence-transformers``.  If the library is unavailable, falls
    back to ``RecursiveChunker`` with a logged warning.
    """

    def __init__(
        self,
        chunk_size: int,
        chunk_overlap: int,
        min_chunk_size: int,
        similarity_threshold: float = 0.5,
        model_name: str = "all-MiniLM-L6-v2",
        use_exact_tokens: bool = False,
    ) -> None:
        super().__init__(chunk_size, chunk_overlap, min_chunk_size, use_exact_tokens)
        self.similarity_threshold = similarity_threshold
        self.model_name = model_name

    def split(self, text: str) -> List[str]:
        try:
            from sentence_transformers import SentenceTransformer  # noqa: PLC0415
        except ImportError:
            logger.warning(
                "sentence-transformers not installed — SemanticChunker falling back "
                "to RecursiveChunker. Install with: pip install sentence-transformers"
            )
            return RecursiveChunker(
                self.chunk_size, self.chunk_overlap,
                self.min_chunk_size, self.use_exact_tokens
            ).split(text)

        sentences = self._split_sentences(text)
        if len(sentences) <= 1:
            return [text] if text.strip() else []

        model = SentenceTransformer(self.model_name)
        embeddings = model.encode(sentences, convert_to_numpy=True)

        chunks: List[str] = []
        current: List[str] = [sentences[0]]

        for i in range(1, len(sentences)):
            sim = self._cosine_similarity(embeddings[i - 1], embeddings[i])
            current_text = " ".join(current)
            if (
                sim < self.similarity_threshold
                or self._count_tokens(current_text) >= self.chunk_size
            ):
                chunks.append(current_text)
                # Overlap: keep last sentence
                current = current[-max(1, self.chunk_overlap // 50):]
            current.append(sentences[i])

        if current:
            chunks.append(" ".join(current))

        return [c for c in chunks if c.strip()]

    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [s.strip() for s in sentences if s.strip()]

    @staticmethod
    def _cosine_similarity(a: object, b: object) -> float:
        import numpy as np  # noqa: PLC0415
        a_arr = np.array(a, dtype=float)
        b_arr = np.array(b, dtype=float)
        norm = np.linalg.norm(a_arr) * np.linalg.norm(b_arr)
        if norm == 0:
            return 0.0
        return float(np.dot(a_arr, b_arr) / norm)


# ---------------------------------------------------------------------------
# Chunker facade
# ---------------------------------------------------------------------------

class Chunker:
    """
    Public facade that selects the concrete chunking strategy.

    Strategy selection priority:
    1. ``source_type`` mapping (e.g. "md" → Markdown, "py" → AST).
    2. ``ChunkingSettings.strategy`` from settings.
    """

    _SOURCE_TYPE_STRATEGY: dict[str, ChunkingStrategy] = {
        "md": ChunkingStrategy.MARKDOWN,
        "markdown": ChunkingStrategy.MARKDOWN,
        "py": ChunkingStrategy.AST,
        "python": ChunkingStrategy.AST,
    }

    def __init__(self) -> None:
        settings = get_settings()
        self._cfg = settings.chunking

    def chunk_document(
        self,
        text: str,
        document_id: str,
        source_type: Optional[str] = None,
    ) -> List[Chunk]:
        """
        Split *text* into ``Chunk`` objects.

        Parameters
        ----------
        text:
            Pre-processed document text.
        document_id:
            The parent document's ID (copied into each chunk).
        source_type:
            Optional MIME/type hint (e.g. ``"pdf"``, ``"md"``, ``"py"``) that
            may override the configured default strategy.
        """
        strategy = self._resolve_strategy(source_type)
        chunker = self._build_chunker(strategy)
        raw_chunks = chunker.split(text)

        # Filter out chunks below the minimum size
        raw_chunks = [
            c for c in raw_chunks
            if len(c.strip()) >= self._cfg.min_chunk_size
        ]

        chunks: List[Chunk] = []
        for idx, chunk_text in enumerate(raw_chunks):
            token_count = _approx_token_count(chunk_text)
            chunks.append(
                Chunk(
                    document_id=document_id,
                    text=chunk_text.strip(),
                    chunk_index=idx,
                    token_count=token_count,
                )
            )

        logger.info(
            "Chunked document %s into %d chunk(s) using %s strategy.",
            document_id,
            len(chunks),
            strategy.value,
        )
        return chunks

    def _resolve_strategy(self, source_type: Optional[str]) -> ChunkingStrategy:
        if source_type:
            st = source_type.lower()
            if st in self._SOURCE_TYPE_STRATEGY:
                return self._SOURCE_TYPE_STRATEGY[st]
        return self._cfg.strategy

    def _build_chunker(self, strategy: ChunkingStrategy) -> BaseChunker:
        common = dict(
            chunk_size=self._cfg.chunk_size,
            chunk_overlap=self._cfg.chunk_overlap,
            min_chunk_size=self._cfg.min_chunk_size,
        )
        if strategy == ChunkingStrategy.MARKDOWN:
            return MarkdownChunker(**common)
        if strategy == ChunkingStrategy.AST:
            return ASTChunker(**common)
        if strategy == ChunkingStrategy.SEMANTIC:
            return SemanticChunker(
                **common,
                similarity_threshold=self._cfg.semantic_similarity_threshold,
            )
        # Default: RECURSIVE
        return RecursiveChunker(**common)


__all__ = [
    "Chunker",
    "BaseChunker",
    "RecursiveChunker",
    "MarkdownChunker",
    "ASTChunker",
    "SemanticChunker",
]
