import os
import glob
from parser import parse_file

BASE = os.path.dirname(os.path.abspath(__file__))
files = sorted(glob.glob(os.path.join(BASE, 'benchmarks', 'GEN', '*.p')))[:20]

errors = 0
for f in files:
    problem = parse_file(f)
    if problem is None:
        errors += 1
        print(f'FAILED: {os.path.basename(f)}')
    else:
        print(f'OK: {os.path.basename(f)} — status={problem.status}')

print(f'\nErrors: {errors}/20')