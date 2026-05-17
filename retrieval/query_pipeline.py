"""Retrieval orchestrator — BM25-only for the FDE deployment scaffold.

The genai-engineer repo uses hybrid (BM25 + dense). For the FDE deployment
scaffold we keep it BM25-only to minimize runtime dependencies on the
customer's VPC (no sentence-transformers model download needed).

When upgrading the customer to hybrid, swap this file with the one from
healthcare-genai-engineer/retrieval/query_pipeline.py.
"""
from __future__ import annotations
from typing import Literal

from .retriever import search as _bm25_search

Method = Literal["bm25"]


class QueryPipeline:
    """Lightweight retrieval facade — BM25 only."""

    def retrieve(
        self,
        query: str,
        *,
        k: int = 5,
        method: Method = "bm25",
    ) -> list[dict]:
        return _bm25_search(query, k=k)
