import ast
import copy
import importlib.abc
import importlib.machinery
import importlib.util
import sys
import types
from typing import Dict, Optional, Sequence


class DevirtualizeMethodCallsTransformer(ast.NodeTransformer):
    _cls_name: str

    def __init__(self, cls_name: str) -> None:
        self._cls_name = cls_name

    def visit_Call(self, node: ast.Call) -> ast.AST:
        self.generic_visit(node)

        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == "self":
            method_name = node.func.attr
            new_func = ast.Attribute(
                value=ast.Name(id=self._cls_name, ctx=ast.Load()),
                attr=method_name,
                ctx=ast.Load())
            new_args = [ast.Name(id="self", ctx=ast.Load())] + node.args
            new_call = ast.Call(func=new_func, args=new_args, keywords=node.keywords)
            new_call = ast.copy_location(new_call, node)
            return new_call
        return node


class InlineTransformer(ast.NodeTransformer):
    _inline_funcs: Dict[str, ast.FunctionDef]

    def __init__(self, inline_funcs: Dict[str, ast.FunctionDef]) -> None:
        self._inline_funcs = inline_funcs

    def visit_Expr(self, node: ast.Expr) -> ast.AST:
        self.generic_visit(node)

        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name):
            func_name = self._get_func_name(node.value)
            if func_name in self._inline_funcs:
                func_def = self._inline_funcs[func_name]
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

        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name | ast.Attribute):
            func_name = self._get_func_name(node.value)
            if func_name in self._inline_funcs:
                func_def = self._inline_funcs[func_name]
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

    def _get_func_name(self, call_node: ast.Call) -> Optional[str]:
        if isinstance(call_node.func, ast.Name):
            return call_node.func.id
        elif isinstance(call_node.func, ast.Attribute) and isinstance(call_node.func.value, ast.Name):
            return f"{call_node.func.value.id}.{call_node.func.attr}"
        return None

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
            # Free functions
            if isinstance(node, ast.FunctionDef):
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Name) and decorator.id == "inline":
                        print("Registering inline function:", node.name)
                        inline_funcs[node.name] = node

            # Class methods
            elif isinstance(node, ast.ClassDef) and "inline_cls" in [d.id for d in node.decorator_list]:
                cls_name = node.name
                devirt = DevirtualizeMethodCallsTransformer(cls_name)
                node.body = [devirt.visit(item) for item in node.body]

                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        for decorator in item.decorator_list:
                            if isinstance(decorator, ast.Name) and decorator.id == "inline":
                                print("Registering inline method:", f"{node.name}.{item.name}")
                                inline_funcs[f"{node.name}.{item.name}"] = item

        if inline_funcs:
            transformer = InlineTransformer(inline_funcs)
            tree = transformer.visit(tree)
            ast.fix_missing_locations(tree)

        tree = ast.fix_missing_locations(tree)
        code = compile(tree, filename=self._path, mode="exec")
        exec(code, module.__dict__)


class InlineFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname: str, path: Sequence[str], target: Optional[types.ModuleType] = ..., /) -> Optional[importlib.machinery.ModuleSpec]:
        spec = importlib.machinery.PathFinder.find_spec(fullname, path)

        # Non-spec modules or non-python files are skipped.
        if not spec or not spec.origin or not spec.origin.endswith(".py"):
            return None

        # Built in libraries are skipped.
        elif spec.origin.startswith(sys.base_prefix):
            return None

        # Otherwise, load the module with the InlineLoader.
        else:
            spec.loader = InlineLoader(fullname, spec.origin)
            return spec


sys.meta_path.insert(0, InlineFinder())
