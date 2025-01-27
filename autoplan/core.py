import asyncio
import functools
import inspect
from functools import wraps
from typing import Callable, TypeVar

from dotenv import load_dotenv
from pydantic import BaseModel

from autoplan.execution_context import ExecutionContext
from autoplan.func_utils import with_name
from autoplan.models import Plan, Step, create_plan_class
from autoplan.phases.combine_steps import combine_steps
from autoplan.phases.generate_plan import generate_plan
from autoplan.results import (
    ExecutionResult,
    FinalResult,
    PartialPlanResult,
    PlanResult,
    StepResult,
)
from autoplan.tool import PriorToolResult, Tool, tool
from autoplan.trace import trace

load_dotenv()

# whatever arguments that are used by the function that is decorated using @with_planning
ApplicationArgsVar = TypeVar("ApplicationArgsVar", bound=dict)

GeneratePlanPromptGenerator = Callable[
    [ExecutionContext, ApplicationArgsVar], list[str]
]


PlanVar = TypeVar("PlanVar", bound=Plan)

CombineStepsPromptGenerator = Callable[
    [ExecutionContext, PlanVar, list[str]], list[str]
]


class StepDependencies:
    def __init__(self):
        self.step_results_by_index = {}

    def add_step_result(self, step_result: StepResult, index: int):
        self.step_results_by_index[index] = step_result

    def substitute_with_dependencies(self, step: Step) -> Step | None:
        args = {}
        for key, arg in step.tool_call.__dict__.items():
            if isinstance(arg, PriorToolResult):
                if arg.step_index_zero_indexed not in self.step_results_by_index:
                    # early return indicating that the step is not ready to be executed
                    return None

                # substitute the prior tool result with the result of the step
                args[key] = self.step_results_by_index[
                    arg.step_index_zero_indexed
                ].result
            else:
                args[key] = arg
        return step.model_copy(
            update={"tool_call": step.tool_call.__class__.model_validate(args)}
        )


@trace
async def _execute[P: Plan, S: Step](
    context: ExecutionContext,
    generate_plan_prompt_generator: GeneratePlanPromptGenerator,
    combine_steps_prompt_generator: CombineStepsPromptGenerator,
    application_args: dict,
    # using a queue instead of an async generator because Weave doesn't work well with async generators
    queue: asyncio.Queue,
    generate_plan_temperature: float,
    combine_steps_temperature: float,
) -> BaseModel:
    generate_plan_prompt = trace(
        with_name(generate_plan_prompt_generator, "generate_plan_prompt")
    )(context, application_args)

    generate_plan_queue: asyncio.Queue[Plan | None] = asyncio.Queue()

    asyncio.create_task(
        generate_plan(
            context,
            generate_plan_prompt,
            generate_plan_temperature,
            generate_plan_queue,
        )
    )

    plan: Plan | None = None

    while True:
        item = await generate_plan_queue.get()
        if item is None:
            break
        else:
            plan = item
            queue.put_nowait(PartialPlanResult(result=item))

    # this is guaranteed by the generate_plan function
    if plan is None:
        raise ValueError("No plan was generated")
    queue.put_nowait(PlanResult(result=plan))

    step_dependencies = StepDependencies()

    async def execute_step_with_result(step: Step, index: int):
        while True:
            if subbed_step := step_dependencies.substitute_with_dependencies(step):
                step = subbed_step
                result = await _execute_step(context, step)
                step_result = StepResult(step=step, result=result)

                step_dependencies.add_step_result(step_result, index)
                queue.put_nowait(step_result)
                return step_result
            else:
                # wait for dependencies to be ready
                await asyncio.sleep(0.1)

    tasks = [
        execute_step_with_result(step, index)
        for index, step in enumerate(plan.steps or [])
    ]
    step_results = await asyncio.gather(*tasks)

    combine_steps_prompt = trace(
        with_name(combine_steps_prompt_generator, "combine_steps_prompt")
    )(context, plan, [r.result for r in step_results])

    result = await combine_steps(
        context, combine_steps_prompt, combine_steps_temperature
    )

    queue.put_nowait(FinalResult(result=result))

    return ExecutionResult(
        result=result, plan=plan, step_results=[r for r in step_results if r]
    )


