# IMPORTANT: All indented recipe lines below MUST use literal tab characters,
# not spaces. If your editor converted tabs to spaces, run:
#   sed -i 's/^    /\t/' Makefile
.PHONY: setup download-data build-index run eval test lint clean help

PYTHON ?= python
INPUT  ?= data/pilot01/
OUTPUT ?= results/

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup: download-data build-index  ## Full setup: download data + build vector index

download-data:  ## Download CDISC Pilot 01 public datasets
	$(PYTHON) data/scripts/download_cdisc_pilot.py
	$(PYTHON) data/scripts/build_sdtm_knowledge_base.py

build-index:  ## Build the ChromaDB vector store
	$(PYTHON) -m sdtm_mapping_ai.rag.build_index

run:  ## Run the mapping pipeline (INPUT=... OUTPUT=...)
	$(PYTHON) -m sdtm_mapping_ai.pipeline.run --input $(INPUT) --output $(OUTPUT)

dry-run:  ## Profile data without making LLM calls
	$(PYTHON) -m sdtm_mapping_ai.pipeline.run --input $(INPUT) --output $(OUTPUT) --dry-run

eval:  ## Evaluate predictions against gold standard
	$(PYTHON) -m sdtm_mapping_ai.evaluation.run_eval \
		--predictions $(OUTPUT)/mappings.csv \
		--gold-standard data/pilot01/gold_standard.csv

test:  ## Run unit tests (no API calls)
	$(PYTHON) -m pytest -m "not integration and not slow" --cov=sdtm_mapping_ai -v

lint:  ## Lint and type-check
	ruff check src/ tests/
	mypy src/sdtm_mapping_ai/ --ignore-missing-imports

clean:  ## Remove generated artifacts
	rm -rf data/chroma_db/ results/*.csv results/*.json
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
