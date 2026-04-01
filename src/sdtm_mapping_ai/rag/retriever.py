"""Semantic retriever for SDTM knowledge base with two-stage retrieval."""

from __future__ import annotations

from dataclasses import dataclass

import chromadb
import structlog

from sdtm_mapping_ai.config import get_settings
from sdtm_mapping_ai.rag.embeddings import get_embedding_model

logger = structlog.get_logger()


@dataclass
class RetrievalResult:
    doc_id: str
    document: str
    metadata: dict
    distance: float

    @property
    def relevance_score(self) -> float:
        return max(1.0 - self.distance, 0.0)


class SDTMRetriever:
    def __init__(
        self,
        persist_dir: str | None = None,
        collection_name: str | None = None,
        embedding_model_name: str | None = None,
    ) -> None:
        settings = get_settings()
        self._persist_dir = persist_dir or settings.chroma_persist_dir
        self._collection_name = collection_name or settings.chroma_collection
        self._embed_model = get_embedding_model(
            embedding_model_name or settings.embedding_model
        )
        self._client: chromadb.PersistentClient | None = None
        self._collection = None

    @property
    def collection(self):
        if self._collection is None:
            self._client = chromadb.PersistentClient(path=self._persist_dir)
            self._collection = self._client.get_collection(self._collection_name)
        return self._collection

    def retrieve(
        self, query: str, n_results: int = 10, filter_type: str | None = None,
    ) -> list[RetrievalResult]:
        query_embedding = self._embed_model.embed_text(query)
        where_filter = {"type": filter_type} if filter_type else None

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        retrieval_results = []
        for i in range(len(results["ids"][0])):
            retrieval_results.append(RetrievalResult(
                doc_id=results["ids"][0][i],
                document=results["documents"][0][i],
                metadata=results["metadatas"][0][i],
                distance=results["distances"][0][i],
            ))

        logger.debug(
            "retrieval_complete", query=query[:80],
            n_results=len(retrieval_results),
            top_score=retrieval_results[0].relevance_score if retrieval_results else 0,
        )
        return retrieval_results

    def retrieve_for_source_variable(
        self,
        variable_name: str,
        variable_label: str,
        sample_values: list[str] | None = None,
        dataset_name: str | None = None,
    ) -> list[RetrievalResult]:
        query_parts = [f"Variable: {variable_name}", f"Label: {variable_label}"]
        if dataset_name:
            query_parts.append(f"Source dataset: {dataset_name}")
        if sample_values:
            safe = [v[:100] for v in sample_values[:5]]
            query_parts.append(f"Sample values: {', '.join(safe)}")
        query = "\n".join(query_parts)

        domain_results = self.retrieve(query, n_results=3, filter_type="domain")
        variable_results = self.retrieve(query, n_results=7, filter_type="variable")

        seen_ids: set[str] = set()
        combined = []
        for r in domain_results + variable_results:
            if r.doc_id not in seen_ids:
                seen_ids.add(r.doc_id)
                combined.append(r)

        return sorted(combined, key=lambda r: r.relevance_score, reverse=True)[:10]

    def format_context(self, results: list[RetrievalResult], max_chars: int = 4000) -> str:
        lines = ["## Relevant SDTM Context\n"]
        char_count = 0
        for r in results:
            chunk = f"[Score: {r.relevance_score:.3f}]\n{r.document}\n---\n"
            if char_count + len(chunk) > max_chars:
                break
            lines.append(chunk)
            char_count += len(chunk)
        return "\n".join(lines)
