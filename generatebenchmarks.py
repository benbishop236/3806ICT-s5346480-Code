# generate_benchmarks.py
#
# Generates synthetic TPTP FOF benchmark problems at three difficulty levels.
# Problems are built from known logical tautologies and theorems parameterised
# over different predicate and variable names to produce many distinct problems.
#
# Usage:
#   python generate_benchmarks.py [output_folder]
#
# Default output folder: benchmarks/GEN
#
# Difficulty levels:
#   Easy   — propositional tautologies, no quantifiers, provable in < 15 steps
#   Medium — one or two quantifiers, always provable, 15-50 steps
#   Hard   — nested quantifiers, mix of Theorem and Satisfiable problems

import os
import random
import itertools

# ─────────────────────────────────────────
# VOCABULARY
# ─────────────────────────────────────────

PREDICATES_1 = ['p', 'q', 'r', 's', 't']       # unary predicates
PREDICATES_2 = ['rel', 'connected', 'leq']      # binary predicates
PROPS        = ['a', 'b', 'c', 'd', 'e', 'f']  # propositional atoms
VARS         = ['X', 'Y', 'Z', 'W']             # bound variables


# ─────────────────────────────────────────
# TPTP FILE WRITER
# ─────────────────────────────────────────

def write_problem(filepath, name, formula_str, status, difficulty, description):
    """Write a single TPTP FOF problem file."""
    content = (
        f"%--------------------------------------------------------------------------\n"
        f"% File     : {name}\n"
        f"% Domain   : Generated\n"
        f"% Problem  : {description}\n"
        f"% Status   : {status}\n"
        f"% Difficulty: {difficulty}\n"
        f"%--------------------------------------------------------------------------\n"
        f"fof({name.lower().replace('+', '_')}, conjecture,\n"
        f"    ( {formula_str} )).\n"
    )
    with open(filepath, 'w') as f:
        f.write(content)


# ─────────────────────────────────────────
# EASY PATTERNS
# Propositional tautologies — no quantifiers
# Always Theorem, provable in under 15 steps
# Tests tiers 1-3 of the algorithm only
# ─────────────────────────────────────────

def easy_patterns():
    problems = []
    for p, q, r in itertools.permutations(PROPS, 3):
        problems += [
            (f'( {p} => {p} )',
             'Theorem', 'easy', f'Identity'),
            (f'( ({p} => {q}) => ({p} => {q}) )',
             'Theorem', 'easy', 'Modus ponens tautology'),
            (f'( ({p} & {q}) => {p} )',
             'Theorem', 'easy', 'Conjunction elimination left'),
            (f'( ({p} & {q}) => {q} )',
             'Theorem', 'easy', 'Conjunction elimination right'),
            (f'( {p} => ({p} | {q}) )',
             'Theorem', 'easy', 'Disjunction introduction left'),
            (f'( {p} => ({q} | {p}) )',
             'Theorem', 'easy', 'Disjunction introduction right'),
            (f'( ~ ~ {p} => {p} )',
             'Theorem', 'easy', 'Double negation elimination'),
            (f'( {p} => ~ ~ {p} )',
             'Theorem', 'easy', 'Double negation introduction'),
            (f'( ({p} => {q}) => (~ {q} => ~ {p}) )',
             'Theorem', 'easy', 'Contrapositive'),
            (f'( ({p} => {q}) => (({q} => {r}) => ({p} => {r})) )',
             'Theorem', 'easy', 'Hypothetical syllogism'),
            (f'( ({p} => {q}) => ({p} => ({p} & {q})) )',
             'Theorem', 'easy', 'Absorption'),
            (f'( (~ {p} & ~ {q}) => ~ ({p} | {q}) )',
             'Theorem', 'easy', 'De Morgan AND to OR'),
            (f'( ~ ({p} & {q}) => (~ {p} | ~ {q}) )',
             'Theorem', 'easy', 'De Morgan negated conjunction'),
            (f'( ({p} & ({p} => {q})) => {q} )',
             'Theorem', 'easy', 'Modus ponens'),
            (f'( ({p} | {q}) => ({q} | {p}) )',
             'Theorem', 'easy', 'Disjunction commutativity'),
            (f'( ({p} & {q}) => ({q} & {p}) )',
             'Theorem', 'easy', 'Conjunction commutativity'),
        ]
    return problems


# ─────────────────────────────────────────
# MEDIUM PATTERNS
# Single quantifiers — always Theorem
# Tests tier 4 quantifier instantiation
# ─────────────────────────────────────────

