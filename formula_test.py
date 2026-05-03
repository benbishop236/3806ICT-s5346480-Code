from formula import *

# Build: ∀x. P(x) → Q(x)
f = ForAll('x', Implies(Pred('P', (Var('x'),)), Pred('Q', (Var('x'),))))
print(f)

# Check two identical formulae are equal
f1 = And(Pred('A', ()), Pred('B', ()))
f2 = And(Pred('A', ()), Pred('B', ()))
print(f1 == f2)   # should print True

# Check a formula can live in a set (requires hashability)
s = {f1, f2}
print(len(s))     # should print 1, not 2