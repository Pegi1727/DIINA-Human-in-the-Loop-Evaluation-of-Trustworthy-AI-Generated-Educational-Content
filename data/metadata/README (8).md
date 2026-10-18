# DIINA Structured Data Repository

**DIINA — Domain-Informed Intelligent Needs-Adaptive Assessment Framework**
Pilot Evaluation Dataset and Reproducible Analysis Results
Target journal: *Educational Technology & Society*

Version: 1.0 | Last updated: 2025 | License: CC BY 4.0 (recommended for data; code under MIT)

---

## 1. Overview

This repository contains the complete, reproducible evidence base for the pilot evaluation of the **DIINA** framework. Twenty benchmark items across four educational-technology domains (Fundamental, Advanced, Applied, Socio-Technical) were generated under two conditions: a **Baseline** (generic large-language-model output) and the **DIINA-curated pipeline**. Five blinded evaluators independently rated every item under four quality dimensions on a 1–5 Likert scale, yielding 200 ratings. The DIINA arm significantly outperformed the baseline on all dimensions (all *p* < .001, *d_z* ≈ 2.7–2.9).

## 2. Repository Structure

```
diina_data_repository/
├── raw/                                  # Unprocessed data, pre-cleaning/analysis
│   ├── DIINA_Pilot_Evaluation_Matrix.xlsx # Provenance & audit log workbook (blinded raw ratings)
│   ├── raw_llm_outputs.csv                # Baseline raw LLM outputs (20 items)
│   └── diina_curated_outputs.csv          # Curated/revised outputs with revision rationale & hashes
├── processed/                            # Cleaned, analysis-ready data
│   ├── diina_evaluation_clean.csv         # 200 records (20 items × 2 conditions × 5 evaluators)
│   ├── diina_composite_scores.csv         # Item-level composites per condition + deltas
│   └── diina_item_level_scores.csv        # Dimension means per item × condition
├── results/                              # Reproducible statistical outputs
│   ├── descriptive_statistics.csv         # N, mean, SD, median, min/max, IQR, 95% CI
│   ├── paired_t_tests.csv                 # Paired t-tests (Baseline vs DIINA), 5 dimensions
│   ├── effect_sizes.csv                   # Cohen's dz, Hedges' g, win rate, CLES
│   ├── inter_rater_reliability.csv        # ICC(2,1) with 95% CIs and classification
│   └── subdomain_analysis.csv             # Domain-level breakdowns (4 domains)
└── metadata/                             # Documentation
    ├── data_dictionary.csv                # Variable-level definitions (59 entries)
    ├── README.md                          # This document
    └── evaluation_rubric.pdf              # Official 5-dimension, 5-point scoring rubric
```

## 3. Data Provenance

1. **Item generation.** Twenty educational-technology concepts (5 per domain) were selected from a curated curriculum map. Baseline outputs were produced with a fixed, standardized prompt requesting academically rigorous educational content.
2. **DIINA curation.** Each baseline output was processed through the DIINA domain-informed pipeline; every revision is logged in `diina_curated_outputs.csv` with a `Revision_Rationale` and a per-item `SHA256_Hash`.
3. **Blinded evaluation.** Five evaluators rated both arms of each item independently and blind to condition (`Arm_Condition` recorded only in the analysis key). Ratings were collected in the pilot evaluation matrix workbook (`raw/DIINA_Pilot_Evaluation_Matrix.xlsx`), which includes a provenance and audit log sheet.
4. **Processing.** Raw ratings were cleaned, unitized (`Record_ID`, `Unit_ID`), and aggregated into processed tables; all statistics in `results/` were computed from `processed/diina_evaluation_clean.csv` only.

## 4. File Inventory and SHA-256 Hashes

