Topics: clinical-trials, cdisc, sdtm, machine-learning, llm, healthcare-ai

# SDTM Mapping AI (sdtm-mapping-ai)

> **⚠️ INDEPENDENCE & DATA DISCLAIMER:** This reference implementation uses exclusively publicly available data (CDISC Pilot 01). It does not reflect, derive from, or use any proprietary systems, workflows, data, or trade secrets of any current or past employers. This work is an independent academic and open-source contribution.

## Overview
This repository provides a machine learning and LLM-assisted pipeline for predicting CDISC Study Data Tabulation Model (SDTM) domains and mapping raw Electronic Data Capture (EDC) variables to target SDTM specifications. It serves as the companion reference implementation to the narrative review paper: *"Automating SDTM Mapping with Artificial Intelligence and Large Language Models"*.

## Architecture
The pipeline implements a two-stage approach:
1. **Domain Prediction:** A supervised classifier (XGBoost/Siamese Network) trained on historical public mappings assigns a target domain (e.g., `AE`, `VS`, `LB`).
2. **Variable Mapping:** For the predicted domain, an LLM utilizing Retrieval-Augmented Generation (RAG) semantically matches source variables to SDTM target variables using CDISC Implementation Guide (SDTMIG) rules as context.

## Public Dataset Acquisition
This project relies **strictly** on the publicly available CDISC Pilot 01 dataset.
1. Clone the official CDISC repository:
   ```bash
   git clone [https://github.com/cdisc-org/sdtm-adam-pilot-project.git](https://github.com/cdisc-org/sdtm-adam-pilot-project.git) data/raw/cdisc-pilot
Run the ingestion script to parse the .xpt transport files into pandas dataframes:

Bash

python src/ingestion/xpt_parser.py --input data/raw/cdisc-pilot --output data/processed/
Quick Start
Bash

# Install dependencies
pip install -r requirements.txt

# Run the end-to-end mapping pipeline on the public AE domain
python src/main.py --domain AE --input data/processed/ae_raw.csv --output results/ae_mapped.csv
Citation
If you use this code, please cite the companion preprint:

Code snippet

@article{arogyasami2026sdtmautomation,
  title={Automating SDTM Mapping with Artificial Intelligence and Large Language Models: A Narrative Review},
  author={Arogyasami, DanielMartin},
  year={2026},
  journal={Preprint}
}