def medium_patterns():
    problems = []
    for p, q in itertools.permutations(PREDICATES_1, 2):
        for x, y in itertools.permutations(VARS[:3], 2):
            problems += [
                (f'! [{x}] : ( {p}({x}) => {p}({x}) )',
                 'Theorem', 'medium', 'Universal identity'),
                (f'! [{x}] : ( ({p}({x}) & {q}({x})) => {p}({x}) )',
                 'Theorem', 'medium', 'Universal conjunction elimination'),
                (f'( ! [{x}] : {p}({x}) ) => ? [{x}] : {p}({x})',
                 'Theorem', 'medium', 'Universal implies existential'),
                (f'( ! [{x}] : ({p}({x}) => {q}({x})) ) => '
                 f'( (! [{x}] : {p}({x})) => (! [{y}] : {q}({y})) )',
                 'Theorem', 'medium', 'Universal distribution over implication'),
                (f'( {p}({x}) => ? [{y}] : {p}({y}) )',
                 'Theorem', 'medium', 'Existential introduction from instance'),
                (f'( (! [{x}] : ({p}({x}) => {q}({x}))) & {p}({x}) ) => {q}({x})',
                 'Theorem', 'medium', 'Universal modus ponens'),
                (f'( ! [{x}] : ({p}({x}) => {q}({x})) ) => '
                 f'( ! [{x}] : (~ {q}({x}) => ~ {p}({x})) )',
                 'Theorem', 'medium', 'Universal contrapositive'),
                (f'( ! [{x}] : ({p}({x}) & {q}({x})) ) => '
                 f'( (! [{x}] : {p}({x})) & (! [{y}] : {q}({y})) )',
                 'Theorem', 'medium', 'Universal conjunction distribution'),
                (f'( (? [{x}] : {p}({x})) | (? [{x}] : {q}({x})) ) => '
                 f'? [{x}] : ({p}({x}) | {q}({x}))',
                 'Theorem', 'medium', 'Existential disjunction'),
            ]
    return problems


# ─────────────────────────────────────────
# HARD PATTERNS
# Nested quantifiers — mix of Theorem and Satisfiable
# Tests the limits of the algorithm — some will timeout
# ─────────────────────────────────────────

def hard_patterns():
    problems = []
    for p in PREDICATES_1:
        for r in PREDICATES_2:
            for x, y, z in itertools.permutations(VARS, 3):
                problems += [
                    # provable direction
                    (f'( ? [{x}] : ! [{y}] : {r}({x},{y}) ) => '
                     f'( ! [{y}] : ? [{x}] : {r}({x},{y}) )',
                     'Theorem', 'hard',
                     'Existential-universal implies universal-existential'),
                    # unprovable converse
                    (f'( ! [{y}] : ? [{x}] : {r}({x},{y}) ) => '
                     f'( ? [{x}] : ! [{y}] : {r}({x},{y}) )',
                     'Satisfiable', 'hard',
                     'Universal-existential does not imply existential-universal'),
                    # quantifier commutativity
                    (f'( ! [{x}] : ! [{y}] : {r}({x},{y}) ) => '
                     f'( ! [{y}] : ! [{x}] : {r}({x},{y}) )',
                     'Theorem', 'hard',
                     'Universal quantifier commutativity'),
                    # double negation under quantifier
                    (f'( ! [{x}] : ~ ~ {p}({x}) ) => ( ! [{x}] : {p}({x}) )',
                     'Theorem', 'hard',
                     'Universal double negation elimination'),
                    # de morgan for quantifiers
                    (f'( ~ ? [{x}] : {p}({x}) ) => ( ! [{x}] : ~ {p}({x}) )',
                     'Theorem', 'hard',
                     'De Morgan negated existential to universal negation'),
                    # excluded middle does not imply existence
                    (f'( ! [{x}] : ({p}({x}) | ~ {p}({x})) ) => '
                     f'( ? [{x}] : {p}({x}) )',
                     'Satisfiable', 'hard',
                     'Excluded middle does not imply existence'),
                ]
    return problems


# ─────────────────────────────────────────
# MAIN GENERATOR
# ─────────────────────────────────────────

def generate(output_folder: str, seed: int = 42) -> int:
    """Generate benchmark problems and write them to output_folder.

    Problems are built from parameterised logical patterns covering
    three difficulty levels. Duplicates are removed before writing.

    Args:
        output_folder: path to write .p files into
        seed:          random seed for reproducible shuffling

    Returns:
        total number of problems written
    """
    os.makedirs(output_folder, exist_ok=True)
    random.seed(seed)

    # collect all problems tagged by difficulty
    all_problems = []
    all_problems.extend(('easy',   p) for p in easy_patterns())
    all_problems.extend(('medium', p) for p in medium_patterns())
    all_problems.extend(('hard',   p) for p in hard_patterns())

    # deduplicate by formula string
    seen   = set()
    unique = []
    for diff, (formula, status, difficulty, desc) in all_problems:
        if formula not in seen:
            seen.add(formula)
            unique.append((diff, formula, status, difficulty, desc))

    # shuffle for variety across the file listing
    random.shuffle(unique)

    counts = {'easy': 0, 'medium': 0, 'hard': 0}
    for i, (diff, formula, status, difficulty, desc) in enumerate(unique, 1):
        name     = f"GEN{i:04d}+1"
        filepath = os.path.join(output_folder, f"{name}.p")
        write_problem(filepath, name, formula, status, difficulty, desc)
        counts[diff] += 1

    total = sum(counts.values())
    print(f"Generated {total} problems:")
    print(f"  Easy   : {counts['easy']}")
    print(f"  Medium : {counts['medium']}")
    print(f"  Hard   : {counts['hard']}")
    print(f"  Output : {output_folder}")
    return total


if __name__ == '__main__':
    import sys
    folder = sys.argv[1] if len(sys.argv) > 1 else 'benchmarks/GEN'
    generate(folder)