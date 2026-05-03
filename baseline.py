# baseline.py
from __future__ import annotations
from formula import (
    Formula, Term,
    Var, Const, FuncApp,
    Top, Bot, Pred, Not, And, Or, Implies, ForAll, Exists
)
from sequent import Sequent, ProofResult
from substitution import fresh_var, substitute
from rules import (
    id_rule, top_r, bot_l,
    and_l, or_r, implies_r, not_l, not_r, forall_r, exists_l,
    and_r, or_l, implies_l,
    forall_l, exists_r
)


# ─────────────────────────────────────────
# HELPER: collect terms from a single term
# ─────────────────────────────────────────

def _collect_from_term(term: Term, out: set):
    """Recursively collect all Var and Const objects from a term."""
    if isinstance(term, (Var, Const)):
        out.add(term)
    elif isinstance(term, FuncApp):
        for arg in term.args:
            _collect_from_term(arg, out)


# ─────────────────────────────────────────
# HELPER: collect terms from a formula
# ─────────────────────────────────────────

def _collect_from_formula(formula: Formula, out: set):
    """Recursively collect all Var and Const objects from a formula."""
    if isinstance(formula, (Top, Bot)):
        pass
    elif isinstance(formula, Pred):
        for arg in formula.args:
            _collect_from_term(arg, out)
    elif isinstance(formula, Not):
        _collect_from_formula(formula.formula, out)
    elif isinstance(formula, (And, Or, Implies)):
        _collect_from_formula(formula.left, out)
        _collect_from_formula(formula.right, out)
    elif isinstance(formula, (ForAll, Exists)):
        _collect_from_formula(formula.formula, out)


# ─────────────────────────────────────────
# HELPER: collect all terms in a sequent
# ─────────────────────────────────────────

def collect_terms(seq: Sequent) -> set:
    """Walk every formula in the sequent and collect
    all Var and Const objects found.
    Used to find candidates for tier 4 instantiation."""
    terms = set()
    for f in seq.ant:
        _collect_from_formula(f, terms)
    for f in seq.suc:
        _collect_from_formula(f, terms)
    return terms


# ─────────────────────────────────────────
# MAIN PROVER
# ─────────────────────────────────────────
import time
def prove(formula: Formula, depth_limit: int = 50, time_limit_s=5.0) -> ProofResult:
    """
    Run Algorithm 2 on a formula.
    Returns a ProofResult with status 'proved', 'open', or 'timeout'.
    """

    start_time = time.perf_counter()
    start = Sequent(frozenset(), frozenset({formula}))
    open_branches = [start]
    used_terms = {}
    steps = 0

    while open_branches:

        # check depth limit
        if steps >= depth_limit:
            return ProofResult('timeout', steps)

            # wall clock time limit
        if time.perf_counter() - start_time > time_limit_s:
            return ProofResult('timeout', steps, 'time limit reached')
        # take the next open branch
        seq = open_branches.pop(0)
        steps += 1

        # ── TIER 1: closing rules ──────────────────
        closed = False
        for rule in [id_rule, top_r, bot_l]:
            result = rule(seq)
            if result is not None:
                closed = True
                break

        if closed:
            continue

        # ── TIER 2: non-branching rules ────────────
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
        for rule in [and_r, or_l, implies_l]:
            result = rule(seq)
            if result is not None:
                open_branches = result + open_branches
                applied = True
                break

        if applied:
            continue

        # ── TIER 4: ∀L / ∃R with existing term ────
        available_terms = collect_terms(seq)
        quantifier_applied = False

        for f in list(seq.ant) + list(seq.suc):
            if not isinstance(f, (ForAll, Exists)):
                continue

            if f not in used_terms:
                used_terms[f] = set()

            untried = available_terms - used_terms[f]

            if untried:
                term = next(iter(untried))
                used_terms[f].add(term)

                if isinstance(f, ForAll) and f in seq.ant:
                    result = forall_l(seq, term)
                elif isinstance(f, Exists) and f in seq.suc:
                    result = exists_r(seq, term)
                else:
                    continue

                if result is not None:
                    open_branches = result + open_branches
                    quantifier_applied = True
                    break

        if quantifier_applied:
            continue

        # ── TIER 5: ∀L / ∃R with fresh term ───────
        for f in list(seq.ant) + list(seq.suc):
            if isinstance(f, ForAll) and f in seq.ant:
                term = Var(fresh_var())
                result = forall_l(seq, term)
                if result is not None:
                    open_branches = result + open_branches
                    quantifier_applied = True
                    break
            elif isinstance(f, Exists) and f in seq.suc:
                term = Var(fresh_var())
                result = exists_r(seq, term)
                if result is not None:
                    open_branches = result + open_branches
                    quantifier_applied = True
                    break

        if quantifier_applied:
            continue

        # ── TIER 6: nothing applies ────────────────
        return ProofResult('open', steps, 'no rule applicable')

    # all branches closed
    return ProofResult('proved', steps)