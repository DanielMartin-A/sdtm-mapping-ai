# SDTM Mapping AI

**AI-Powered SDTM Domain Prediction and Variable Mapping Using LLMs and RAG**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **Disclaimer:** This implementation uses exclusively publicly available data. It does not reflect, derive from, or use any proprietary systems, data, or trade secrets of any employer. All concepts are based on generalized industry standards and publicly available CDISC resources.

## Overview

This repository implements an AI-driven SDTM (Study Data Tabulation Model) mapping system that demonstrates the three-generation automation architecture described in the companion paper *"Automating SDTM Mapping with Artificial Intelligence and Large Language Models: A Narrative Review"*.

The system combines:
- **Retrieval-Augmented Generation (RAG)** with CDISC standards as the knowledge base
- **LLM-based domain prediction** — classifying source variables into SDTM domains
- **Variable-level mapping** — matching source fields to target SDTM variables with confidence scores
- **Human-in-the-loop review** — routing low-confidence predictions for expert validation
- **Automated conformance checking** against CDISC Controlled Terminology

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SDTM Mapping Pipeline                     │
├──────────┬──────────┬───────────┬────────────┬──────────────┤
│  Source  │  RAG     │  LLM      │ Confidence │   Human      │
│  Data    │  Context │  Mapping  │ Scoring &  │   Review     │
│  Profiler│  Engine  │  Engine   │ Validation │   Interface  │
└──────────┴──────────┴───────────┴────────────┴──────────────┘
│              │              │              │
▼              ▼              ▼              ▼
┌──────────────────────────────────────────────────────┐
│              CDISC Knowledge Base (Vector Store)      │
│  SDTMIG v3.4 specs │ Controlled Terminology │ aCRFs  │
└──────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# 1. Clone and install
git clone https://github.com/YOUR_USERNAME/sdtm-mapping-ai.git
cd sdtm-mapping-ai
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# 2. Configure
cp .env.example .env   # Edit with your API keys

# 3. Download public data and build index
make setup           # Or run the steps manually:
# python data/scripts/download_cdisc_pilot.py
# python data/scripts/build_sdtm_knowledge_base.py
# python -m sdtm_mapping_ai.rag.build_index

# 4. Run the pipeline
make run INPUT=data/pilot01/ OUTPUT=results/
# Or: python -m sdtm_mapping_ai.pipeline.run --input data/pilot01/ --output results/

# 5. Evaluate
make eval
# Or: python -m sdtm_mapping_ai.evaluation.run_eval \
#        --predictions results/mappings.csv \
#        --gold-standard data/pilot01/gold_standard.csv
```

## Public Data Sources

|Source                                                                 |Description                                  |License        |
|------------------------------------------------------------------------|---------------------------------------------|---------------|
|[CDISC Pilot 01](https://github.com/cdisc-org/sdtm-adam-pilot-project) |Complete SDTM datasets (DM, AE, LB, VS, etc.)|Public         |
|[CDISC Controlled Terminology](https://www.cdisc.org/standards/terminology)|Quarterly CT releases                        |Free download  |
|[CDISC SDTMIG v3.4](https://www.cdisc.org/standards/foundational/sdtmig) |Implementation guide specifications          |Public standard|

## Citation

```bibtex
@misc{arogyasami2026sdtm,
  title={Automating SDTM Mapping with Artificial Intelligence and Large
         Language Models: A Narrative Review},
  author={Arogyasami, DanielMartin},
  year={2026},
  note={Preprint}
}
```

## License

MIT License — see [LICENSE](LICENSE) for details.
