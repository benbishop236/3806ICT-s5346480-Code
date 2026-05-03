# substitution.py
from __future__ import annotations
from formula import (
    Formula, Term,
    Var, Const, FuncApp,
    Top, Bot, Pred, Not, And, Or, Implies, ForAll, Exists
)

# ─────────────────────────────────────────
# HELPER: fresh variable name generator
# ─────────────────────────────────────────

_fresh_counter = 0

def fresh_var() -> str:
    """Returns a new variable name that has never been used before.
    e.g. _a0, _a1, _a2 ...
    Used to avoid variable capture during substitution."""
    global _fresh_counter
    name = f"_a{_fresh_counter}"
    _fresh_counter += 1
    return name


# ─────────────────────────────────────────
# FREE VARIABLES
# ─────────────────────────────────────────

def free_vars_term(term: Term) -> set[str]:
    """Returns the set of free variable names in a term."""
    if isinstance(term, Var):
        # a variable is always free at the term level
        return {term.name}
    elif isinstance(term, Const):
        # constants have no variables
        return set()
    elif isinstance(term, FuncApp):
        # collect free vars from all arguments
        result = set()
        for arg in term.args:
            result |= free_vars_term(arg)
        return result


def free_vars(formula: Formula) -> set[str]:
    """Returns the set of free variable names in a formula."""
    if isinstance(formula, (Top, Bot)):
        return set()
    elif isinstance(formula, Pred):
        # free vars come from the terms in the args
        result = set()
        for arg in formula.args:
            result |= free_vars_term(arg)
        return result
    elif isinstance(formula, Not):
        return free_vars(formula.formula)
    elif isinstance(formula, (And, Or, Implies)):
        return free_vars(formula.left) | free_vars(formula.right)
    elif isinstance(formula, (ForAll, Exists)):
        # x is bound here — remove it from the result
        inner = free_vars(formula.formula)
        return inner - {formula.var}


# ─────────────────────────────────────────
# SUBSTITUTION IN TERMS
# ─────────────────────────────────────────

def substitute_term(term: Term, var_name: str, replacement: Term) -> Term:
    """Replace every occurrence of Var(var_name) in term with replacement."""
    if isinstance(term, Var):
        if term.name == var_name:
            return replacement   # this is the variable — replace it
        else:
            return term          # different variable — leave it alone
    elif isinstance(term, Const):
        return term              # constants never change
    elif isinstance(term, FuncApp):
        # rebuild the function application with substituted args
        new_args = tuple(substitute_term(a, var_name, replacement)
                         for a in term.args)
        return FuncApp(term.func_name, new_args)


# ─────────────────────────────────────────
# SUBSTITUTION IN FORMULAE
# ─────────────────────────────────────────

def substitute(formula: Formula, var_name: str, replacement: Term) -> Formula:
    """Return a new formula with every free occurrence of
    Var(var_name) replaced by replacement.
    Handles variable capture by renaming bound variables when needed."""

    if isinstance(formula, (Top, Bot)):
        return formula

    elif isinstance(formula, Pred):
        new_args = tuple(substitute_term(a, var_name, replacement)
                         for a in formula.args)
        return Pred(formula.name, new_args)

    elif isinstance(formula, Not):
        return Not(substitute(formula.formula, var_name, replacement))

    elif isinstance(formula, And):
        return And(
            substitute(formula.left,  var_name, replacement),
            substitute(formula.right, var_name, replacement)
        )

    elif isinstance(formula, Or):
        return Or(
            substitute(formula.left,  var_name, replacement),
            substitute(formula.right, var_name, replacement)
        )

    elif isinstance(formula, Implies):
        return Implies(
            substitute(formula.left,  var_name, replacement),
            substitute(formula.right, var_name, replacement)
        )

    elif isinstance(formula, (ForAll, Exists)):
        # if this quantifier binds the variable we are replacing,
        # do not go inside — var_name is not free in the body
        if formula.var == var_name:
            return formula

        # variable capture check:
        # if the bound variable appears free in replacement,
        # rename it to something fresh before substituting
        if formula.var in free_vars_term(replacement):
            fresh = fresh_var()
            new_body = substitute(formula.formula, formula.var, Var(fresh))
            new_body = substitute(new_body, var_name, replacement)
            if isinstance(formula, ForAll):
                return ForAll(fresh, new_body)
            else:
                return Exists(fresh, new_body)

        # safe to substitute directly into the body
        new_body = substitute(formula.formula, var_name, replacement)
        if isinstance(formula, ForAll):
            return ForAll(formula.var, new_body)
        else:
            return Exists(formula.var, new_body)