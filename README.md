# Inline

This repository contains a simple `inline` decorator, that allows for the called function to be moved into the caller
before the code is run. It uses an import hook and the `ast` module to inject the code. A simple argument-parameter
match and replace is done to allow any variables to be used as arguments to the function.

## Running

A `run.py` or similar runner file will need to be created. This must contains 2 lines of code:

```python
import inline.inline_hook
import main
```

In this example, `main` is the entry module for the program. The `inline_hook` module will be imported first, and will
perform all the inlining. See the other [examples](./example) for the file structure.

## Decorators

- `@inline` - This decorator will inline the function into the caller. It will replace the function call with the
  function body, and replace any arguments with the values passed in. The function must be defined in the same module as
  it is called from.
- `@inline_cls` - This decorator causes all `self.` method calls to be devirtualized, allowing for `@inline` class
  methods to be inlined properly. Without the `@inline_cls`, no class methods can be inlined.

## AST replacement

### Functions

```python
from inline.inline_runtime import inline

@inline
def func(a, b):
    return a + b
```

The following three asts are checked:

- `Expr`: handles inner `Call`, such as `func(1, 2)`
- `Assign`: handles rhs `Call`, place return value into target, such as `a = func(3, 4)`
- `Return`: handles value `Call`, returns returned value, such as `return func(5, 6)`

### Methods

```python
from inline.inline_runtime import inline, inline_cls

@inline_cls
class MyClass:
    def __init__(self, a):
        self.a = a

    @inline
    def func(self, b):
        return self.a + b

    def test(self):
        return self.func(1)
```

When a class is decorated as `@inline_cls`, all `self.` method calls are devirtualized. This allows methods identified
by `Type.name` to be matched and inlined. This [example](./example/method_based_inline) shows how to use this feature.
In the example, `self.func(1)` is translated to `MyClass.func(self, 1)`, which allows the function to be inlined as
`self.a + 1`.

## Known restrictions

- Free function replacements only occur in the same module.
- Method replacements only occur from inside the same class.
- Inlining nested functions are not supported, because recursive checks are not done yet.
- Inlining nested classes' methods are not supported, because recursive checks are not done yet.
- Other usages of the function (in walrus operators, etc) are not supported yet.