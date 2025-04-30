import ast
import copy
import importlib.abc
import importlib.machinery
import importlib.util
import sys
import types
from typing import Dict, Optional, Sequence


class InlineTransformer(ast.NodeTransformer):
    _inline_funcs: Dict[str, ast.FunctionDef]

    def __init__(self, inline_funcs: Dict[str, ast.FunctionDef]) -> None:
        self._inline_funcs = inline_funcs

    def visit_Expr(self, node: ast.Expr) -> ast.AST:
        self.generic_visit(node)

        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id in self._inline_funcs:
            func_def = self._inline_funcs[node.value.func.id]
            param_map = {param.arg: arg for param, arg in zip(func_def.args.args, node.value.args)}
            new_body = []

            for stmt in func_def.body:
                inline_stmt = self._replace(copy.deepcopy(stmt), param_map)
                inline_stmt = ast.copy_location(inline_stmt, stmt)
                new_body.append(inline_stmt)

            return new_body
        return node

    def visit_Assign(self, node: ast.Assign) -> ast.AST:
        # Special version where the return statement's value from the target function is used as the assignment target.
        self.generic_visit(node)

        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id in self._inline_funcs:
            func_def = self._inline_funcs[node.value.func.id]
            param_map = {param.arg: arg for param, arg in zip(func_def.args.args, node.value.args)}
            new_body = []

            for stmt in func_def.body:
                inline_stmt = self._replace(copy.deepcopy(stmt), param_map)
                inline_stmt = ast.copy_location(inline_stmt, stmt)
                new_body.append(inline_stmt)

            if isinstance(ret_stmt := new_body[-1], ast.Return):
                assign_stmt = ast.Assign(targets=node.targets, value=ret_stmt.value)
                assign_stmt = ast.copy_location(assign_stmt, func_def.body[-1])
                new_body[-1] = assign_stmt

            return new_body
        return node

    def _replace(self, node: ast.AST, param_map: Dict[str, ast.expr]) -> ast.AST:
        if isinstance(node, ast.Name) and node.id in param_map:
            return param_map[node.id]

        # Recursively replace in all child nodes
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, ast.AST):
                        value[i] = self._replace(item, param_map)
            elif isinstance(value, ast.AST):
                setattr(node, field, self._replace(value, param_map))
        return node


class InlineLoader(importlib.abc.Loader):
    _fullname: str
    _path: str

    def __init__(self, fullname: str, path: str) -> None:
        self._fullname = fullname
        self._path = path

    def create_module(self, spec: importlib.machinery.ModuleSpec) -> types.ModuleType:
        return None

    def exec_module(self, module: types.ModuleType) -> None:
        with open(self._path, "r") as f:
            source = f.read()

        tree = ast.parse(source)

        inline_funcs = {}
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Name) and decorator.id == "inline":
                        inline_funcs[node.name] = node

        if inline_funcs:
            transformer = InlineTransformer(inline_funcs)
            tree = transformer.visit(tree)
            ast.fix_missing_locations(tree)

        tree = ast.fix_missing_locations(tree)
        code = compile(tree, filename=self._path, mode="exec")
        exec(code, module.__dict__)


class InlineFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname: str, path: Sequence[str], target: Optional[types.ModuleType] = ..., /) -> Optional[importlib.machinery.ModuleSpec]:
        spec = importlib.machinery.PathFinder.find_spec(fullname)
        if spec and spec.origin and spec.origin != "built-in" and spec.origin.endswith(".py"):
            spec.loader = InlineLoader(fullname, spec.origin)
            return spec
        return None


sys.meta_path.insert(0, InlineFinder())
