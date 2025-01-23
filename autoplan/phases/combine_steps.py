from litellm import acompletion
from litellm.types.utils import Choices, ModelResponse
from pydantic import BaseModel

from autoplan.execution_context import ExecutionContext
from autoplan.trace import trace


@trace
async def combine_steps(
    context: ExecutionContext,
    prompts: list[str],
    temperature: float,
) -> BaseModel:
    """
    Combine the steps into a final result.
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
        model=context.summary_llm_model,
        messages=messages,
        **context.summary_llm_args,
        temperature=temperature,
        response_format=context.output_model,
    )

    # asserts are for type checking, and reflect invariants we expect from the acompletion function
    assert isinstance(response, ModelResponse)
    choice = response.choices[0]
    assert isinstance(choice, Choices)
    assert choice.message.content

    return context.output_model.model_validate_json(choice.message.content)
