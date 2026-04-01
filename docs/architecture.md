# Architecture Documentation

## System Design

The SDTM Mapping AI system implements a three-stage pipeline that mirrors
the "Generation 3" architecture described in the companion paper.

### Stage 1: Source Data Profiling
- Reads CSV and XPT files from the input directory
- Extracts: variable names, labels, data types, unique counts, sample values
- Produces a `DatasetProfile` object per input file
- Memory-efficient: samples only 1,000 rows for profiling

### Stage 2: RAG-Enhanced LLM Mapping (Concurrent)
For each source variable (processed concurrently via ThreadPoolExecutor):
1. **Retrieval**: Query ChromaDB with variable metadata → domain + variable specs
2. **Domain Prediction**: LLM classifies into SDTM domain
3. **Variable Mapping**: LLM maps to target variable within domain

All LLM calls use the shared `LLMClient` with automatic retry (3 attempts,
exponential backoff) on transient API failures.

### Stage 3: Validation & Output
- Confidence scoring with threshold-based routing (accept / review / reject)
- Conformance checking against SDTM structural rules and Controlled Terminology
- Output as CSV mapping specification with audit trail

## Key Design Decisions

### Shared LLMClient (C1 fix)
A single `LLMClient` class handles all LLM interactions, eliminating code
duplication between DomainPredictor and VariableMapper. Retry logic lives
in one place via tenacity decorators.

### Concurrent Mapping (H1 fix)
Variables are mapped in parallel using `ThreadPoolExecutor` gated by
`MAX_CONCURRENT_CALLS`. This provides ~5× throughput improvement on typical
studies while respecting API rate limits.

### Human-in-the-Loop
The confidence scorer partitions mappings into three buckets:
- `auto_accept`: confidence >= threshold (default 0.70)
- `human_review`: confidence >= threshold * 0.5
- `reject`: confidence < threshold * 0.5
