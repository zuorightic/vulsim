"""Narrow, auditable RTL rewrites for offline implementation sensitivity probes.

These helpers neither change the production emitter nor provide a price.  The
statement permutation accepts only independent, single-line nonblocking clocked
assignments.  The commutation certificate keeps the entire surrounding RTL
byte-identical and requires a separately proved equivalence receipt.
"""
from collections import Counter
import hashlib
import re


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def reorder_independent_clocked(text):
    chunks = text.split('endmodule')
    changes = []
    for index, chunk in enumerate(chunks[:-1]):
        lines = chunk.splitlines(keepends=True)
        positions = [i for i, line in enumerate(lines) if line.startswith('always @')]
        if not positions:
            continue
        statements = [lines[i] for i in positions]
        targets = []
        for statement in statements:
            if not statement.startswith('always @(posedge clk)') or 'begin' in statement or '=' in statement.replace('<=', ''):
                raise ValueError('unsupported procedural statement')
            lhs = re.findall(r'\b([A-Za-z_][A-Za-z_0-9]*)\s*<=', statement)
            if not lhs or len(set(lhs)) != 1:
                raise ValueError('statement must assign one register')
            targets.append(lhs[0])
        if len(set(targets)) != len(targets):
            raise ValueError('multiple processes write the same register')
        for location, replacement in zip(positions, reversed(statements), strict=True):
            lines[location] = replacement
        changed = ''.join(lines)
        if Counter(changed.splitlines()) != Counter(chunk.splitlines()):
            raise ValueError('permutation changed a statement')
        changes.append(dict(module=re.search(r'\bmodule\s+(\w+)', chunk)[1],
                            statements=len(statements), unique_targets=targets))
        chunks[index] = changed
    result = 'endmodule'.join(chunks)
    if result == text or not changes:
        raise ValueError('empty statement permutation')
    return result, dict(kind='independent_nonblocking_process_order', modules=changes,
                        original_sha256=digest(text), variant_sha256=digest(result),
                        declarations_and_statements_preserved=True)


def commute_expression(text, original, swapped):
    if text.count(original) != 1 or not original or original == swapped:
        raise ValueError('commutation needs one explicit expression')
    # The expression is deliberately supplied by the registered experiment;
    # this is a certificate of the exact edit, not a general Verilog parser.
    result = text.replace(original, swapped)
    return result, dict(kind='registered_addition_commutation', original=original,
                        swapped=swapped, original_sha256=digest(text),
                        variant_sha256=digest(result), outside_expression_unchanged=True,
                        equivalence_proof_required=True)
