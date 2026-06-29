"""
tools/code_search.py

Pure-stdlib code search across a Python repository.

Two search modes:
  1. Symbol search  — AST-based enumeration of function/class definitions
     whose names contain the query string (case-insensitive substring match).
  2. Substring search — plain text grep across all *.py files.

Both modes are combined and de-duplicated before returning the top-k results.

No third-party dependencies — uses only ``ast``, ``pathlib``, and stdlib.
"""

from __future__ import annotations

import ast
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class CodeSearchTool:
    """
    Searches Python source files for symbols and text patterns.

    Parameters
    ----------
    encoding:
        File encoding used when reading source files (default ``utf-8``).
    """

    def __init__(self, encoding: str = "utf-8") -> None:
        self._encoding = encoding

    def search(
        self,
        query: str,
        repo_path: str,
        top_k: int = 10,
        tenant_id: Optional[str] = None,
    ) -> List[Dict]:
        """
        Search *repo_path* for Python symbols and text matching *query*.

        Parameters
        ----------
        query:
            Search string.  Used both as a symbol-name substring and as a
            literal text pattern.
        repo_path:
            Absolute or relative path to the repository root.
        top_k:
            Maximum number of results to return.

        Returns
        -------
        List of dicts, each with keys:
            ``file_path``    — str path to the file
            ``symbol_name``  — function/class name (empty for text matches)
            ``symbol_type``  — ``"function"``, ``"class"``, or ``"text_match"``
            ``snippet``      — up to 10 lines of source context
            ``line_number``  — 1-based line number of the match
        """
        import time
        import asyncio
        from services.tool_logger import log_tool_execution

        start_time = time.perf_counter()
        tool_id = "00000000-0000-0000-0001-000000000003"

        def _log(status: str, error: Optional[str] = None):
            if tenant_id:
                latency_ms = (time.perf_counter() - start_time) * 1000
                asyncio.create_task(log_tool_execution(
                    tenant_id=tenant_id,
                    tool_id=tool_id,
                    status=status,
                    latency_ms=latency_ms,
                    error_message=error
                ))

        root = Path(repo_path)
        if not root.exists():
            logger.warning("CodeSearchTool: repo_path %s does not exist.", repo_path)
            _log("failed", f"repo_path {repo_path} does not exist")
            return []

        py_files = list(root.rglob("*.py"))
        if not py_files:
            logger.info("No Python files found under %s.", repo_path)
            _log("success")
            return []

        results: List[Dict] = []
        seen: set = set()  # (file_path, line_number) dedup key

        for file_path in py_files:
            file_results = self._search_file(file_path, query, root)
            for r in file_results:
                key = (r["file_path"], r["line_number"])
                if key not in seen:
                    seen.add(key)
                    results.append(r)

        # Sort by symbol matches first, then text matches; stable sort
        results.sort(key=lambda r: (0 if r["symbol_type"] != "text_match" else 1))
        _log("success")
        return results[:top_k]

    # ------------------------------------------------------------------
    # Per-file search
    # ------------------------------------------------------------------

    def _search_file(
        self, file_path: Path, query: str, root: Path
    ) -> List[Dict]:
        try:
            source = file_path.read_text(encoding=self._encoding, errors="replace")
        except Exception as exc:  # noqa: BLE001
            logger.debug("Could not read %s: %s", file_path, exc)
            return []

        lines = source.splitlines()
        str_path = str(file_path.relative_to(root))
        results: List[Dict] = []

        # --- AST symbol search ---
        results.extend(self._ast_search(source, lines, str_path, query))

        # --- Text/substring search ---
        results.extend(self._text_search(lines, str_path, query))

        return results

    def _ast_search(
        self, source: str, lines: List[str], file_path: str, query: str
    ) -> List[Dict]:
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return []

        query_lower = query.lower()
        results: List[Dict] = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                symbol_type = "function"
            elif isinstance(node, ast.ClassDef):
                symbol_type = "class"
            else:
                continue

            if query_lower not in node.name.lower():
                continue

            lineno = node.lineno
            end_lineno = getattr(node, "end_lineno", lineno + 10)
            snippet_lines = lines[lineno - 1 : min(end_lineno, lineno + 9)]
            snippet = "\n".join(snippet_lines)

            results.append(
                {
                    "file_path": file_path,
                    "symbol_name": node.name,
                    "symbol_type": symbol_type,
                    "snippet": snippet,
                    "line_number": lineno,
                }
            )

        return results

    def _text_search(
        self, lines: List[str], file_path: str, query: str
    ) -> List[Dict]:
        try:
            pattern = re.compile(re.escape(query), re.IGNORECASE)
        except re.error:
            pattern = re.compile(re.escape(query), re.IGNORECASE)

        results: List[Dict] = []
        for lineno, line in enumerate(lines, start=1):
            if pattern.search(line):
                start = max(0, lineno - 2)
                end = min(len(lines), lineno + 3)
                snippet = "\n".join(lines[start:end])
                results.append(
                    {
                        "file_path": file_path,
                        "symbol_name": "",
                        "symbol_type": "text_match",
                        "snippet": snippet,
                        "line_number": lineno,
                    }
                )
        return results


__all__ = ["CodeSearchTool"]
