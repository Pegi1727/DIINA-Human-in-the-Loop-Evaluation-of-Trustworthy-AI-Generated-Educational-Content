# DIINA results/

Final statistical outputs for DIINA v1.00, produced programmatically by the reproducible
analysis scripts (see scripts/). No values are entered manually.

## Files
| File | Description |
|---|---|
| descriptive_statistics.csv | Mean, SD, median, min/max, IQR, 95% CI per dimension and condition (Baseline vs DIINA; N=20 each). |
| inter_rater_agreement.csv | Two-rater exact agreement and ICC(2,1). **Boundary condition:** 100% agreement, ICC(2,1)=1.000, MS_error=0; degenerate CIs omitted / marked indeterminate; F-based tests not applicable. |
| condition_comparison.csv | Paired t-tests (DIINA vs baseline) per dimension and composite with Cohen's d_z. |
| cluster_analysis.csv | Four thematic clusters: Fundamental (Basic Machine Learning), Advanced (Advanced Neural Architectures), Applied (Applied Modeling), Socio-Technical (Socio-Technical Implications). |
| item_level_scores.csv | Per-unit scores by condition and dimension; no evaluator identifiers. |
| data_quality_report.txt | Record counts, missing values, score ranges, duplicates, agreement checks. |

## Methodological caveat (mandatory)
Both evaluators assigned identical ratings on all 40 evaluated units across all four
dimensions. Unanimous agreement reflects standardized rubric calibration / consensus
protocol under zero within-unit variance; it does NOT constitute independent empirical
external validation of the framework. No degenerate CI or F-based significance values
are reported for inter-rater reliability.

## How to reproduce
Run `scripts/08_run_all.py` (or each numbered script in order) against the released
dataset files; all files here are regenerated deterministically.

## Limitations
- Single-site evaluation, N=20 items, two raters with perfect consensus (no independent rater variance).
- Condition comparison assumes the paired design and normality of differences.
