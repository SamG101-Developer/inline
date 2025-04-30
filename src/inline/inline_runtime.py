from typing import Callable


def inline(func: Callable) -> Callable:
    func.__inline__ = True
    return func
