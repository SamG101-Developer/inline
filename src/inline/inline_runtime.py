from typing import Callable


def inline(func: Callable) -> Callable:
    func.__inline__ = True
    return func


def inline_cls[T](cls: T) -> T:
    cls.__inline__ = True
    return cls
