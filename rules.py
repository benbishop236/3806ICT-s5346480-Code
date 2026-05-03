# rules.py
from __future__ import annotations
from formula import (
    Formula, Term,
    Var, Const, FuncApp,
    Top, Bot, Pred, Not, And, Or, Implies, ForAll, Exists
)
from sequent import Sequent
from substitution import substitute, free_vars, fresh_var

# ─────────────────────────────────────────
# GROUP 1 — CLOSING RULES
# return [] when applicable (branch closed)
# return None when not applicable
# ─────────────────────────────────────────

def id_rule(seq: Sequent):
    """id — closes branch if any formula appears on both sides.
    Γ, A ⊢ A, Δ"""
    if seq.ant & seq.suc:   # & on frozensets = intersection
        return []
    return None

def top_r(seq: Sequent):
    """⊤R — closes branch if ⊤ appears in succedent.
    Γ ⊢ ⊤, Δ"""
    if Top() in seq.suc:
        return []
    return None

def bot_l(seq: Sequent):
    """⊥L — closes branch if ⊥ appears in antecedent.
    Γ, ⊥ ⊢ Δ"""
    if Bot() in seq.ant:
        return []
    return None

# ─────────────────────────────────────────
# GROUP 2 — NON-BRANCHING RULES
# return [new_sequent] when applicable
# return None when not applicable
# ─────────────────────────────────────────

def and_l(seq: Sequent):
    """∧L — replaces A∧B in antecedent with A, B.
    Γ, A, B ⊢ Δ
    ───────────
    Γ, A∧B ⊢ Δ"""
    for f in seq.ant:
        if isinstance(f, And):
            new_ant = (seq.ant - {f}) | {f.left, f.right}
            return [Sequent(frozenset(new_ant), seq.suc)]
    return None

def or_r(seq: Sequent):
    """∨R — replaces A∨B in succedent with A, B.
    Γ ⊢ A, B, Δ
    ───────────
    Γ ⊢ A∨B, Δ"""
    for f in seq.suc:
        if isinstance(f, Or):
            new_suc = (seq.suc - {f}) | {f.left, f.right}
            return [Sequent(seq.ant, frozenset(new_suc))]
    return None

def implies_r(seq: Sequent):
    """→R — moves A to antecedent, keeps B in succedent.
    Γ, A ⊢ B, Δ
    ───────────
    Γ ⊢ A→B, Δ"""
    for f in seq.suc:
        if isinstance(f, Implies):
            new_ant = seq.ant | {f.left}
            new_suc = (seq.suc - {f}) | {f.right}
            return [Sequent(frozenset(new_ant), frozenset(new_suc))]
    return None

def not_l(seq: Sequent):
    """¬L — moves formula inside ¬A from antecedent to succedent.
    Γ ⊢ A, Δ
    ────────
    Γ, ¬A ⊢ Δ"""
    for f in seq.ant:
        if isinstance(f, Not):
            new_ant = seq.ant - {f}
            new_suc = seq.suc | {f.formula}
            return [Sequent(frozenset(new_ant), frozenset(new_suc))]
    return None

def not_r(seq: Sequent):
    """¬R — moves formula inside ¬A from succedent to antecedent.
    Γ, A ⊢ Δ
    ────────
    Γ ⊢ ¬A, Δ"""
    for f in seq.suc:
        if isinstance(f, Not):
            new_suc = seq.suc - {f}
            new_ant = seq.ant | {f.formula}
            return [Sequent(frozenset(new_ant), frozenset(new_suc))]
    return None

def forall_r(seq: Sequent):
    """∀R — replaces ∀x.A in succedent with A[a/x], a fresh.
    Side condition: a does not appear in the conclusion.
    Γ ⊢ A[a/x], Δ
    ──────────────
    Γ ⊢ ∀x.A, Δ"""
    for f in seq.suc:
        if isinstance(f, ForAll):
            a = fresh_var()
            instantiated = substitute(f.formula, f.var, Var(a))
            new_suc = (seq.suc - {f}) | {instantiated}
            return [Sequent(seq.ant, frozenset(new_suc))]
    return None