@trace
async def _execute_step(context: ExecutionContext, step: Step):
    try:
        return await step.tool_call()
    except Exception as e:
        print(f"Error executing step {step}: {e}")
        return "Error executing step"


def _from_planned(f):
    """
    Turns a "with_planning" decorated function into a tool, by:
    a) Creating a function that returns the final result
    b) Decorating it with @tool
    """

    @tool
    @wraps(f)
    async def inner(*args, **kwargs):
        async for r in f(*args, **kwargs):
            if isinstance(r, FinalResult):
                return r.result

    return inner


_WITH_PLANNING_ATTR = "__withplanning__"


def with_planning(
    step_class: type[Step],
    plan_class: type[Plan],
    generate_plan_prompt_generator: GeneratePlanPromptGenerator,
    combine_steps_prompt_generator: CombineStepsPromptGenerator,
    tools: list[type[Tool]],
    generate_plan_temperature: float = 0.0,
    combine_steps_temperature: float = 0.0,
    generate_plan_llm_model: Optional[str] = None,
    combine_steps_llm_model: Optional[str] = None,
    generate_plan_llm_args: Optional[dict] = None,
    combine_steps_llm_args: Optional[dict] = None,
):
    """
    Decorator to add planning to a function.

    step_class: The class for a step in the plan.
    plan_class: The class for the plan.
    generate_plan_prompt_generator: A function that generates the prompt for the plan.
    combine_steps_prompt_generator: A function that generates the prompt for combining the steps.
    tools: The tools that can be used in the plan.
    generate_plan_temperature: The temperature for the generate plan prompt.
    combine_steps_temperature: The temperature for the combine steps prompt.
    generate_plan_llm_model: The model to use for the generate plan prompt.
    combine_steps_llm_model: The model to use for the combine steps prompt.
    generate_plan_llm_args: The arguments to pass to the generate plan prompt.
    combine_steps_llm_args: The arguments to pass to the combine steps prompt.
    """

    def wrapper(func):
        function_return_type = func.__annotations__.get("return")
        func_signature = inspect.signature(func)

        updated_tools = [
            # if the tool has the WITH_PLANNING_ATTR, then we need to wrap it in a from_planned function
            _from_planned(tool)
            if hasattr(tool, _WITH_PLANNING_ATTR)
            # otherwise, we expect it to be a tool
            else tool
            for tool in tools
        ]

        for tool in updated_tools:
            if not issubclass(tool, Tool):
                raise ValueError(f"{tool} is not a Tool. Was it decorated with @tool?")

        # These annotations will create a trace whose name and arguments come from the decorated function
        @functools.wraps(func)
        async def wrapped(*args, **kwargs):
            arguments = func_signature.bind(*args, **kwargs).arguments

            queue = asyncio.Queue()

            context = ExecutionContext(
                plan_class=create_plan_class(step_class, plan_class, updated_tools),
                tools=tools,
                output_model=function_return_type,
                application_args=arguments,
                generate_plan_llm_model=generate_plan_llm_model,
                generate_plan_llm_args=generate_plan_llm_args,
                combine_steps_llm_model=combine_steps_llm_model,
                combine_steps_llm_args=combine_steps_llm_args,
            )

            # start the execution in the background
            asyncio.create_task(
                _execute(
                    context,
                    generate_plan_prompt_generator,
                    combine_steps_prompt_generator,
                    arguments,
                    queue,
                    generate_plan_temperature,
                    combine_steps_temperature,
                )
            )

            # yield each item from the queue as it comes in
            while True:
                item = await queue.get()
                yield item

                if isinstance(item, FinalResult):
                    return

        # add a marker so we can identify the function as a "with_planning" decorated function
        setattr(wrapped, _WITH_PLANNING_ATTR, True)
        return wrapped

    return wrapper
