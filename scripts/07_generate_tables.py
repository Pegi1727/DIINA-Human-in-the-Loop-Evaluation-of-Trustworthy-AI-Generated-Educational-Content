#!/usr/bin/env python3
"""Step 07: Assemble publication-style tables from all previous step outputs."""
import os, json, csv
import pandas as pd

def main(outdir="outputs"):
    os.makedirs(outdir,exist_ok=True)
    tables=[]
    desc_path=os.path.join(outdir,"03_descriptive_statistics.csv")
    if os.path.exists(desc_path):
        t=pd.read_csv(desc_path); t.to_latex(os.path.join(outdir,"Table1_descriptive.tex"),index=False)
        tables.append("Table1_descriptive.tex")
    for src,dst in [("04_inter_rater_agreement.json","Table2_inter_rater_agreement.txt"),
                    ("05_condition_comparison.json","Table3_condition_comparison.txt"),
                    ("06_cluster_summary.json","Table4_cluster_summary.txt")]:
        p=os.path.join(outdir,src)
        if os.path.exists(p):
            with open(p) as f: data=json.load(f)
            with open(os.path.join(outdir,dst),"w") as f:
                for key,val in data.items(): f.write(f"{key}: {val}\n")
            tables.append(dst)
    with open(os.path.join(outdir,"07_tables_manifest.txt"),"w") as f:
        f.write("\n".join(tables))
    print("[07] Tables generated:",tables)

if __name__=="__main__":
    main()
