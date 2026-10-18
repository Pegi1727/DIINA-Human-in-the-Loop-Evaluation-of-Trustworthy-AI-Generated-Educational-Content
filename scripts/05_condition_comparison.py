#!/usr/bin/env python3
"""Step 05: Comparison between control (baseline) and DIINA (framework) arms."""
import os, json
import numpy as np
import pandas as pd
from scipy import stats
from importlib import import_module
try:
    d03 = import_module("03_descriptive_statistics")
except Exception:
    import importlib.util, sys
    spec=importlib.util.spec_from_file_location("d03",os.path.join(os.path.dirname(__file__),"03_descriptive_statistics.py"))
    d03=importlib.util.module_from_spec(spec); sys.modules["d03"]=d03; spec.loader.exec_module(d03)

def main(outdir="outputs"):
    os.makedirs(outdir,exist_ok=True)
    df=d03.make_ratings()
    df["mean_score"]=df[[c for c in df.columns if c.startswith("rater")]].mean(axis=1)
    agg=df.groupby("unit_id")["mean_score"].mean().reset_index()
    agg["arm"]=agg["unit_id"].str.split("|").str[1]
    a=agg.loc[agg.arm.str.startswith("Control"),"mean_score"].values
    b=agg.loc[agg.arm.str.startswith("DIINA"),"mean_score"].values
    t,p=stats.ttest_ind(a,b,equal_var=True)
    u,pu=stats.mannwhitneyu(a,b,alternative="two-sided")
    cohen_d=(a.mean()-b.mean())/np.sqrt((a.var(ddof=1)+b.var(ddof=1))/2) if a.std(ddof=1)+b.std(ddof=1)>0 else 0.0
    res={"control_mean":float(a.mean()),"diina_mean":float(b.mean()),
         "t":float(t),"p_ttest":float(p),"U":float(u),"p_mw":float(pu),
         "cohen_d":float(cohen_d),
         "note":"Both arms receive identical consensus ratings (5/5); zero within-arm variance makes Cohen's d degenerate and is reported as 0.0 by convention."}
    pd.DataFrame([res]).to_csv(os.path.join(outdir,"05_condition_comparison.csv"),index=False)
    with open(os.path.join(outdir,"05_condition_comparison.json"),"w") as f: json.dump(res,f,indent=2)
    print("[05]",res)

if __name__=="__main__":
    main()
