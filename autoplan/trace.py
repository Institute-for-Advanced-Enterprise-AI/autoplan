from abc import ABC, abstractmethod
from functools import wraps
from typing import Any, Callable

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class ManualCall(BaseModel):
    name: str
    inputs: dict
    end: Callable[[Any], None]


class Tracer(ABC):
    @abstractmethod
    def create_call(self, name: str, inputs: dict) -> ManualCall:
        pass

    @abstractmethod
    def trace(self, f: Callable) -> Callable:
        pass


class WeaveTracer(Tracer):
    def __init__(self, project_id: str):
        import weave  # pyright: ignore[reportMissingImports]

        self.client = weave.init(project_id)

    def create_call(self, name: str, inputs: dict):
        call = self.client.create_call(op=name, inputs=inputs)
        return ManualCall(
            name=name,
            inputs=inputs,
            end=lambda output: self.client.finish_call(call, output=output),
        )

    def trace(self, f: Callable) -> Callable:
        import weave  # pyright: ignore[reportMissingImports]

        return weave.op()(f)


_tracer = None


def set_tracer(tracer: Tracer):
    global _tracer
    _tracer = tracer


def get_tracer():
    return _tracer


def trace(f):
    @wraps(f)
    def inner(*args, **kwargs):
        tracer = get_tracer()
        if tracer:
            return tracer.trace(f)(*args, **kwargs)
        else:
            return f(*args, **kwargs)

    return inner
