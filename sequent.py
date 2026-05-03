# sequent.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import FrozenSet, Optional
from formula import Formula

@dataclass(frozen=True)
class Sequent:
    """Represents Γ ⊢ Δ in LK'.
    ant is the antecedent (left side, assumptions).
    suc is the succedent (right side, goals).
    Both are frozensets so the sequent is hashable."""
    ant: FrozenSet[Formula]
    suc: FrozenSet[Formula]

    def __str__(self):
        """Pretty print as:  A, B ⊢ C, D"""
        left  = ', '.join(str(f) for f in self.ant) or '∅'
        right = ', '.join(str(f) for f in self.suc) or '∅'
        return f"{left} ⊢ {right}"


@dataclass
class ProofResult:
    """The outcome of running the prover on a formula.
    status  : 'proved' | 'open' | 'timeout'
    steps   : number of rule applications made
    message : optional extra detail for debugging"""
    status:  str
    steps:   int
    message: Optional[str] = None

    def __str__(self):
        base = f"[{self.status.upper()}] after {self.steps} steps"
        if self.message:
            base += f" — {self.message}"
        return base