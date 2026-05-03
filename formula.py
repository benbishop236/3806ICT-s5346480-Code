# formula.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Union, Tuple

# ─────────────────────────────────────────
# TERMS  (the objects being talked about)
# ─────────────────────────────────────────

@dataclass(frozen=True)
class Var:
    """A logical variable, e.g. x, y, z.
    Variables can be bound by ∀ and ∃."""
    name: str

@dataclass(frozen=True)
class Const:
    """A constant, e.g. a, b, c.
    Constants are fixed objects in the domain."""
    name: str

@dataclass(frozen=True)
class FuncApp:
    """A function applied to arguments, e.g. f(a, b).
    func_name is the function name.
    args is a tuple of Terms."""
    func_name: str
    args: Tuple[Term, ...]

# A Term is any of the above
Term = Union[Var, Const, FuncApp]


# ─────────────────────────────────────────
# FORMULAE  (statements that are true/false)
# ─────────────────────────────────────────

@dataclass(frozen=True)
class Top:
    """⊤ — always true."""
    pass

@dataclass(frozen=True)
class Bot:
    """⊥ — always false."""
    pass

@dataclass(frozen=True)
class Pred:
    """A predicate applied to terms, e.g. P(x, a).
    This is the atomic building block of formulae."""
    name: str
    args: Tuple[Term, ...]

@dataclass(frozen=True)
class Not:
    """¬A — negation of a formula."""
    formula: Formula

@dataclass(frozen=True)
class And:
    """A ∧ B — conjunction."""
    left: Formula
    right: Formula

@dataclass(frozen=True)
class Or:
    """A ∨ B — disjunction."""
    left: Formula
    right: Formula

@dataclass(frozen=True)
class Implies:
    """A → B — implication."""
    left: Formula
    right: Formula

@dataclass(frozen=True)
class ForAll:
    """∀x. A — universal quantifier.
    var is the name of the bound variable (a string).
    formula is the body A."""
    var: str
    formula: Formula

@dataclass(frozen=True)
class Exists:
    """∃x. A — existential quantifier."""
    var: str
    formula: Formula

# A Formula is any of the above
Formula = Union[Top, Bot, Pred, Not, And, Or, Implies, ForAll, Exists]