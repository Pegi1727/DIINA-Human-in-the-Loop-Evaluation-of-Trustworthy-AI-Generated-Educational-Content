#!/usr/bin/env python3
"""
02_prepare_analysis_data.py
---------------------------
Build a tidy analysis dataset from the raw blinded evaluation matrix.
The original file is never modified; a derived tidy CSV is written to
outputs/analysis_data.csv.

Output columns:
  Item_ID, Condition (DIINA/Baseline from blinding mapping),
  Evaluator, Dim1..Dim5, Composite (mean of Dims 1-4)
"""
import os
import sys

import numpy as np
import pandas as pd
import yaml

sys.path.insert(0, os.path.dirname(__file__))
from importlib import import_module
_01 = import_module("01_validate_data")

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.yaml")


def build_analysis_data(cfg: dict) -> pd.DataFrame:
    raw = _01.load_blinded_data(cfg)
    dims = cfg["evaluation"]["composite_dimensions"]
    dim5 = cfg["evaluation"]["provenance_dimension"]
    composite_cols = [f"Dim{i}" for i in range(1, 5)]

    df = raw.rename(columns={
        dims[0]: "Dim1", dims[1]: "Dim2", dims[2]: "Dim3",
        dims[3]: "Dim4", dim5: "Dim5",
        "Blinded Code": "Blinded_Code",
        "Evaluator ID": "Evaluator",
        "Case ID": "Case_ID",
    })

    # Condition is derived from the blinded arm suffix (_A vs _B).
    # The master key (unblinded) maps Arm A -> DIINA, Arm B -> Baseline.
    arm = df["Blinded_Code"].str.extract(r"_([AB])$")[0]
    df["Condition"] = arm.map({"A": "DIINA", "B": "Baseline"})
    if df["Condition"].isna().any():
        raise ValueError("Unrecognized blinded-code arm suffix.")

    df["Composite"] = df[composite_cols].mean(axis=1)

    cols = ["Case_ID", "Blinded_Code", "Condition", "Evaluator"] + \
           composite_cols + ["Dim5", "Composite"]
    out = df[cols].sort_values(
        ["Case_ID", "Condition", "Evaluator"]).reset_index(drop=True)
    return out


def main() -> int:
    cfg = _01.load_config() if "cfg" not in dir() else cfg
    cfg = _01.load_config(CONFIG_PATH)
    print("=== 02_prepare_analysis_data ===")
    tidy = build_analysis_data(cfg)
    out_path = cfg["paths"]["analysis_data"]
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    tidy.to_csv(out_path, index=False)
    print(f"Wrote {len(tidy)} tidy records to {out_path}")
    print(f"Conditions: {tidy['Condition'].value_counts().to_dict()}")
    print(f"Evaluators: {tidy['Evaluator'].value_counts().to_dict()}")
    print(f"Composite mean by condition:\n"
          f"{tidy.groupby('Condition')['Composite'].mean().to_string()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
