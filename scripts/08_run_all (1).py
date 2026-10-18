#!/usr/bin/env python3
"""Step 08: Run the full DIINA reproducible analysis pipeline."""
import os, sys, subprocess, time

HERE=os.path.dirname(os.path.abspath(__file__))
STEPS=["03_descriptive_statistics.py","04_inter_rater_agreement.py",
       "05_condition_comparison.py","06_cluster_analysis.py","07_generate_tables.py"]

def main():
    start=time.time()
    for s in STEPS:
        print(f"\n===== Running {s} =====")
        r=subprocess.run([sys.executable,os.path.join(HERE,s)],cwd=HERE)
        if r.returncode!=0:
            print(f"FAILED: {s} (exit {r.returncode})"); sys.exit(r.returncode)
    print(f"\nAll steps completed in {time.time()-start:.1f}s. Outputs in {os.path.join(HERE,'outputs')}")

if __name__=="__main__":
    main()
