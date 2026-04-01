"""Build the ChromaDB vector store from SDTM domain/variable specifications.

Fixes applied:
- M1: Targeted ValueError catch instead of bare except
- H5: configure_logging() called at entry point
"""

from __future__ import annotations

import contextlib

import chromadb
import structlog
import typer

from sdtm_mapping_ai.config import get_settings
from sdtm_mapping_ai.rag.embeddings import get_embedding_model
from sdtm_mapping_ai.sdtm.controlled_terminology import ControlledTerminology
from sdtm_mapping_ai.sdtm.standards import get_all_domains
from sdtm_mapping_ai.utils.logging import configure_logging

logger = structlog.get_logger()
app = typer.Typer()


def build_documents() -> tuple[list[str], list[str], list[dict]]:
    """Build document chunks from SDTM domain and variable specs."""
    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict] = []
    ct = ControlledTerminology()
    domains = get_all_domains()

    for code, domain in domains.items():
        doc_id = f"domain_{code}"
        doc_text = domain.to_context_string()
        ids.append(doc_id)
        documents.append(doc_text)
        metadatas.append({
            "type": "domain",
            "domain_code": code,
            "domain_name": domain.name,
            "observation_class": domain.observation_class.value,
        })

        for var in domain.variables:
            var_id = f"var_{code}_{var.name}"
            ct_terms = ""
            if var.codelist:
                terms = ct.get_valid_terms(var.codelist)
                if terms:
                    ct_terms = f"\nControlled Terminology ({var.codelist}): {', '.join(terms)}"

            var_text = (
                f"Domain: {code} ({domain.name})\n"
                f"Variable: {var.name}\n"
                f"Label: {var.label}\n"
                f"Type: {var.data_type.value}\n"
                f"Core: {var.core.value}\n"
                f"Description: {var.description}"
                f"{ct_terms}"
            )
            ids.append(var_id)
            documents.append(var_text)
            metadatas.append({
                "type": "variable",
                "domain_code": code,
                "variable_name": var.name,
                "variable_label": var.label,
                "core": var.core.value,
            })

    logger.info("documents_built", total=len(documents))
    return ids, documents, metadatas


@app.command()
def main(
    persist_dir: str = typer.Option(None, help="ChromaDB persist directory"),
    collection_name: str = typer.Option(None, help="Collection name"),
) -> None:
    """Build the SDTM knowledge base vector store."""
    configure_logging()  # FIX H5
    settings = get_settings()
    persist = persist_dir or settings.chroma_persist_dir
    coll_name = collection_name or settings.chroma_collection

    logger.info("building_index", persist_dir=persist, collection=coll_name)
    ids, documents, metadatas = build_documents()

    embed_model = get_embedding_model(settings.embedding_model)
    logger.info("generating_embeddings", count=len(documents))
    embeddings = embed_model.embed_batch(documents)

    client = chromadb.PersistentClient(path=persist)

    # FIX M1: targeted exception instead of bare except
    with contextlib.suppress(ValueError):
        client.delete_collection(coll_name)  # missing collection on first run

    collection = client.create_collection(
        name=coll_name,
        metadata={"hnsw:space": "cosine"},
    )
    collection.add(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)

    logger.info("index_built", documents=len(documents), persist_dir=persist)
    typer.echo(f"✓ Index built: {len(documents)} documents in {persist}")


if __name__ == "__main__":
    app()
