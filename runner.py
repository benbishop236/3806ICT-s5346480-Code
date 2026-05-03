# runner.py
import os
import glob
import time
import csv
import signal
from sequent import ProofResult
from typing import Optional

class HardTimeout(Exception):
    """Raised by the OS signal when wall clock time is exceeded."""
    pass

def _timeout_handler(signum, frame):
    raise HardTimeout()

# ─────────────────────────────────────────
# VERDICT LOGIC
# ─────────────────────────────────────────

def compute_verdict(result_status: str, expected: Optional[str]) -> str:
    """
    Compare a prover result against the expected status from the TPTP header.

    Returns one of:
        'correct'    — result matches expected
        'incomplete' — timed out or open when a proof was expected (known limitation)
        'error'      — proved something that should not be provable (soundness bug)
        'unknown'    — no expected status to compare against
    """
    if expected is None:
        return 'unknown'

    if expected == 'proved':
        if result_status == 'proved':
            return 'correct'
        elif result_status in ('timeout', 'open'):
            return 'incomplete'

    elif expected == 'open':
        if result_status in ('open', 'timeout'):
            return 'correct'
        elif result_status == 'proved':
            return 'error'   # soundness violation — serious bug if this appears

    return 'unknown'


# ─────────────────────────────────────────
# SINGLE PROBLEM RUN
# ─────────────────────────────────────────

#def run_one(formula, prove_fn, depth_limit: int = 500, time_limit_s: float = 10.0):
#    """Run a single prover function on a formula.
#    Returns (ProofResult, elapsed_ms)."""
#    start = time.perf_counter()
#    result = prove_fn(formula, depth_limit)
#    elapsed_ms = (time.perf_counter() - start) * 1000
#    return result, elapsed_ms

#New run_one function that includes OS level time out to stop hangtime during a depth search
def run_one(formula, prove_fn, depth_limit: int = 500, time_limit_s: float = 5.0):
    """Run a single prover function on a formula.
    Enforces a hard wall clock time limit using OS signals.
    Returns (ProofResult, elapsed_ms)."""

    # register the OS signal handler
    signal.signal(signal.SIGALRM, _timeout_handler)
    # tell the OS to interrupt after time_limit_s seconds
    signal.alarm(int(time_limit_s))

    start = time.perf_counter()
    try:
        result = prove_fn(formula, depth_limit, time_limit_s)
        signal.alarm(0)   # cancel the alarm — prove finished in time
    except HardTimeout:
        result = ProofResult('timeout', 0, 'hard time limit reached')

    elapsed_ms = (time.perf_counter() - start) * 1000
    return result, elapsed_ms

# ─────────────────────────────────────────
# SUMMARY STATISTICS
# ─────────────────────────────────────────

def compute_summary(rows: list, prefix: str) -> dict:
    """Compute summary statistics for one algorithm across all result rows.
    prefix is either 'baseline' or 'improved'."""
    total      = len(rows)
    proved     = sum(1 for r in rows if r[f'{prefix}_result'] == 'proved')
    open_      = sum(1 for r in rows if r[f'{prefix}_result'] == 'open')
    timeout    = sum(1 for r in rows if r[f'{prefix}_result'] == 'timeout')
    correct    = sum(1 for r in rows if r[f'{prefix}_verdict'] == 'correct')
    incomplete = sum(1 for r in rows if r[f'{prefix}_verdict'] == 'incomplete')
    errors     = sum(1 for r in rows if r[f'{prefix}_verdict'] == 'error')
    unknown    = sum(1 for r in rows if r[f'{prefix}_verdict'] == 'unknown')

    # accuracy only counted over problems where expected is known
    checkable = correct + incomplete + errors
    accuracy  = (correct / checkable * 100) if checkable > 0 else 0.0

    times     = [r[f'{prefix}_time_ms'] for r in rows]
    steps     = [r[f'{prefix}_steps']   for r in rows]
    avg_time  = sum(times) / total if total > 0 else 0.0
    avg_steps = sum(steps) / total if total > 0 else 0.0

    return {
        'total':      total,
        'proved':     proved,
        'open':       open_,
        'timeout':    timeout,
        'correct':    correct,
        'incomplete': incomplete,
        'errors':     errors,
        'unknown':    unknown,
        'accuracy':   accuracy,
        'avg_time':   avg_time,
        'avg_steps':  avg_steps,
    }


# ─────────────────────────────────────────
# PRINT SUMMARY REPORT TO CONSOLE
# ─────────────────────────────────────────