def exists_l(seq: Sequent):
    """∃L — replaces ∃x.A in antecedent with A[a/x], a fresh.
    Side condition: a does not appear in the conclusion.
    Γ, A[a/x] ⊢ Δ
    ──────────────
    Γ, ∃x.A ⊢ Δ"""
    for f in seq.ant:
        if isinstance(f, Exists):
            a = fresh_var()
            instantiated = substitute(f.formula, f.var, Var(a))
            new_ant = (seq.ant - {f}) | {instantiated}
            return [Sequent(frozenset(new_ant), seq.suc)]
    return None

# ─────────────────────────────────────────
# GROUP 3 — BRANCHING RULES
# return [sequent1, sequent2] when applicable
# return None when not applicable
# ─────────────────────────────────────────

def and_r(seq: Sequent):
    """∧R — splits A∧B in succedent into two branches.
    Γ ⊢ A, Δ    Γ ⊢ B, Δ
    ─────────────────────
         Γ ⊢ A∧B, Δ"""
    for f in seq.suc:
        if isinstance(f, And):
            new_suc_left  = (seq.suc - {f}) | {f.left}
            new_suc_right = (seq.suc - {f}) | {f.right}
            return [
                Sequent(seq.ant, frozenset(new_suc_left)),
                Sequent(seq.ant, frozenset(new_suc_right))
            ]
    return None

def or_l(seq: Sequent):
    """∨L — splits A∨B in antecedent into two branches.
    Γ, A ⊢ Δ    Γ, B ⊢ Δ
    ─────────────────────
         Γ, A∨B ⊢ Δ"""
    for f in seq.ant:
        if isinstance(f, Or):
            new_ant_left  = (seq.ant - {f}) | {f.left}
            new_ant_right = (seq.ant - {f}) | {f.right}
            return [
                Sequent(frozenset(new_ant_left),  seq.suc),
                Sequent(frozenset(new_ant_right), seq.suc)
            ]
    return None

def implies_l(seq: Sequent):
    """→L — splits A→B in antecedent into two branches.
    Γ ⊢ A, Δ    Γ, B ⊢ Δ
    ─────────────────────
       Γ, A→B ⊢ Δ"""
    for f in seq.ant:
        if isinstance(f, Implies):
            # left branch: prove A (move to succedent)
            new_suc_left = (seq.suc) | {f.left}
            # right branch: assume B (move to antecedent)
            new_ant_right = (seq.ant - {f}) | {f.right}
            return [
                Sequent(seq.ant - {f}, frozenset(new_suc_left)),
                Sequent(frozenset(new_ant_right), seq.suc)
            ]
    return None

# ─────────────────────────────────────────
# GROUP 4 — COPY RULES
# take an extra term argument
# keep the original formula (copy rule)
# return [new_sequent] when applicable
# return None when not applicable
# ─────────────────────────────────────────

def forall_l(seq: Sequent, term: Term):
    """∀L — adds A[t/x] to antecedent, keeps ∀x.A.
    Γ, ∀x.A, A[t/x] ⊢ Δ
    ─────────────────────
       Γ, ∀x.A ⊢ Δ"""
    for f in seq.ant:
        if isinstance(f, ForAll):
            instantiated = substitute(f.formula, f.var, term)
            # keep f in ant (copy rule), add instantiated version
            new_ant = seq.ant | {instantiated}
            return [Sequent(frozenset(new_ant), seq.suc)]
    return None

def exists_r(seq: Sequent, term: Term):
    """∃R — adds A[t/x] to succedent, keeps ∃x.A.
    Γ ⊢ ∃x.A, A[t/x], Δ
    ─────────────────────
       Γ ⊢ ∃x.A, Δ"""
    for f in seq.suc:
        if isinstance(f, Exists):
            instantiated = substitute(f.formula, f.var, term)
            # keep f in suc (copy rule), add instantiated version
            new_suc = seq.suc | {instantiated}
            return [Sequent(seq.ant, frozenset(new_suc))]
    return None

