from formula import *
from baseline import prove as baseline_prove
from improved import prove as improved_prove

tests = [
    ('A → A',
     Implies(Pred('A',()), Pred('A',())),
     'proved'),
    ('A ∧ B → A',
     Implies(And(Pred('A',()), Pred('B',())), Pred('A',())),
     'proved'),
    ('A → A ∧ A',
     Implies(Pred('A',()), And(Pred('A',()), Pred('A',()))),
     'proved'),
    ('A → B  (unprovable)',
     Implies(Pred('A',()), Pred('B',())),
     'open'),
    ('∀x. P(x) → P(x)',
     ForAll('x', Implies(Pred('P',(Var('x'),)), Pred('P',(Var('x'),)))),
     'proved'),
    ('∃x.P(x) → ∃x.P(x)',
     Implies(Exists('x', Pred('P',(Var('x'),))),
             Exists('x', Pred('P',(Var('x'),)))),
     'proved'),
    ('(A∧B)∧C → A∧(B∧C)',
     Implies(And(And(Pred('A',()), Pred('B',())), Pred('C',())),
             And(Pred('A',()), And(Pred('B',()), Pred('C',())))),
     'proved'),
]

print(f"{'Test':<35} {'Exp':<8} {'Baseline':<20} {'Improved':<20} {'OK'}")
print('-' * 90)
all_pass = True
for name, formula, expected in tests:
    b = baseline_prove(formula, 500, 10.0)
    i = improved_prove(formula, 500, 10.0)
    ok = b.status == expected and i.status == expected
    if not ok: all_pass = False
    print(f"{name:<35} {expected:<8} "
          f"{b.status+'('+str(b.steps)+'s)':<20} "
          f"{i.status+'('+str(i.steps)+'s)':<20} "
          f"{'✓' if ok else '✗ FAIL'}")

print(f"\nAll passed: {all_pass}")