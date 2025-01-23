from asyncio import Queue

from autoplan.execution_context import ExecutionContext
from autoplan.llm_utils.create_partial_streaming_completion import (
    create_partial_streaming_completion,
)
from autoplan.models import Plan
from autoplan.trace import trace


@trace
async def generate_plan(
    context: ExecutionContext,
    prompts: list[str],
    temperature: float,
    queue: Queue[Plan | None],
):
    """
    Generate a plan for achieving the application's goal using steps that use the provided tools.
    """
    messages = []

    for index, prompt in enumerate(prompts):
        messages.append(
            {
                "role":
                # use "system" for the first message, and "user" for the rest
                "user" if index > 0 else "system",
                "content": prompt,
            }
        )

    response = create_partial_streaming_completion(
        model=context.planning_llm_model,
        messages=messages,
        response_format=context.plan_class,
        **context.planning_llm_args,
        temperature=temperature,
    )

    item = None

    async for item in response:
        queue.put_nowait(item)

    # signal the end of the plan generation
    queue.put_nowait(None)

    return item
