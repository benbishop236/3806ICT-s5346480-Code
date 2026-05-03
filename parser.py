# parser.py
from __future__ import annotations
import re
from typing import Optional
from lark import Lark, Transformer, v_args
from formula import (
    Formula, Term,
    Var, Const, FuncApp,
    Top, Bot, Pred, Not, And, Or, Implies, ForAll, Exists
)

# ─────────────────────────────────────────
# TPTP FOF GRAMMAR
# ─────────────────────────────────────────

TPTP_GRAMMAR = r"""
    start       : fof_entry+

    fof_entry   : "fof" "(" name "," role "," formula ")" "."

    role        : ROLE_WORD
    ROLE_WORD   : "axiom" | "conjecture" | "hypothesis"
                | "negated_conjecture" | "lemma" | "theorem"
                | "assumption" | "definition" | "unknown"

    name        : WORD | INTEGER

    // Formula precedence levels (lowest first)
    ?formula    : bicond

    ?bicond     : bicond "<=>" xor   -> iff
                | bicond "<~>" xor   -> xor
                | xor

    ?xor        : xor "<~>" rimpl    -> xor
                | rimpl

    ?rimpl      : rimpl "<=" and_or  -> rimpl
                | and_or

    ?and_or     : and_or "=>" unary  -> implies
                | and_or "&"  unary  -> and_
                | and_or "|"  unary  -> or_
                | unary

    ?unary      : "~" unary          -> not_
                | quantified
                | atom

    ?quantified : "!" "[" var_list "]" ":" unary  -> forall
                | "?" "[" var_list "]" ":" unary  -> exists_

    var_list    : UWORD ("," UWORD)*

    ?atom       : "$true"            -> top
                | "$false"           -> bot
                | LWORD "(" args ")" -> pred_app
                | LWORD              -> prop
                | "(" formula ")"

    args        : term ("," term)*

    ?term       : LWORD "(" args ")" -> func_app
                | UWORD              -> var
                | LWORD              -> const

    // Uppercase first letter = variable, lowercase = constant/predicate/function
    UWORD       : /[A-Z][A-Za-z0-9_]*/
    LWORD       : /[a-z_][A-Za-z0-9_]*/
    INTEGER     : /[0-9]+/
    WORD        : /[A-Za-z0-9_]+/

    %import common.WS
    %ignore WS
    %ignore /%[^\n]*/        // line comments starting with %
    %ignore /\/\*.*?\*\//s   // block comments /* ... */
"""

# ─────────────────────────────────────────
# TRANSFORMER: lark tree → Formula objects
# ─────────────────────────────────────────

class FOFTransformer(Transformer):

    # ── terms ──────────────────────────────
    @v_args(inline=True)
    def var(self, name):
        return Var(str(name))

    @v_args(inline=True)
    def const(self, name):
        return Const(str(name))

    @v_args(inline=True)
    def func_app(self, name, args):
        return FuncApp(str(name), tuple(args.children))

    # ── atoms ──────────────────────────────
    @v_args(inline=True)
    def top(self):
        return Top()

    @v_args(inline=True)
    def bot(self):
        return Bot()

    @v_args(inline=True)
    def prop(self, name):
        return Pred(str(name), ())

    @v_args(inline=True)
    def pred_app(self, name, args):
        return Pred(str(name), tuple(args.children))

    # ── connectives ────────────────────────
    @v_args(inline=True)
    def not_(self, f):
        return Not(f)

    @v_args(inline=True)
    def and_(self, left, right):
        return And(left, right)

    @v_args(inline=True)
    def or_(self, left, right):
        return Or(left, right)

    @v_args(inline=True)
    def implies(self, left, right):
        return Implies(left, right)

    @v_args(inline=True)
    def rimpl(self, left, right):
        # A <= B  desugars to  B => A
        return Implies(right, left)

    @v_args(inline=True)
    def iff(self, left, right):
        # A <=> B  desugars to  (A => B) & (B => A)
        return And(Implies(left, right), Implies(right, left))

    @v_args(inline=True)
    def xor(self, left, right):
        # A <~> B  desugars to  ~(A <=> B)
        return Not(And(Implies(left, right), Implies(right, left)))

    # ── quantifiers ────────────────────────
    @v_args(inline=True)
    def forall(self, var_list, body):
        vars_ = list(var_list.children)
        result = body
        for v in reversed(vars_):
            result = ForAll(str(v), result)
        return result

    @v_args(inline=True)
    def exists_(self, var_list, body):
        vars_ = list(var_list.children)
        result = body
        for v in reversed(vars_):
            result = Exists(str(v), result)
        return result

    # ── fof entry ──────────────────────────
    @v_args(inline=True)
    def fof_entry(self, name, role, formula):
        return (str(role.children[0]), formula)

    # start receives children as a list — do NOT use inline
    def start(self, items):
        return list(items)


