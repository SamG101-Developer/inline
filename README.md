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
perform all the inlining.

## Decorators:

- `@inline` - This decorator will inline the function into the caller. It will replace the function call with the
  function body, and replace any arguments with the values passed in. The function must be defined in the same module as
  it is called from.
- `@inline_cls` - This decorator causes all `self.` method calls to be devirtualized, allowing for `@inline` class
  methods to be inlined properly. Without the `@inline_cls`, no class methods can be inlined.

## AST replacement

Three nodes are checked:
- `Expr`: handles inner `Call`
- `Assign`: handles rhs `Call`, place return value into target
- `Return`: handles value `Call`, returns returned value

## Results

Disassembly of the code will show that the function has been inlined into the caller.

## Known restrictions

- Replacements only happen within the module the function is defined in. This means that if the function is
  imported from another module, it will not be replaced.
- Inlining nested functions are not supported, because recursive checks are not done yet.
- Inlining nested classes' methods are not supported, because recursive checks are not done yet.
- Other usages of the function (in conditions, walrus operators, etc) are not supported yet.