import inspect
import pydoc
from collections import OrderedDict
from functools import wraps
from typing import Any, Callable, Literal

from pydantic import BaseModel, Field, create_model

from autoplan.dependency import Dependency
from autoplan.trace import trace


class Tool(BaseModel):
    """
    A tool that can be used in a plan.
    """

    type: str

    async def __call__(self) -> object:
        pass


TYPE_FIELD = "type"


class PriorToolResult(BaseModel):
    """
    A reference to a prior tool result.
    """

    step_index_zero_indexed: int


def _function_to_tool_subclass(
    func: Callable[..., Any], can_use_prior_results: bool | None = None
) -> type[Tool]:
    signature = inspect.signature(func)
    fields = OrderedDict()

    # add a "type" field to the model to be used as a discriminator
    fields[TYPE_FIELD] = (Literal[func.__name__], Field(default=func.__name__))
    fields.update(
        {
            name: (
                param.annotation | PriorToolResult,
                ... if param.default is inspect.Parameter.empty else param.default,
            )
            if can_use_prior_results
            else (
                param.annotation,
                ... if param.default is inspect.Parameter.empty else param.default,
            )
            for name, param in signature.parameters.items()
            if param.annotation != inspect.Parameter.empty
            and not isinstance(param.default, Dependency)
        }
    )

    doc = pydoc.getdoc(func)
    name = "".join(word.capitalize() for word in func.__name__.split("_"))
    model = create_model(name, **fields, __base__=Tool)
    model.__doc__ = doc.strip()

    async def call(self):
        kwargs = {}
        for name, value in self.model_dump().items():
            if name != TYPE_FIELD:
                kwargs[name] = getattr(self, name)

        return await func(**kwargs)

    model.__call__ = call

    return model


def tool(
    f: Callable[..., Any] | None = None,
    can_use_prior_results: bool | None = None,
) -> type[Tool]:
    """
    Decorator to create a tool from a function.

    Can be called either as:
    @tool
    def my_tool(arg: str) -> str:
        ...

    or as:
    @tool()
    def my_tool(arg: str) -> str:
        ...


    if @tool(can_use_prior_results=True)
    def my_tool(arg: str) -> str:
        ...
    then "arg" could be the result of a prior tool, if specified by the plan
    """
    if f is None:

        @wraps(tool)
        def decorator(f: Callable[..., Any]) -> type[Tool]:
            return tool(f, can_use_prior_results)

        return decorator  # type: ignore
    else:
        if not inspect.iscoroutinefunction(f):
            raise ValueError("Tool functions must be asynchronous")
        cls = _function_to_tool_subclass(trace(f), can_use_prior_results)
        return cls
