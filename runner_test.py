import os
from baseline import prove
from runner import run_benchmark

BASE = os.path.dirname(os.path.abspath(__file__))

# use baseline as both algorithms for now
# replace second argument with improved.prove once built
run_benchmark(
    benchmark_folder = os.path.join(BASE, 'benchmarks', 'SYN'),
    baseline_fn      = prove,
    improved_fn      = prove,
    depth_limit      = 50,
    time_limit_s     = 5.0,
    output_csv       = os.path.join(BASE, 'results', 'results.csv'),
    verbose          = True
)