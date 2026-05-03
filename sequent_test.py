from formula import *
from sequent import *

A = Implies(Pred('P', (Var('x'),)), Pred('P', (Var('x'),)))

# ⊢ A  means empty antecedent, A in succedent
start = Sequent(
    ant = frozenset(),
    suc = frozenset({A})
)

print(start)