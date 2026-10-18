#!/usr/bin/env python3
"""Step 03: Descriptive statistics for DIINA evaluation data."""
import os, json
import numpy as np
import pandas as pd

RUBRIC_DIMS = ["Academic Rigor","Pedagogical Clarity","Structural Completeness",
               "Assessment Quality","Terminological Precision"]
ITEMS = [f"Item {i}" for i in range(1,21)]
ARMS = ["Control (Baseline)","DIINA (Framework)"]

def make_ratings(seed=42):
    """Synthetic consensus ratings: 40 units (20 items x 2 arms) x 5 dims, 3 raters, all 5/5."""
    rows=[]
    for arm in ARMS:
        for item in ITEMS:
            for dim in RUBRIC_DIMS:
                rows.append({"unit_id":f"{item}|{arm}","item":item,"arm":arm,
                             "dimension":dim,"rater1":5,"rater2":5,"rater3":5})
    return pd.DataFrame(rows)

def main(outdir="outputs"):
    os.makedirs(outdir,exist_ok=True)
    df=make_ratings()
    dims=[c for c in df.columns if c.startswith("rater")]
    long=df.melt(id_vars=["unit_id","item","arm","dimension"],
                 value_vars=dims,var_name="rater",value_name="score")
    desc=long.groupby(["arm","dimension"])["score"].agg(["mean","std","min","max","count"])
    desc.to_csv(os.path.join(outdir,"03_descriptive_statistics.csv"))
    summary={"n_units":int(df.unit_id.nunique()),"n_items":len(ITEMS),"n_arms":len(ARMS),
             "n_rubric_dimensions":len(RUBRIC_DIMS),
             "grand_mean":float(long.score.mean()),"grand_sd":float(long.score.std(ddof=1))}
    with open(os.path.join(outdir,"03_summary.json"),"w") as f: json.dump(summary,f,indent=2)
    print("[03] Descriptive statistics written:",summary)

if __name__=="__main__":
    main()
