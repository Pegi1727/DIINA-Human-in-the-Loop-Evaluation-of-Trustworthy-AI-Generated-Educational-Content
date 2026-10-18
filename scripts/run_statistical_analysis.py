#!/usr/bin/env python3
"""
run_statistical_analysis.py
===========================
Standalone statistical analysis script for the DIINA pilot evaluation matrix.

Input
-----
DIINA_Pilot_Evaluation_Matrix.xlsx  (path may be passed as the first CLI
argument; defaults to the script directory / current working directory).

The workbook is expected to contain one sheet where each row is an evaluation
item and columns hold numeric scores from two (or more) raters/systems, e.g.:

    Item | Human_Expert | DIINA_v1 | DIINA_v2 | ...

If the workbook contains multiple such sheets, the first parseable one is used.

Analyses performed
------------------
1. Descriptive statistics (n, mean, SD, min, max, median) per rater.
2. Paired t-tests between every rater pair (two-sided).
3. Cohen's d_z for paired differences (mean(diff) / SD(diff)).
4. Win rates: proportion of items where one rater scores higher than another
   (ties counted and reported separately).
5. ICC(2,1) -- two-way random effects, single measurement, absolute agreement --
   computed manually, with an exact F-based 95% confidence interval.

Outputs
-------
* Clean terminal report.
* `statistical_analysis_summary.txt` written next to the input file.

Dependencies: numpy, pandas, scipy, openpyxl  (see requirements.txt)
Usage       : python run_statistical_analysis.py [path/to/matrix.xlsx]
"""

from __future__ import annotations

import os
import sys
from itertools import combinations
from typing import List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from scipy import stats

DEFAULT_FILENAME = "DIINA_Pilot_Evaluation_Matrix.xlsx"
ALPHA = 0.05
MIN_NUMERIC_COLS = 2   # need at least two raters
MIN_ROWS = 3           # need at least 3 items for meaningful tests


# --------------------------------------------------------------------------- #
# Data loading                                                                #
# --------------------------------------------------------------------------- #
def load_matrix(path: str) -> Tuple[pd.DataFrame, str]:
    """Load the evaluation matrix, returning (numeric_frame, sheet_name)."""
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Input workbook not found: {path}")

    xls = pd.ExcelFile(path, engine="openpyxl")
    best: Optional[Tuple[pd.DataFrame, str]] = None
    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet)
        df = df.dropna(axis=1, how="all").dropna(axis=0, how="all")
        if df.shape[0] == 0:
            continue
        # First row might be a title; try to detect a header with >=2 numeric cols
        num = df.select_dtypes(include=[np.number])
        if num.shape[1] >= MIN_NUMERIC_COLS and num.shape[0] >= MIN_ROWS:
            best = (num, sheet)
            break
    if best is None:
        raise ValueError(
            "No sheet found with at least "
            f"{MIN_NUMERIC_COLS} numeric columns and {MIN_ROWS} rows."
        )
    return best


# --------------------------------------------------------------------------- #
# Statistics                                                                  #
# --------------------------------------------------------------------------- #
def descriptive_stats(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "n": df.count(),
        "Mean": df.mean(),
        "SD": df.std(ddof=1),
        "Min": df.min(),
        "Median": df.median(),
        "Max": df.max(),
    }).round(4)