| File | Size (bytes) | SHA-256 |
|---|---|---|
| raw/DIINA_Pilot_Evaluation_Matrix.xlsx | 14,754 | `a575fc59d54d70e9fb703f838571dc84e35b45d40a9dad32fa72d2e389396af8` |
| raw/diina_curated_outputs.csv | 15,103 | `026f563accc31add8f28cabcf23a2995b348d49441163a58a5fc4b0958171c83` |
| raw/raw_llm_outputs.csv | 60,940 | `40339d84aae7631211dc81796de88ddb230dd27b20083f4e72d23d715dc96eaa` |
| processed/diina_evaluation_clean.csv | 11,335 | `97791fbe1266bc2b77894619e3952c7f325c9d893a7999ea8d27cfa70a1636f6` |
| processed/diina_composite_scores.csv | 886 | `4d5d976c2fe7f6563f4ff5ad6825104044e302c1820209354e5cd22110c56788` |
| processed/diina_item_level_scores.csv | 2,325 | `2970ce02415fc6a3214c11daf66a4276a866cb2c20f7c175799f2b4601fde515` |
| results/descriptive_statistics.csv | 811 | `e693299501774a5c73620881fc4a0a9c4f87ad52302627abd508e0905bd060c7` |
| results/paired_t_tests.csv | 421 | `9b5837a376ab86d7e2e8b6a7319d7159c37f06e1e9725bc5397cad4d8622fee8` |
| results/effect_sizes.csv | 264 | `8826db595c2adb9b43458d83557e2d570112e0ebd96b7fa2e7d3cad80cf09931` |
| results/inter_rater_reliability.csv | 394 | `8e15e7e2ce0fe09b72733a19b645fceda87b8de8c5957dde8fdd8c6b0777af45` |
| results/subdomain_analysis.csv | 326 | `7ac5ee5b5d51af7eeb0b455b3887456c86d77822d0ca6716d90fbe6fdcf1a2ed` |
| metadata/data_dictionary.csv | 6,517 | `c28267a6f012d8e78898e4920f18d01ad93e63b94d091ac2110174209eba7d95` |

Verify locally (Linux/macOS): `sha256sum <file>`; Windows PowerShell: `Get-FileHash <file> -Algorithm SHA256`.

## 5. Reproduction Guidelines

All text CSV files are UTF-8 encoded with BOM and comma-delimited. To reproduce the results:

1. Load `processed/diina_evaluation_clean.csv` (200 rows; 10 columns; ratings 1–5).
2. Compute per-item dimension means, aggregated by `Item_ID` × `Arm_Condition` → reproduce `processed/diina_item_level_scores.csv`.
3. Pair the two arms per item (10 pairwise dimensions × 20 items) → reproduce `results/paired_t_tests.csv` (paired *t*, df = 19, two-tailed).
4. Compute Cohen's *d_z* = mean(diff)/SD(diff), Hedges' *g*, win rate, and CLES → `results/effect_sizes.csv`.
5. ICC(2,1) with 95% CI (two-way random, single measures, absolute agreement) on the 20×5 evaluator matrix per dimension → `results/inter_rater_reliability.csv`.
6. Group items by `Domain` → `results/subdomain_analysis.csv`.
7. Descriptives (mean, SD, median, min, max, IQR, 95% CI) per condition → `results/descriptive_statistics.csv`.

Recommended environment: Python ≥ 3.10 with `pandas`, `numpy`, `scipy`, `pingouin` (or equivalent R: `psych`, `effectsize`).

**Key headline results (for quick verification):** Composite Score Baseline M = 3.750 vs DIINA M = 4.508, Δ = 0.758, *t*(19) = 12.965, *p* < .001, *d_z* = 2.899.

## 6. Evaluation Rubric Summary

Five dimensions, each scored 1–5 (see `metadata/evaluation_rubric.pdf` for full anchors):
**Technical Accuracy**, **Pedagogical Appropriateness**, **Linguistic Suitability**, **Cultural & Contextual Relevance**, and the **Composite** (equal-weight mean). Full anchors: 1 = Unacceptable, 2 = Poor, 3 = Adequate, 4 = Good, 5 = Excellent.

## 7. Ethical Framework

- **Human oversight:** All DIINA outputs were human-curated and logged; no unreviewed AI text was evaluated as final content.
- **Blinding:** Evaluators were blinded to generation condition to prevent systematic bias.
- **No personal data:** The dataset contains no human-subject personal identifiers; evaluator identities are pseudonymized (EV_01–EV_05) and no consent-sensitive data is included.
- **Transparency:** Every transformation from raw outputs to published statistics is documented in `metadata/data_dictionary.csv` and reproducible from the files above.
- **Academic integrity:** The repository is intended to support transparent, verifiable reporting per *Educational Technology & Society* data-availability policies. Users must cite this dataset and the accompanying article; re-use of the benchmark items requires attribution (CC BY 4.0).
- **Fairness & bias:** Cultural relevance was explicitly evaluated as a dimension; residual limitations (evaluator panel composition, single-prompt baseline) are acknowledged in the accompanying manuscript.

## 8. Contact

Corresponding author — DIINA project. For questions, access to audit logs, or re-use permissions, contact the repository maintainer listed with the submission.
