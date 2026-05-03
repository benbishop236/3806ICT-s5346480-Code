# improved.py
from __future__ import annotations
import time
from formula import (
    Formula, Term,
    Var, Const, FuncApp,
    Top, Bot, Pred, Not, And, Or, Implies, ForAll, Exists
)
from sequent import Sequent, ProofResult
from substitution import fresh_var
from baseline import collect_terms, _collect_from_formula

# Import all rules from improvedrules.py
# Non-branching and branching rules use depth-based formula selection (Improvement 1)
# Closing and quantifier rules are imported unchanged from rules.py via improvedrules.py
from improvedrules import (
    formula_depth,
    id_rule, top_r, bot_l,
    and_l, or_r, implies_r, not_l, not_r, forall_r, exists_l,
    and_r, or_l, implies_l,
    forall_l, exists_r
)


# ─────────────────────────────────────────
# IMPROVEMENT 2: targeted term scoring
# ─────────────────────────────────────────

def score_terms(terms: set, opposite_side) -> list:
    """Order terms by likelihood of enabling branch closure.

    When instantiating ∀L or ∃R, the algorithm needs to pick a term
    to substitute for the bound variable. The naive approach tries
    terms in arbitrary order. This function scores terms so that:

    - Terms already visible on the opposite side of the sequent are
      tried first — these are most likely to eventually match via id
    - Constants are preferred over variables as they are more specific
    - Fresh variables (machine-generated) are tried last

    Args:
        terms:         set of Term objects available to try
        opposite_side: frozenset of formulae on the other side of ⊢
                       (use seq.suc when applying ∀L to antecedent,
                        use seq.ant when applying ∃R to succedent)
    """
    opposite_terms = set()
    for f in opposite_side:
        _collect_from_formula(f, opposite_terms)

    def score(t):
        if t in opposite_terms:
            return 0   # visible on opposite side — try first
        if isinstance(t, Const):
            return 1   # constants before variables
        return 2       # fresh variables last

    return sorted(terms, key=score)


# ─────────────────────────────────────────
# MAIN IMPROVED PROVER
# ─────────────────────────────────────────

def prove(formula: Formula,
          depth_limit:  int   = 500,
          time_limit_s: float = 10.0) -> ProofResult:
    """
    Improved backward proof search for first-order logic using LK'.

    Implements Algorithm 2 from the textbook with three enhancements:

    Improvement 1 — Deterministic formula selection (in improvedrules.py)
        Each rule selects the shallowest matching formula by nesting depth
        rather than relying on arbitrary frozenset iteration order.
        This makes the algorithm deterministic across runs and tends to
        keep sequents simpler by resolving shallow structure first.

    Improvement 2 — Targeted term selection (score_terms)
        When instantiating ∀L or ∃R, available terms are scored by
        visibility on the opposite side of the sequent. Terms already
        present there are tried first as they are most likely to
        eventually unify via the id rule and close a branch.

    """
    start_time    = time.perf_counter()
    start_sequent = Sequent(frozenset(), frozenset({formula}))
    open_branches = [start_sequent]
    used_terms    = {}
    steps         = 0

    while open_branches:

        # depth limit
        if steps >= depth_limit:
            return ProofResult('timeout', steps, 'depth limit reached')

        # wall clock time limit
        if time.perf_counter() - start_time > time_limit_s:
            return ProofResult('timeout', steps, 'time limit reached')

        seq = open_branches.pop(0)
        steps += 1


        # ── TIER 1: closing rules ──────────────────
        # unchanged — no selection decision needed here
        closed = False
        for rule in [id_rule, top_r, bot_l]:
            if rule(seq) is not None:
                closed = True
                break

        if closed:
            continue

        # ── TIER 2: non-branching rules ────────────
        # improvement 1 active via improvedrules.py
        applied = False
        for rule in [and_l, or_r, implies_r, not_l, not_r, forall_r, exists_l]:
            result = rule(seq)
            if result is not None:
                open_branches = result + open_branches
                applied = True
                break

        if applied:
            continue

        # ── TIER 3: branching rules ────────────────
        # improvement 1 active via improvedrules.py
        for rule in [and_r, or_l, implies_l]:
            result = rule(seq)
            if result is not None:
                open_branches = result + open_branches
                applied = True
                break

        if applied:
            continue

        # ── TIER 4: ∀L / ∃R with existing term ────
        # improvement 2 active — score_terms orders candidates
        available_terms     = collect_terms(seq)
        quantifier_applied  = False

        for f in list(seq.ant) + list(seq.suc):
            if not isinstance(f, (ForAll, Exists)):
                continue

            if f not in used_terms:
                used_terms[f] = set()

            untried = available_terms - used_terms[f]

            if untried:
                if isinstance(f, ForAll) and f in seq.ant:
                    # try terms visible in succedent first
                    scored = score_terms(untried, seq.suc)
                    term   = scored[0]
                    used_terms[f].add(term)
                    result = forall_l(seq, term)

                elif isinstance(f, Exists) and f in seq.suc:
                    # try terms visible in antecedent first
                    scored = score_terms(untried, seq.ant)
                    term   = scored[0]
                    used_terms[f].add(term)
                    result = exists_r(seq, term)

                else:
                    continue

                if result is not None:
                    open_branches      = result + open_branches
                    quantifier_applied = True
                    break

        if quantifier_applied:
            continue

        # ── TIER 5: ∀L / ∃R with fresh term ───────
        for f in list(seq.ant) + list(seq.suc):
            if isinstance(f, ForAll) and f in seq.ant:
                result = forall_l(seq, Var(fresh_var()))
                if result is not None:
                    open_branches      = result + open_branches
                    quantifier_applied = True
                    break

            elif isinstance(f, Exists) and f in seq.suc:
                result = exists_r(seq, Var(fresh_var()))
                if result is not None:
                    open_branches      = result + open_branches
                    quantifier_applied = True
                    break

        if quantifier_applied:
            continue

        # ── TIER 6: nothing applies ────────────────
        return ProofResult('open', steps, 'no rule applicable')

    # all branches closed
    return ProofResult('proved', steps)