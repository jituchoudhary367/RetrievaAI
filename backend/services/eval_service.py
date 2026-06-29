"""
services/eval_service.py

Retrieval-quality offline evaluation (§1.6).

Replays every EvalQuery through HybridRetriever and computes:
  - MRR (Mean Reciprocal Rank)
  - Hit Rate @ 5
  - NDCG @ 10
  - Top-1 Accuracy

Results are stored in an EvalRun row. The Analytics page shows the LAST
EvalRun labeled with its timestamp — this is explicitly NOT a live metric.

Trigger via POST /api/analytics/eval/run (TENANT_ADMIN only).
"""

from __future__ import annotations

import json
import logging
import math
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.engine import async_session_factory
from db.models.eval import EvalQuery, EvalRun
from retrieval.hybrid_retriever import HybridRetriever

logger = logging.getLogger(__name__)


def _compute_metrics(
    results: List[List[str]],  # List of retrieved doc_id lists (one per query)
    expected: List[List[str]],  # List of expected doc_id lists (one per query)
    at_k: int = 5,
    ndcg_k: int = 10,
) -> Dict[str, float]:
    """
    Compute MRR, Hit Rate@k, NDCG@k, and Top-1 Accuracy.

    Parameters
    ----------
    results:  List of ranked retrieved document_id lists (one per query)
    expected: List of expected document_id sets (one per query)
    """
    n = len(results)
    if n == 0:
        return {}

    mrr_sum = 0.0
    hit_sum = 0.0
    ndcg_sum = 0.0
    top1_sum = 0.0

    for retrieved, gold in zip(results, expected):
        gold_set = set(gold)

        # MRR — reciprocal rank of first relevant result
        rr = 0.0
        for rank, doc_id in enumerate(retrieved, start=1):
            if doc_id in gold_set:
                rr = 1.0 / rank
                break
        mrr_sum += rr

        # Hit Rate @ k
        top_k = retrieved[:at_k]
        if any(d in gold_set for d in top_k):
            hit_sum += 1.0

        # Top-1 Accuracy
        if retrieved and retrieved[0] in gold_set:
            top1_sum += 1.0

        # NDCG @ ndcg_k
        top_ndcg = retrieved[:ndcg_k]
        dcg = sum(
            1.0 / math.log2(rank + 1)
            for rank, doc_id in enumerate(top_ndcg, start=1)
            if doc_id in gold_set
        )
        ideal_hits = min(len(gold_set), ndcg_k)
        idcg = sum(1.0 / math.log2(rank + 1) for rank in range(1, ideal_hits + 1))
        ndcg_sum += (dcg / idcg) if idcg > 0 else 0.0

    return {
        "mrr": round(mrr_sum / n, 4),
        f"hit_rate_at_{at_k}": round(hit_sum / n, 4),
        f"ndcg_at_{ndcg_k}": round(ndcg_sum / n, 4),
        "top1_accuracy": round(top1_sum / n, 4),
        "num_queries": n,
    }


async def run_eval(tenant_id: str) -> str:
    """
    Run a full evaluation pass for *tenant_id*.

    Returns the EvalRun ID.
    """
    async with async_session_factory() as db:
        # Create the EvalRun row
        run = EvalRun(tenant_id=tenant_id, status="running")
        db.add(run)
        await db.flush()
        run_id = run.id

        # Load all EvalQuery rows for this tenant
        result = await db.execute(
            select(EvalQuery).where(EvalQuery.tenant_id == tenant_id)
        )
        eval_queries = result.scalars().all()

        if not eval_queries:
            run.status = "completed"
            run.metrics = json.dumps({"error": "No eval queries defined for this tenant"})
            run.completed_at = datetime.now(timezone.utc)
            await db.commit()
            return run_id

        try:
            retriever = HybridRetriever()
            all_retrieved: List[List[str]] = []
            all_expected: List[List[str]] = []

            for eq in eval_queries:
                expected_ids = json.loads(eq.expected_document_ids)
                chunks = retriever.retrieve(query=eq.query_text, top_k=10)
                retrieved_doc_ids = list(dict.fromkeys(c.document_id for c in chunks))
                all_retrieved.append(retrieved_doc_ids)
                all_expected.append(expected_ids)

            metrics = _compute_metrics(all_retrieved, all_expected)
            run.status = "completed"
            run.metrics = json.dumps(metrics)
            run.completed_at = datetime.now(timezone.utc)
        except Exception as exc:  # noqa: BLE001
            logger.error("EvalRun %s failed: %s", run_id, exc, exc_info=True)
            run.status = "failed"
            run.error_message = str(exc)
            run.completed_at = datetime.now(timezone.utc)

        await db.commit()
    return run_id


async def get_latest_eval_run(db: AsyncSession, tenant_id: str) -> Optional[EvalRun]:
    """Return the most recent EvalRun for a tenant."""
    result = await db.execute(
        select(EvalRun)
        .where(EvalRun.tenant_id == tenant_id)
        .order_by(EvalRun.triggered_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


__all__ = ["run_eval", "get_latest_eval_run", "_compute_metrics"]
