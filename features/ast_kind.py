from __future__ import annotations
import ast
from ast import AST
from dataclasses import dataclass
from typing import Callable, ClassVar
from unittest import TestCase

# https://docs.python.org/3/library/ast.html


def is_function(n: AST) -> bool: return isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))


def _is_class(n: AST) -> bool: return isinstance(n, ast.ClassDef)


def _is_loop(n: AST) -> bool: return isinstance(n, (ast.For, ast.AsyncFor, ast.While))


def _is_condition(n: AST) -> bool: return isinstance(n, (ast.If, ast.Match, ast.Assert))


def _is_resource(n: AST) -> bool: return isinstance(n, (ast.With, ast.AsyncWith, ast.Try))


def _is_assign(n: AST) -> bool: return isinstance(n, (ast.Assign, ast.AugAssign, ast.AnnAssign, ast.Delete))


def _is_break(n: AST) -> bool: return isinstance(n, (ast.Return, ast.Raise, ast.Break, ast.Continue))


def _is_import(n: AST) -> bool: return isinstance(n, (ast.Import, ast.ImportFrom))


def _is_docstr(n: AST) -> bool:
    return isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str)


def _is_voidexpr(n: AST) -> bool:
    return isinstance(n, ast.Expr) and not _is_docstr(n)


def _is_arith(n: AST) -> bool: return isinstance(n, (ast.Add, ast.Sub, ast.Mult,
                                                     ast.MatMult, ast.Div, ast.Mod, ast.Pow, ast.FloorDiv, ast.UAdd, ast.USub))


def _is_logic(n: AST) -> bool: return isinstance(n, (ast.And, ast.Or, ast.Not))


def _is_comp(n: AST) -> bool: return isinstance(n, (ast.Eq, ast.NotEq,
                                                    ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.Is, ast.IsNot))


def _is_call(n: AST) -> bool: return isinstance(n, ast.Call)


def _is_literal(n: AST) -> bool: return isinstance(n, ast.Constant)


@dataclass(frozen=True)
class AstKind:
    name: str
    predicate: Callable[[AST], bool]
    metric_label: str

    stmts: ClassVar[list[AstKind]]
    exprs: ClassVar[list[AstKind]]


AstKind.stmts = [
    AstKind("FUNCTION", is_function, "functions"),
    AstKind("CLASS", _is_class, "classes"),
    AstKind("LOOP", _is_loop, "loops"),
    AstKind("CONDITION", _is_condition, "conditions"),
    AstKind("RESOURCE", _is_resource, "resources"),
    AstKind("ASSIGN", _is_assign, "assigns"),
    AstKind("BREAK", _is_break, "breaks"),
    AstKind("IMPORT", _is_import, "imports"),
    AstKind("DOCSTR", _is_docstr, "docstrs"),
    AstKind("VOIDEXPR", _is_voidexpr, "voidexprs"),
]

AstKind.exprs = [
    AstKind("ARITH", _is_arith, "ariths"),
    AstKind("LOGIC", _is_logic, "logics"),
    AstKind("COMP", _is_comp, "comps"),
    AstKind("CALL", _is_call, "calls"),
    AstKind("LITERAL", _is_literal, "literals"),
]


def get_stmt_kind(node: AST) -> AstKind | None:
    return next((kind for kind in AstKind.stmts if kind.predicate(node)), None)


def get_expr_kind(node: AST) -> AstKind | None:
    return next((kind for kind in AstKind.exprs if kind.predicate(node)), None)


class TestAstKind(TestCase):
    def test_get_stmt_kind(self):
        def assert_kind(text, kind): return self.assertEqual(get_stmt_kind(ast.parse(text).body[0]).name, kind)

        assert_kind("def f(): pass", "FUNCTION")
        assert_kind("class C: pass", "CLASS")
        assert_kind("for i in range(3): pass", "LOOP")
        assert_kind("if True: pass", "CONDITION")
        assert_kind("with open('f') as f: pass", "RESOURCE")
        assert_kind("a = 1", "ASSIGN")
        assert_kind("break", "BREAK")
        assert_kind("import os", "IMPORT")
        assert_kind('"""doc"""', "DOCSTR")
        assert_kind("1", "VOIDEXPR")

    def test_get_expr_kind(self):
        def assert_kind(text, kind):
            count = 0
            for node in ast.walk(ast.parse(text)):
                if (k := get_expr_kind(node)) and k.name == kind:
                    count += 1
            self.assertEqual(count, 1)

        assert_kind("1 + 2", "ARITH")
        assert_kind("not True", "LOGIC")
        assert_kind("1 == 2", "COMP")
        assert_kind("f()", "CALL")
        assert_kind("1", "LITERAL")
