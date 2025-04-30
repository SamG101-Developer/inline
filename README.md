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

## AST replacement

Two nodes are checked: `Expr` nodes, and `Assign` nodes. This is because for multi-line functions, analysing the `Call`
node does not allow for multiple statements to be returned in place. Instead, the `Expr` node is checked whether is
internally contains a `Call` node. The `Assign` node is checked so that if the inlined function returns a value, it can
be mapped into the assignment value. This is shows in the example.

## Results

Disassembly of the code will show that the function has been inlined into the caller.

## Known restrictions

- Replacements only happen within the module the function is defined in. This means that if the function is
  imported from another module, it will not be replaced.
