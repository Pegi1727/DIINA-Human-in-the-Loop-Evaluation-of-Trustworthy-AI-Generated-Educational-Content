#!/usr/bin/env python3
"""
01_validate_data.py
-------------------
Validate the structure of the blinded DIINA pilot evaluation data:
record counts, identifiers, missing values, and rating ranges.

Exit codes: 0 = all checks passed, 1 = validation failures found.
"""
import os
import sys

import pandas as pd
import yaml

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.yaml")


def load_config(path: str = CONFIG_PATH) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_blinded_data(cfg: dict) -> pd.DataFrame:
    """Load the blinded evaluation sheet with its true header row (row 2)."""
    df = pd.read_excel(
        cfg["paths"]["evaluation_matrix"],
        sheet_name=cfg["paths"]["evaluation_sheet"],
        header=1,
    )
    return df


def validate(df: pd.DataFrame, cfg: dict) -> list:
    """Return a list of validation-failure messages (empty list = valid)."""
    problems = []
    eval_cfg = cfg["evaluation"]
    dims = eval_cfg["composite_dimensions"] + [eval_cfg["provenance_dimension"]]

    # Required columns
    required = ["Evaluation ID", "Case ID", "Blinded Code", "Evaluator ID"] + dims
    for col in required:
        if col not in df.columns:
            problems.append(f"Missing required column: {col!r}")
    if problems:
        return problems

    # Record count
    expected = eval_cfg["expected_records"]
    if len(df) != expected:
        problems.append(f"Expected {expected} records, found {len(df)}.")

    # Unique identifiers
    if df["Evaluation ID"].duplicated().any():
        problems.append("Duplicate Evaluation ID values found.")
    if df["Blinded Code"].duplicated().any():
        problems.append("Duplicate Blinded Code values found.")

    # Case-arm structure
    n_units = df["Blinded Code"].nunique()
    expected_units = eval_cfg["expected_cases"] * eval_cfg["expected_arms"]
    if n_units != expected_units:
        problems.append(
            f"Expected {expected_units} case-arm units, found {n_units}."
        )

    # Evaluators
    raters = sorted(df["Evaluator ID"].dropna().unique())
    if raters != sorted(eval_cfg["evaluators"]):
        problems.append(f"Unexpected evaluator set: {raters}")
    counts = df["Evaluator ID"].value_counts()
    for rater in eval_cfg["evaluators"]:
        if counts.get(rater, 0) != expected_units:
            problems.append(
                f"{rater} rated {counts.get(rater, 0)} units, "
                f"expected {expected_units}."
            )

    # Missing values in identifiers and rating columns
    for col in ["Evaluation ID", "Case ID", "Blinded Code", "Evaluator ID"] + dims:
        n_missing = df[col].isna().sum()
        if n_missing:
            problems.append(f"Column {col!r} has {n_missing} missing value(s).")

    # Rating ranges
    lo, hi = eval_cfg["scale_min"], eval_cfg["scale_max"]
    for col in dims:
        vals = pd.to_numeric(df[col], errors="coerce")
        out_of_range = ((vals < lo) | (vals > hi)).sum()
        if out_of_range:
            problems.append(
                f"Column {col!r} has {out_of_range} value(s) outside [{lo},{hi}]."
            )

    return problems


def main() -> int:
    cfg = load_config()
    print("=== 01_validate_data ===")
    try:
        df = load_blinded_data(cfg)
    except Exception as exc:  # pragma: no cover
        print(f"[FAIL] Could not load data: {exc}")
        return 1
    print(f"Loaded {len(df)} records x {df.shape[1]} columns "
          f"from {os.path.basename(cfg['paths']['evaluation_matrix'])} "
          f"({cfg['paths']['evaluation_sheet']}).")
    print(f"Missing values per column (rating/id columns only):\n"
          f"{df[[c for c in df.columns if c.startswith('Dim') or 'ID' in c or 'Code' in c]].isna().sum().to_string()}")

    problems = validate(df, cfg)
    if problems:
        for p in problems:
            print(f"[PROBLEM] {p}")
        print("Validation FAILED.")
        return 1
    print("All validation checks passed: 80 records, 40 case-arm units, "
          "2 evaluators, ratings within [1, 5], no missing identifiers.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
