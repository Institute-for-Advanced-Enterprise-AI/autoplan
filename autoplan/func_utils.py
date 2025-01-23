import types
from typing import Callable


def with_name(original_func: Callable, new_name: str) -> Callable:
    """
    Decorator to change the name of a function.
    """
    return types.FunctionType(
        original_func.__code__,
        original_func.__globals__,
        name=new_name,
        argdefs=original_func.__defaults__,
        closure=original_func.__closure__,
    )
