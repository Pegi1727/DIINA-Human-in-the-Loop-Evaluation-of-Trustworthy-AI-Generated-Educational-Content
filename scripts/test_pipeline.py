#!/usr/bin/env python3
"""Pytest verification suite for the DIINA reproducible pipeline."""
import os, sys, json, subprocess, importlib.util
import numpy as np

HERE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,HERE)

def load(name):
    spec=importlib.util.spec_from_file_location(name,os.path.join(HERE,name+".py"))
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def test_descriptive_shape():
    d03=load("03_descriptive_statistics")
    df=d03.make_ratings()
    assert df.unit_id.nunique()==40 and len(df)==40*5

def test_unanimous_agreement():
    d04=load("04_inter_rater_agreement")
    X=d04.build_matrix()
    assert (X.std(axis=1,ddof=1)==0).all(), "All ratings must be unanimous"

def test_icc_and_ms():
    d04=load("04_inter_rater_agreement")
    X=d04.build_matrix()
    icc,_,MS_rater,MS_error=d04.icc_2_1(X)
    assert round(float(icc),3)==1.000
    assert MS_error==0 and MS_rater==0

def test_ci_degenerate_documented(tmp_path):
    d04=load("04_inter_rater_agreement")
    res=d04.main(outdir=str(tmp_path))
    assert res["confidence_interval"]["status"].startswith("OMITTED")
    assert "indeterminate" in res["confidence_interval"]["reason"]
    assert "must NOT be interpreted" in res["methodological_caveat"]

def test_run_all_exit_code():
    r=subprocess.run([sys.executable,os.path.join(HERE,"08_run_all.py")],
                     cwd=HERE,capture_output=True,text=True)
    assert r.returncode==0, r.stderr
    out=os.path.join(HERE,"outputs","04_inter_rater_agreement.json")
    with open(out) as f: res=json.load(f)
    assert res["ICC_2_1"]==1.000 and res["n_evaluation_units"]==40
