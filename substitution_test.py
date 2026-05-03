from formula import *
from substitution import *

# Test 1: basic substitution
# P(x)[a/x]  should give  P(a)
f = Pred('P', (Var('x'),))
result = substitute(f, 'x', Const('a'))
print(result)   # Pred(name='P', args=(Const(name='a'),))

# Test 2: bound variable blocks substitution
# (∀x. P(x))[a/x]  should give  ∀x. P(x)  unchanged
f2 = ForAll('x', Pred('P', (Var('x'),)))
result2 = substitute(f2, 'x', Const('a'))
print(result2)  # ForAll(var='x', ...) unchanged

# Test 3: free vars
# free_vars of ∀x. P(x, y)  should be  {'y'}
f3 = ForAll('x', Pred('P', (Var('x'), Var('y'))))
print(free_vars(f3))  # {'y'}

# Test 4: variable capture avoided
# (∀y. R(x, y))[y/x]  should rename bound y, not capture it
f4 = ForAll('y', Pred('R', (Var('x'), Var('y'))))
result4 = substitute(f4, 'x', Var('y'))
print(result4)  # bound y should be renamed to _v0