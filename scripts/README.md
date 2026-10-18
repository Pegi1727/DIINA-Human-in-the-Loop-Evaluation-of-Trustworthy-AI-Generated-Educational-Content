# DIINA Reproducible Analysis Scripts

Pipeline for the DIINA framework evaluation study (20 items x 2 arms = 40 evaluation
units, 5 rubric dimensions, 3 calibrated raters).

## Contents
| File | Purpose |
|---|---|
| `03_descriptive_statistics.py` | Descriptive statistics of rubric ratings per arm/dimension |
| `04_inter_rater_agreement.py` | ICC(2,1), ANOVA mean squares, unanimous-agreement audit |
| `05_condition_comparison.py` | Control vs. DIINA arm comparison (t-test, Mann-Whitney, d) |
| `06_cluster_analysis.py` | K-means clustering of the 40 evaluation units |
| `07_generate_tables.py` | Assembles LaTeX/text tables from all outputs |
| `08_run_all.py` | Runs the full pipeline end-to-end |
| `tests/test_pipeline.py` | Pytest suite verifying key statistical claims |

## Usage
```bash
python 08_run_all.py          # full pipeline -> ./outputs/
pytest tests/ -v              # verification suite
```

Dependencies: `numpy`, `pandas`, `scipy`, `scikit-learn`, `pytest`.

## Key methodological notes (Step 04)
- 100% unanimous agreement across all 40 evaluation units and all rubric dimensions.
- ICC(2,1) point estimate = 1.000; MS_error = 0 and MS_rater = 0.
- The F-ratio confidence interval for ICC(2,1) is degenerate under zero residual
  variance and is therefore omitted / documented as indeterminate.
- **Caveat:** Unanimous agreement reflects standardized rubric calibration /
  consensus rating protocol and must NOT be interpreted as independent empirical
  validation of the framework.