# ─────────────────────────────────────────
# BUILD THE PARSER (done once at import)
# ─────────────────────────────────────────

_parser      = Lark(TPTP_GRAMMAR, parser='lalr')
_transformer = FOFTransformer()


# ─────────────────────────────────────────
# STATUS EXTRACTION
# ─────────────────────────────────────────

def extract_status(text: str) -> Optional[str]:
    """Read the % Status line from a TPTP file header."""
    match = re.search(r'%\s*Status\s*:\s*(\w+)', text)
    return match.group(1) if match else None


def expected_result(status: Optional[str]) -> Optional[str]:
    """Convert TPTP status string to expected ProofResult status.

    Theorem / Unsatisfiable → 'proved'
    Satisfiable / CounterSatisfiable → 'open'
    Unknown / None → None (skip validity check)
    """
    if status in ('Theorem', 'Unsatisfiable'):
        return 'proved'
    elif status in ('Satisfiable', 'CounterSatisfiable'):
        return 'open'
    return None


# ─────────────────────────────────────────
# NORMALISE TRANSFORMER OUTPUT
# ─────────────────────────────────────────

def _normalise_entries(result) -> list:
    """Ensure transformer output is always a list of (role, formula) tuples.

    With LALR parsing and a single fof entry, lark passes the tuple
    directly rather than wrapping it in a list. This normalises both
    cases so combine_entries always receives a consistent type.
    """
    if isinstance(result, tuple):
        return [result]
    if isinstance(result, list):
        return result
    return []


# ─────────────────────────────────────────
# COMBINE AXIOMS + CONJECTURE
# ─────────────────────────────────────────

def combine_entries(entries: list) -> Optional[Formula]:
    """Given a list of (role, formula) pairs, produce one formula.

    Single conjecture, no axioms → return conjecture directly.
    Axioms + conjecture → return Implies(And(axioms...), conjecture).
    No conjecture → return None (skip this file).
    """
    axioms = [f for role, f in entries
              if role in ('axiom', 'hypothesis', 'assumption')]
    conjectures = [f for role, f in entries
                   if role == 'conjecture']

    if not conjectures:
        return None

    conjecture = conjectures[0]

    if not axioms:
        return conjecture

    premise = axioms[0]
    for ax in axioms[1:]:
        premise = And(premise, ax)

    return Implies(premise, conjecture)


# ─────────────────────────────────────────
# PUBLIC RESULT TYPE
# ─────────────────────────────────────────

class ParsedProblem:
    """Everything extracted from one TPTP .p file."""

    def __init__(self, formula: Formula,
                 status:   Optional[str],
                 expected: Optional[str],
                 filepath: str):
        self.formula  = formula
        self.status   = status
        self.expected = expected
        self.filepath = filepath

    def __str__(self):
        return (f"ParsedProblem(file={self.filepath}, "
                f"status={self.status}, expected={self.expected})")


# ─────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────

def parse_file(filepath: str) -> Optional[ParsedProblem]:
    """Parse a TPTP FOF file and return a ParsedProblem.

    Returns None if the file has no conjecture or cannot be parsed.
    """
    with open(filepath, 'r') as f:
        text = f.read()

    status   = extract_status(text)
    expected = expected_result(status)

    text_clean = re.sub(r"include\s*\([^)]*\)\s*\.", "", text)

    try:
        tree    = _parser.parse(text_clean)
        raw     = _transformer.transform(tree)
        entries = _normalise_entries(raw)
        formula = combine_entries(entries)
    except Exception as e:
        print(f"  [PARSE ERROR] {filepath}: {e}")
        return None

    if formula is None:
        return None

    return ParsedProblem(formula, status, expected, filepath)