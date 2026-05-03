import os
from parser import parse_file

# get the folder this test file lives in
BASE = os.path.dirname(os.path.abspath(__file__))

# Test 1: single conjecture file (SYN001+1)
p1 = parse_file(os.path.join(BASE, 'SYN001+1.p'))
print('=== SYN001+1 ===')
print(f'Status  : {p1.status}')
print(f'Expected: {p1.expected}')
print(f'Formula : {p1.formula}')

print()

# Test 2: axioms + conjecture file (SYN057+1)
p2 = parse_file(os.path.join(BASE, 'SYN057+1.p'))
print('=== SYN057+1 ===')
print(f'Status  : {p2.status}')
print(f'Expected: {p2.expected}')
print(f'Top-level type: {type(p2.formula).__name__}')


from baseline import prove

print()
print('=== END TO END: parse then prove ===')
print(f'SYN001+1: {prove(p1.formula)}')
print(f'SYN057+1: {prove(p2.formula)}')

from baseline import prove

print()
print('=== END TO END: parse then prove ===')

result1 = prove(p1.formula)
print(f'SYN001+1: {result1}')
print(f'  Expected: {p1.expected}, Got: {result1.status}')
print(f'  Match: {result1.status == p1.expected}')

print()

result2 = prove(p2.formula)
print(f'SYN057+1: {result2}')
print(f'  Expected: {p2.expected}, Got: {result2.status}')
print(f'  Match: {result2.status == p2.expected}')