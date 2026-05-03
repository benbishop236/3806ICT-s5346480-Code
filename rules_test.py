from formula import *
from sequent import Sequent
from rules import *

# Test 1: id rule closes branch when A appears on both sides
# P(a) ⊢ P(a)  should close
seq1 = Sequent(
    frozenset({Pred('P', (Const('a'),))}),
    frozenset({Pred('P', (Const('a'),))})
)
print(id_rule(seq1))   # []  meaning closed

# Test 2: and_l splits conjunction in antecedent
# A∧B ⊢ C  should give  A, B ⊢ C
A = Pred('A', ())
B = Pred('B', ())
C = Pred('C', ())
seq2 = Sequent(frozenset({And(A, B)}), frozenset({C}))
print(and_l(seq2))     # [Sequent with A, B in ant]

# Test 3: and_r creates two branches
# ⊢ A∧B  should give  ⊢ A  and  ⊢ B
seq3 = Sequent(frozenset(), frozenset({And(A, B)}))
result = and_r(seq3)
print(len(result))     # 2
print(result[0])       # ∅ ⊢ A
print(result[1])       # ∅ ⊢ B

# Test 4: rule returns None when not applicable
seq4 = Sequent(frozenset({A}), frozenset({B}))
print(and_l(seq4))     # None — no conjunction in antecedent