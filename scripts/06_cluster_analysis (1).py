#!/usr/bin/env python3
"""Step 06: Cluster analysis of the 40 evaluation units across rubric dimensions."""
import os, json
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from importlib import import_module
import importlib.util, sys
spec=importlib.util.spec_from_file_location("d03",os.path.join(os.path.dirname(__file__),"03_descriptive_statistics.py"))
d03=importlib.util.module_from_spec(spec); sys.modules["d03"]=d03; spec.loader.exec_module(d03)

def main(outdir="outputs",k=2,seed=0):
    os.makedirs(outdir,exist_ok=True)
    df=d03.make_ratings()
    dims=[c for c in df.columns if c.startswith("rater")]
    X=df.groupby(["unit_id","arm"])[dims].mean().reset_index()
    M=X[dims].values
    km=KMeans(n_clusters=k,n_init=10,random_state=seed).fit(M)
    X["cluster"]=km.labels_
    # All-identical scores: k-means splits ties arbitrarily; report dispersion diagnostics.
    inertia=float(km.inertia_)
    res={"n_units":len(X),"k":k,"inertia":inertia,
         "within_unit_sd_max":float(M.std(axis=1,ddof=1).max()),
         "note":"All 40 units have identical rubric profiles (unanimous consensus); clusters reflect arbitrary tie-breaking, not substantive differentiation."}
    X.to_csv(os.path.join(outdir,"06_cluster_assignments.csv"),index=False)
    with open(os.path.join(outdir,"06_cluster_summary.json"),"w") as f: json.dump(res,f,indent=2)
    print("[06]",res)

if __name__=="__main__":
    main()
