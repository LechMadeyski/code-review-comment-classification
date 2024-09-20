import ast
from ast import AST
from unittest import TestCase
from textwrap import dedent
from typing import Any

from features.text_utils import extract_range, line_count
from features.ast_kind import AstKind, get_expr_kind, get_stmt_kind, is_function

_OPTIMAL_CONTEXT_LINES = 20
_MAX_CONTEXT_STMT_LINES = 100


def has_syntax_error(code: str) -> bool:
    try:
        ast.parse(code)
        return False
    except SyntaxError:
        return True


def extract_context(code: str, start_line: int | None, end_line: int | None) -> tuple[str, ast.stmt | ast.expr | ast.Module, int, int]:
    # Return empty module for empty (blank line) contexts
    if start_line is None or end_line is None or extract_range(code, start_line, end_line).strip() == "":
        return "", ast.parse(""), -1, -1

    # Build the statement path from the context node to the root
    tree = ast.parse(code)
    _adjust_decorator_lines(tree)
    path = _build_path(tree, start_line, end_line, [])

    # If the path is empty (probably a top-level comment), return the entire AST
    if len(path) == 0:
        return code, tree, 1, line_count(code)

    # Prefer functions over other nodes
    if func := next((n for n in path if is_function(n)), None):
        return _return_context(code, func)

    # Select the node which has the most suitable length
    node = min(path, key=_context_score)

    # Use statement if it is not extremely long
    if _end_lineno(node) - node.lineno + 1 <= _MAX_CONTEXT_STMT_LINES:
        return _return_context(code, node)

    # Find the most suitable statement subexpression
    path = [n for n in ast.walk(node)
            if isinstance(n, ast.expr)
            and n.lineno <= start_line and end_line <= _end_lineno(n)]
    node = min(path, key=_context_score, default=node)
    segment = ast.get_source_segment(code, node)
    assert segment is not None
    return dedent(segment), node, node.lineno, _end_lineno(node)


def calculate_code_metrics(code: str, tree: AST | None = None) -> dict[str, Any]:
    KINDS = AstKind.stmts + AstKind.exprs

    if tree is None:
        tree = ast.parse(code)

    nodes = {kind.metric_label: 0 for kind in KINDS}
    for node in ast.walk(tree):
        if kind := get_stmt_kind(node):
            nodes[kind.metric_label] += 1
        if kind := get_expr_kind(node):
            nodes[kind.metric_label] += 1

    all_nodes = _count_nodes(tree)
    volumes = {}
    if all_nodes > 0:
        volumes = {kind.metric_label: nodes[kind.metric_label] / all_nodes for kind in KINDS}
    else:
        volumes = {kind.metric_label: 0 for kind in KINDS}

    return {
        "len": len(code),
        "lines": line_count(code),
        "cyc_comp": _cyc_comp(tree),
        "nodes": {
            "all": all_nodes,
            **nodes
        },
        "volumes": volumes
    }


def _context_score(node: ast.stmt | ast.expr) -> int:
    return abs((_end_lineno(node) - node.lineno + 1) - _OPTIMAL_CONTEXT_LINES)


def _build_path(parent: AST, start_line: int, end_line: int, path: list[ast.stmt]) -> list[ast.stmt]:
    for child in ast.iter_child_nodes(parent):
        if isinstance(child, ast.stmt) and child.lineno <= start_line and end_line <= _end_lineno(child):
            return _build_path(child, start_line, end_line, [child] + path)
    return path


def _return_context(code: str, node: ast.stmt) -> tuple[str, ast.stmt, int, int]:
    return dedent(extract_range(code, node.lineno, _end_lineno(node))), node, node.lineno, _end_lineno(node)


def _cyc_comp(tree: AST) -> int:
    FORK_NODES = (ast.For, ast.AsyncFor, ast.While, ast.If, ast.match_case, ast.IfExp, ast.And, ast.Or)
    return sum(1 for node in ast.walk(tree) if isinstance(node, FORK_NODES)) + 1


def _count_nodes(tree: AST) -> int:
    count = 0
    for node in ast.walk(tree):
        if (isinstance(node, ast.stmt) and not isinstance(node, ast.Expr)) or isinstance(node, ast.expr):
            count += 1
    return count


def _adjust_decorator_lines(tree: AST) -> None:
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if len(node.decorator_list) == 0:
            continue
        node.lineno = min(d.lineno for d in node.decorator_list)


def _end_lineno(node: ast.stmt | ast.expr) -> int:
    return node.end_lineno if node.end_lineno is not None else node.lineno


class TestAstUtils(TestCase):
    def test_has_syntax_error(self):
        self.assertFalse(has_syntax_error("def f(): pass"))
        self.assertTrue(has_syntax_error("def f():"))
        self.assertTrue(has_syntax_error("def f():\npass"))

    def test_context_score(self):
        self.assertEqual(_context_score(ast.parse("def f(): pass").body[0]), 19)
        self.assertEqual(_context_score(ast.parse("if x == 1:\n\tx += 1\n\tprint(x)").body[0]), 17)

    def test_cyc_comp(self):
        self.assertEqual(_cyc_comp(ast.parse("")), 1)
        self.assertEqual(_cyc_comp(ast.parse("if x == 1: pass")), 2)
        self.assertEqual(_cyc_comp(ast.parse("if x == 1: pass\nelif x == 2: pass")), 3)
        self.assertEqual(_cyc_comp(ast.parse("while True: pass")), 2)

    def test_count_nodes(self):
        self.assertEqual(_count_nodes(ast.parse("")), 0)
        self.assertEqual(_count_nodes(ast.parse("def f(): pass")), 2)
        self.assertEqual(_count_nodes(ast.parse("if x == 1: pass")), 5)

    def test_adjust_decorator_lines(self):
        code = "@dec1\n@dec2\ndef f(): pass\n\n@dec\nclass C: pass\n\ndef g(): pass"
        tree = ast.parse(code)
        f, C, g = tree.body

        self.assertEqual(f.lineno, 3)
        self.assertEqual(C.lineno, 6)
        self.assertEqual(g.lineno, 8)

        _adjust_decorator_lines(tree)

        self.assertEqual(f.lineno, 1)
        self.assertEqual(C.lineno, 5)
        self.assertEqual(g.lineno, 8)
