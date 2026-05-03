from formula import *
from baseline import prove

# Test 1: A → A  (should prove immediately)
# this is trivial — implies_r moves A to antecedent
# then id closes it
A = Pred('A', ())
f1 = Implies(A, A)
print(prove(f1))   # [PROVED] after N steps

# Test 2: A ∧ B → A  (should prove)
B = Pred('B', ())
f2 = Implies(And(A, B), A)
print(prove(f2))   # [PROVED]

# Test 3: A → A ∧ A  (should prove)
f3 = Implies(A, And(A, A))
print(prove(f3))   # [PROVED]

# Test 4: A → B  (should not prove — open)
f4 = Implies(A, B)
print(prove(f4))   # [OPEN]

# Test 5: ∀x. P(x) → P(x)  (FOL, should prove)
f5 = ForAll('x', Implies(Pred('P', (Var('x'),)),
                          Pred('P', (Var('x'),))))
print(prove(f5))   # [PROVED]