def print_summary(rows: list, parse_errors: list,
                  label_a: str = 'Baseline',
                  label_b: str = 'Improved'):
    """Print the full benchmark summary report to console."""
    s_a = compute_summary(rows, 'baseline')
    s_b = compute_summary(rows, 'improved')
    w   = 62   # report width

    print('=' * w)
    print(f'  THEOREM PROVER BENCHMARK REPORT')
    print(f'  Problems attempted : {s_a["total"]}')
    print(f'  Parse errors       : {len(parse_errors)}')
    print('=' * w)

    for label, s in [(label_a, s_a), (label_b, s_b)]:
        print(f'\n  {label}')
        print(f'  {"─" * (w - 4)}')
        print(f'  Proved             : {s["proved"]}')
        print(f'  Open               : {s["open"]}')
        print(f'  Timeout            : {s["timeout"]}')
        print(f'  Correct            : {s["correct"]}')
        print(f'  Incomplete         : {s["incomplete"]}')
        print(f'  Errors (soundness) : {s["errors"]}')
        print(f'  Unknown            : {s["unknown"]}')
        print(f'  Accuracy           : {s["accuracy"]:.1f}%')
        print(f'  Avg time (ms)      : {s["avg_time"]:.2f}')
        print(f'  Avg steps          : {s["avg_steps"]:.1f}')

    # ── comparison section ─────────────────
    print(f'\n  COMPARISON')
    print(f'  {"─" * (w - 4)}')

    wins = [r for r in rows
            if r['improved_result'] == 'proved'
            and r['baseline_result'] in ('timeout', 'open')]

    regressions = [r for r in rows
                   if r['baseline_result'] == 'proved'
                   and r['improved_result'] in ('timeout', 'open')]

    print(f'  Improved solved, baseline failed  : {len(wins)}')
    print(f'  Baseline solved, improved failed  : {len(regressions)}')

    # speedup on problems both algorithms proved
    both_proved = [r for r in rows
                   if r['baseline_result'] == 'proved'
                   and r['improved_result'] == 'proved'
                   and r['improved_time_ms'] > 0]
    if both_proved:
        ratios      = [r['baseline_time_ms'] / r['improved_time_ms']
                       for r in both_proved]
        avg_speedup = sum(ratios) / len(ratios)
        print(f'  Avg speedup (time) on shared wins : {avg_speedup:.2f}x')
    else:
        print(f'  Avg speedup (time) on shared wins : N/A')

    # ── error report ───────────────────────
    all_errors = [r for r in rows
                  if r['baseline_verdict'] == 'error'
                  or r['improved_verdict'] == 'error']

    print(f'\n  ERROR REPORT')
    print(f'  {"─" * (w - 4)}')
    if not all_errors and not parse_errors:
        print(f'  No errors detected.')
    else:
        for r in all_errors:
            print(f'  [SOUNDNESS]  {r["filename"]} '
                  f'baseline={r["baseline_verdict"]} '
                  f'improved={r["improved_verdict"]}')
        for filepath, reason in parse_errors:
            print(f'  [PARSE ERR]  {os.path.basename(filepath)}: {reason}')

    print('=' * w)


# ─────────────────────────────────────────
# CSV OUTPUT
# ─────────────────────────────────────────

CSV_FIELDS = [
    'filename',
    'expected_status',
    'baseline_result', 'baseline_steps', 'baseline_time_ms', 'baseline_verdict',
    'improved_result', 'improved_steps', 'improved_time_ms', 'improved_verdict',
]

def write_csv(rows: list, output_path: str):
    """Write all result rows to a CSV file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row[k] for k in CSV_FIELDS})
    print(f'\n  Results written to: {output_path}')


# ─────────────────────────────────────────
# MAIN RUNNER
# ─────────────────────────────────────────

def run_benchmark(
        benchmark_folder: str,
        baseline_fn,
        improved_fn,
        depth_limit: int  = 500,
        time_limit_s: float = 10.0,
        output_csv:  str  = 'results/results.csv',
        verbose:     bool = True
) -> list:
    """
    Run both provers against all FOF .p files in benchmark_folder.

    Parameters:
        benchmark_folder : path to folder containing *+*.p files
        baseline_fn      : the baseline prove() function
        improved_fn      : the improved prove() function
        depth_limit      : max rule applications before timeout
        output_csv       : path to write the CSV results file
        verbose          : if True, print one line per problem as it runs

    Returns:
        list of result row dicts (same data as written to CSV)
    """
    from parser import parse_file

    # ── find all FOF problems ──────────────
    pattern   = os.path.join(benchmark_folder, '*+*.p')
    filepaths = sorted(glob.glob(pattern))

    if not filepaths:
        print(f'No .p files found in {benchmark_folder}')
        return []

    print(f'Found {len(filepaths)} problems in {benchmark_folder}')
    print(f'Running with depth limit {depth_limit}\n')

    rows         = []
    parse_errors = []

    for i, filepath in enumerate(filepaths, 1):
        filename = os.path.basename(filepath)

        # ── parse ──────────────────────────
       #print(f'  [{i:4d}] parsing {filename}...', flush=True) Debug line
        problem = parse_file(filepath)
        #print(f'  [{i:4d}] parsed  {filename}', flush=True) Debug line

        if problem is None:
            parse_errors.append((filepath, 'no conjecture or parse error'))
            if verbose:
                print(f'  [{i:4d}] {filename:30s} SKIPPED')
            continue

        # ── run baseline ───────────────────
        b_result, b_time = run_one(problem.formula, baseline_fn, depth_limit, time_limit_s)
        b_verdict        = compute_verdict(b_result.status, problem.expected)

        # ── run improved ───────────────────
        i_result, i_time = run_one(problem.formula, improved_fn, depth_limit, time_limit_s)
        i_verdict        = compute_verdict(i_result.status, problem.expected)

        # ── store row ──────────────────────
        row = {
            'filename':         filename,
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

        if verbose:
            print(f'  [{i:4d}] {filename:30s} '
                  f'B={b_result.status:8s}'
                  f'({b_result.steps:4d} steps, {b_time:7.1f}ms)  '
                  f'I={i_result.status:8s}'
                  f'({i_result.steps:4d} steps, {i_time:7.1f}ms)')

    # ── print summary and write CSV ────────
    print()
    print_summary(rows, parse_errors)
    write_csv(rows, output_csv)

    return rows