def paired_tests(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    cols = list(df.columns)
    for a, b in combinations(cols, 2):
        x, y = df[a].astype(float), df[b].astype(float)
        ok = x.notna() & y.notna()
        x, y = x[ok].values, y[ok].values
        n = len(x)
        diff = x - y
        mean_d = diff.mean() if n else np.nan
        sd_d = diff.std(ddof=1) if n > 1 else np.nan
        dz = mean_d / sd_d if (n > 1 and sd_d and not np.isnan(sd_d) and sd_d != 0) else np.nan
        if n > 1 and np.allclose(diff, 0):
            t, p = np.nan, np.nan
        else:
            t, p = stats.ttest_rel(x, y) if n > 1 else (np.nan, np.nan)
        rows.append({
            "Rater A": a, "Rater B": b, "n": n,
            "Mean diff (A-B)": round(mean_d, 4) if n else np.nan,
            "SD diff": round(sd_d, 4) if n > 1 else np.nan,
            "t": round(t, 4) if not np.isnan(t) else np.nan,
            "p (2-sided)": round(p, 5) if p is not None and not np.isnan(p) else np.nan,
            "Cohen's d_z": round(dz, 4) if not np.isnan(dz) else np.nan,
            "Sig. (α=0.05)": "Yes" if (p is not None and not np.isnan(p) and p < ALPHA) else "No",
        })
    return pd.DataFrame(rows)


def win_rates(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for a, b in combinations(list(df.columns), 2):
        x, y = df[a].astype(float), df[b].astype(float)
        ok = x.notna() & y.notna()
        x, y = x[ok].values, y[ok].values
        n = len(x)
        wins_a = int(np.sum(x > y))
        wins_b = int(np.sum(y > x))
        ties = n - wins_a - wins_b
        rows.append({
            "Rater A": a, "Rater B": b, "n pairs": n,
            f"A wins": wins_a, f"B wins": wins_b, "Ties": ties,
            "A win rate": round(wins_a / n, 4) if n else np.nan,
            "B win rate": round(wins_b / n, 4) if n else np.nan,
        })
    return pd.DataFrame(rows)


def icc_2_1(df: pd.DataFrame) -> dict:
    """
    ICC(2,1): two-way random effects, single measurement, absolute agreement.

    Point estimate:
        ICC = (MSR - MSE) / (MSR + (k-1)*MSE + k*(MSC - MSE)/n)
    Exact F-based 95% CI (McGraw & Wong, 1996; Shrout & Fleiss, 1979).
    """
    data = df.dropna().astype(float)
    n, k = data.shape
    if n < 3 or k < 2:
        return {"ICC(2,1)": np.nan, "note": "insufficient data"}

    grand = data.values.mean()
    row_means = data.mean(axis=1).values
    col_means = data.mean(axis=0).values

    SST = ((data.values - grand) ** 2).sum()
    SSR = k * ((row_means - grand) ** 2).sum()          # rows (targets)
    SSC = n * ((col_means - grand) ** 2).sum()          # columns (raters)
    SSE = SST - SSR - SSC

    MSR = SSR / (n - 1)
    MSC = SSC / (k - 1)
    MSE = SSE / ((n - 1) * (k - 1))

    denom = MSR + (k - 1) * MSE + k * (MSC - MSE) / n
    icc = (MSR - MSE) / denom if denom != 0 else np.nan

    # Exact F confidence intervals
    f1 = MSR / MSE if MSE > 0 else np.inf               # F for rows
    f2 = MSC / MSE if MSE > 0 else np.inf               # F for columns
    nu_n, nu_k, nu_e = n - 1, k - 1, (n - 1) * (k - 1)

    fl = stats.f.ppf(1 - ALPHA / 2, nu_n, nu_e)          # lower F crit
    fu = stats.f.ppf(ALPHA / 2, nu_n, nu_e)              # = 1/F upper crit

    def ci_single(fl_: float, fu_: float) -> Tuple[float, float]:
        a = fl_ * MSR
        b = (k - 1) * MSE + k * (MSC - MSE) / n
        c = fu_ * MSR
        lower = (a - b) / (a + (k - 1) * b) if (a + (k - 1) * b) != 0 else np.nan
        upper = (c - b) / (c + (k - 1) * b) if (c + (k - 1) * b) != 0 else np.nan
        return float(np.clip(lower, -1, 1)), float(np.clip(upper, -1, 1))

    lo, hi = ci_single(fl, fu)

    return {
        "ICC(2,1)": round(float(icc), 4),
        "95% CI": (round(lo, 4), round(hi, 4)),
        "n targets": n,
        "k raters": k,
        "MSR": round(MSR, 4), "MSC": round(MSC, 4), "MSE": round(MSE, 4),
    }


# --------------------------------------------------------------------------- #
# Reporting                                                                   #
# --------------------------------------------------------------------------- #
def _df_to_text(df: pd.DataFrame, title: str) -> str:
    lines = [title, "-" * len(title)]
    lines.append(df.to_string(index=descriptive_ok(df)))
    lines.append("")
    return "\n".join(lines)


def descriptive_ok(df: pd.DataFrame) -> bool:
    # For descriptive stats keep the index (rater names); for others hide it.
    return df.index.name is not None or "Mean" in df.columns


def build_report(df: pd.DataFrame, path: str) -> str:
    desc = descriptive_stats(df)
    ptests = paired_tests(df)
    wins = win_rates(df)
    icc = icc_2_1(df)

    parts: List[str] = []
    parts.append("=" * 72)
    parts.append("DIINA Pilot Evaluation — Statistical Analysis Report")
    parts.append("=" * 72)
    parts.append(f"Input file : {os.path.abspath(path)}")
    parts.append(f"Items (n)  : {df.shape[0]}    Raters (k) : {df.shape[1]}")
    parts.append("")

    parts.append("1. DESCRIPTIVE STATISTICS")
    parts.append(desc.to_string())
    parts.append("")

    parts.append("2. PAIRED T-TESTS & COHEN'S d_z")
    parts.append(ptests.to_string(index=False))
    parts.append("")

    parts.append("3. WIN RATES")
    parts.append(wins.to_string(index=False))
    parts.append("")

    parts.append("4. INTER-RATER RELIABILITY — ICC(2,1)")
    parts.append(f"  ICC(2,1) = {icc.get('ICC(2,1)')}")
    if "95% CI" in icc:
        lo, hi = icc["95% CI"]
        parts.append(f"  95% CI   = [{lo}, {hi}]  (exact F-based)")
    parts.append(f"  targets n = {icc.get('n targets')}, raters k = {icc.get('k raters')}")
    parts.append("")
    parts.append("Notes: d_z = mean(pairwise diff) / SD(pairwise diff);")
    parts.append("       ICC(2,1) = two-way random, single measure, absolute agreement.")
    parts.append("=" * 72)
    return "\n".join(parts)


def main(argv: Optional[Sequence[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    path = argv[0] if argv else os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                             DEFAULT_FILENAME)
    if not os.path.isfile(path):
        # fallback: current working directory
        alt = os.path.join(os.getcwd(), DEFAULT_FILENAME)
        if os.path.isfile(alt):
            path = alt
        else:
            print(f"ERROR: input workbook not found: {path}", file=sys.stderr)
            return 2

    df, sheet = load_matrix(path)
    print(f"[load] sheet '{sheet}': {df.shape[0]} items x {df.shape[1]} raters "
          f"({list(df.columns)})")

    report = build_report(df, path)
    print(report)

    out_path = os.path.join(os.path.dirname(os.path.abspath(path)),
                            "statistical_analysis_summary.txt")
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(report + "\n")
    print(f"[done] summary written to: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
