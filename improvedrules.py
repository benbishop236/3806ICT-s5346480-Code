# improvedrules.py
from __future__ import annotations
from formula import (
    Formula, Term,
    Top, Bot, Pred, Not, And, Or, Implies, ForAll, Exists
)
from sequent import Sequent
from substitution import substitute, fresh_var

# Closing rules and quantifier rules are unchanged from rules.py.
# These have no formula selection decision to make so no improvement needed.
from rules import (
    id_rule, top_r, bot_l,
    forall_r, exists_l,
    forall_l, exists_r
)


# ─────────────────────────────────────────
# FORMULA DEPTH
# ─────────────────────────────────────────

def formula_depth(formula: Formula) -> int:
    """Return the nesting depth of a formula.
    Used to prefer simpler formulae when multiple candidates exist.
    Shallower = simpler = tried first.

    Examples:
        Pred('P', ())          → depth 0
        Not(Pred('P', ()))     → depth 1
        And(Pred('A'), Not(B)) → depth 2
    """
    if isinstance(formula, (Top, Bot, Pred)):
        return 0
    elif isinstance(formula, Not):
        return 1 + formula_depth(formula.formula)
    elif isinstance(formula, (And, Or, Implies)):
        return 1 + max(formula_depth(formula.left),
                       formula_depth(formula.right))
    elif isinstance(formula, (ForAll, Exists)):
        return 1 + formula_depth(formula.formula)
    return 0


# ─────────────────────────────────────────
# IMPROVED NON-BRANCHING RULES
# Each picks the shallowest matching formula first
# rather than relying on arbitrary frozenset iteration order.
# This makes rule application deterministic and keeps sequents simpler.
# ─────────────────────────────────────────

def and_l(seq: Sequent):
    """∧L — picks the shallowest conjunction in antecedent."""
    candidates = [f for f in seq.ant if isinstance(f, And)]
    if not candidates:
        return None
    chosen  = min(candidates, key=formula_depth)
    new_ant = (seq.ant - {chosen}) | {chosen.left, chosen.right}
    return [Sequent(frozenset(new_ant), seq.suc)]


def or_r(seq: Sequent):
    """∨R — picks the shallowest disjunction in succedent."""
    candidates = [f for f in seq.suc if isinstance(f, Or)]
    if not candidates:
        return None
    chosen  = min(candidates, key=formula_depth)
    new_suc = (seq.suc - {chosen}) | {chosen.left, chosen.right}
    return [Sequent(seq.ant, frozenset(new_suc))]


def implies_r(seq: Sequent):
    """→R — picks the shallowest implication in succedent."""
    candidates = [f for f in seq.suc if isinstance(f, Implies)]
    if not candidates:
        return None
    chosen  = min(candidates, key=formula_depth)
    new_ant = seq.ant | {chosen.left}
    new_suc = (seq.suc - {chosen}) | {chosen.right}
    return [Sequent(frozenset(new_ant), frozenset(new_suc))]


def not_l(seq: Sequent):
    """¬L — picks the shallowest negation in antecedent."""
    candidates = [f for f in seq.ant if isinstance(f, Not)]
    if not candidates:
        return None
    chosen  = min(candidates, key=formula_depth)
    new_ant = seq.ant - {chosen}
    new_suc = seq.suc | {chosen.formula}
    return [Sequent(frozenset(new_ant), frozenset(new_suc))]


def not_r(seq: Sequent):
    """¬R — picks the shallowest negation in succedent."""
    candidates = [f for f in seq.suc if isinstance(f, Not)]
    if not candidates:
        return None
    chosen  = min(candidates, key=formula_depth)
    new_suc = seq.suc - {chosen}
    new_ant = seq.ant | {chosen.formula}
    return [Sequent(frozenset(new_ant), frozenset(new_suc))]


# ─────────────────────────────────────────
# IMPROVED BRANCHING RULES
# Same depth-first selection logic applied to branching rules
# ─────────────────────────────────────────

def and_r(seq: Sequent):
    """∧R — picks the shallowest conjunction in succedent."""
    candidates = [f for f in seq.suc if isinstance(f, And)]
    if not candidates:
        return None
    chosen = min(candidates, key=formula_depth)
    return [
        Sequent(seq.ant, frozenset((seq.suc - {chosen}) | {chosen.left})),
        Sequent(seq.ant, frozenset((seq.suc - {chosen}) | {chosen.right}))
    ]


def or_l(seq: Sequent):
    """∨L — picks the shallowest disjunction in antecedent."""
    candidates = [f for f in seq.ant if isinstance(f, Or)]
    if not candidates:
        return None
    chosen = min(candidates, key=formula_depth)
    return [
        Sequent(frozenset((seq.ant - {chosen}) | {chosen.left}),  seq.suc),
        Sequent(frozenset((seq.ant - {chosen}) | {chosen.right}), seq.suc)
    ]


def implies_l(seq: Sequent):
    """→L — picks the shallowest implication in antecedent."""
    candidates = [f for f in seq.ant if isinstance(f, Implies)]
    if not candidates:
        return None
    chosen = min(candidates, key=formula_depth)
    return [
        Sequent(seq.ant - {chosen},
                frozenset(seq.suc | {chosen.left})),
        Sequent(frozenset((seq.ant - {chosen}) | {chosen.right}),
                seq.suc)
    ]