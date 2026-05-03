# main.py
#
# Entry point for the theorem prover benchmark evaluation.
# Runs both the baseline and improved algorithms against all benchmark
# problems and produces a console report and CSV output.
#
# Usage:
#   python main.py
#
# Settings are configured in the CONFIGURATION section below.
# Change DEPTH_LIMIT and TIME_LIMIT_S before the final data collection run.

import os
import glob
import time
import datetime

# ─────────────────────────────────────────
# CONFIGURATION
# Change these before the final data collection run
# ─────────────────────────────────────────

DEPTH_LIMIT  = 500         # max rule applications per problem (use 500 for final run)
TIME_LIMIT_S = 10.0        # max seconds per problem per algorithm (use 10.0 for final run)
OUTPUT_CSV   = 'results/results.csv'

BENCHMARK_FOLDERS = [
    'benchmarks/SYN',
    'benchmarks/GEN',
]


# ─────────────────────────────────────────
# IMPORTS
# ─────────────────────────────────────────

from baseline import prove as baseline_prove
from improved import prove as improved_prove
from runner   import run_benchmark


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────

def main():

    # ── resolve paths relative to this file ───
    base = os.path.dirname(os.path.abspath(__file__))

    benchmark_folders = [
        os.path.join(base, folder)
        for folder in BENCHMARK_FOLDERS
    ]
    output_csv = os.path.join(base, OUTPUT_CSV)

    # ── collect all problem files ──────────────
    all_files = []
    for folder in benchmark_folders:
        pattern = os.path.join(folder, '*+*.p')
        found   = sorted(glob.glob(pattern))
        all_files.extend(found)

    # ── print run header ───────────────────────
    run_start = time.perf_counter()
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    width = 62
    print('=' * width)
    print('  THEOREM PROVER — BENCHMARK EVALUATION')
    print('=' * width)
    print(f'  Started          : {timestamp}')
    print(f'  Depth limit      : {DEPTH_LIMIT} steps')
    print(f'  Time limit       : {TIME_LIMIT_S}s per problem per algorithm')
    print(f'  Benchmark folders: {len(benchmark_folders)}')
    for folder in benchmark_folders:
        count   = len(sorted(glob.glob(os.path.join(folder, '*+*.p'))))
        name    = os.path.basename(folder)
        print(f'    {name:<10}: {count} problems')
    print(f'  Total problems   : {len(all_files)}')
    print(f'  Output CSV       : {output_csv}')
    print('=' * width)
    print()

    # ── run benchmark across all folders ───────
    # runner.run_benchmark scans one folder at a time
    # we combine results from all folders manually

    from parser import parse_file
    from runner import run_one, compute_verdict, print_summary, write_csv, CSV_FIELDS

    rows         = []
    parse_errors = []

    for i, filepath in enumerate(all_files, 1):
        filename = os.path.basename(filepath)
        folder   = os.path.basename(os.path.dirname(filepath))

        # ── parse ──────────────────────────
        problem = parse_file(filepath)

        if problem is None:
            parse_errors.append((filepath, 'no conjecture or parse error'))
            print(f'  [{i:5d}] {folder}/{filename:30s} SKIPPED')
            continue

        # ── run baseline ───────────────────
        b_result, b_time = run_one(
            problem.formula, baseline_prove, DEPTH_LIMIT, TIME_LIMIT_S
        )
        b_verdict = compute_verdict(b_result.status, problem.expected)

        # ── run improved ───────────────────
        i_result, i_time = run_one(
            problem.formula, improved_prove, DEPTH_LIMIT, TIME_LIMIT_S
        )
        i_verdict = compute_verdict(i_result.status, problem.expected)

        # ── store row ──────────────────────
        row = {
            'filename':         f'{folder}/{filename}',
            'expected_status':  problem.expected or 'unknown',
            'baseline_result':  b_result.status,
            'baseline_steps':   b_result.steps,
            'baseline_time_ms': round(b_time, 3),
            'baseline_verdict': b_verdict,
            'improved_result':  i_result.status,
            'improved_steps':   i_result.steps,
            'improved_time_ms': round(i_time, 3),
            'improved_verdict': i_verdict,
        }
        rows.append(row)

        print(f'  [{i:5d}] {folder}/{filename:30s} '
              f'B={b_result.status:8s}'
              f'({b_result.steps:4d} steps, {b_time:8.1f}ms)  '
              f'I={i_result.status:8s}'
              f'({i_result.steps:4d} steps, {i_time:8.1f}ms)')

    # ── wall clock time ────────────────────────
    total_elapsed = time.perf_counter() - run_start

    # ── print summary and error report ─────────
    print()
    print_summary(rows, parse_errors, 'Baseline (Algorithm 2)', 'Improved')

    # ── write CSV ──────────────────────────────
    write_csv(rows, output_csv)

    # ── print total run time ───────────────────
    mins, secs = divmod(int(total_elapsed), 60)
    print(f'\n  Total wall clock time: {mins}m {secs}s')
    print('=' * width)


if __name__ == '__main__':
    main()