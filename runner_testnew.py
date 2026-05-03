import os
import glob
from baseline import prove as baseline_prove
from improved import prove as improved_prove
from runner import run_benchmark

BASE = os.path.dirname(os.path.abspath(__file__))

# collect all problems from both folders
all_files = sorted(
    glob.glob(os.path.join(BASE, 'benchmarks', 'SYN', '*+*.p')) +
    glob.glob(os.path.join(BASE, 'benchmarks', 'GEN', '*+*.p'))
)

print(f"Total problems found: {len(all_files)}")