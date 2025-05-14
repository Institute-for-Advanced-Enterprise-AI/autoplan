from asyncio import Queue

from autoplan.execution_context import ExecutionContext
from autoplan.llm_utils.create_partial_streaming_completion import (
    create_partial_streaming_completion,
)
from autoplan.models import Plan
from autoplan.trace import trace
from litellm import acompletion


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
    response = await acompletion(
        model=context.generate_plan_llm_model,
        messages=messages,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "schema": context.plan_class.model_json_schema(),
                "name": context.plan_class.__name__,
            },
        },
        **context.generate_plan_llm_args,
        temperature=temperature,
    )

    queue.put_nowait(context.plan_class.model_validate_json(response.choices[0].message.content))
    queue.put_nowait(None)
    return context.plan_class.model_validate_json(response.choices[0].message.content)
