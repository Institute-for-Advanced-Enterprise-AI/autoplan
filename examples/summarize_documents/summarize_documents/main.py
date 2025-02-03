from pydantic import BaseModel, Field
from summarize_documents.tools.you_search import you_search

from autoplan import Plan, Step, with_planning


class ApplicationStep(Step):
    rationale: str = Field(
        description="Layout a detailed rationale for the current step. Explain why it is important and how it contributes to the overall plan. Be objective, don't make up any information, don't rely on your general knowledge."
    )
    objective: str = Field(
        description="Describe the objective of the current step in a single sentence. Start each objective with a verb."
    )


class ApplicationPlan(Plan):
    steps: list[ApplicationStep] = Field(
        description="The list of steps that make up this plan."
    )


class ApplicationOutput(BaseModel):
    summary: str

    display_title: str = Field(
        description="A short title that summarizes the output to be displayed in the UI."
    )


tools = [
    you_search,
]


def generate_plan(execution_context, application_args) -> list[str]:
    messages = [
        "Use the you_search tool to search for information about the topic. Then use the results to summarize each document in the context of the topic."
    ]
    for i in range(3):
        key = f"document{i+1}"
        if key in application_args and application_args[key]:
            messages.append(f"{key}: {application_args[key]}")
    return messages


def combine_steps(
    execution_context, plan: ApplicationPlan, steps: list[ApplicationStep]
) -> list[str]:
    return [
        "Combine the individual summaries and context discussions into a cohesive final summary.",
        str(steps),
        str(execution_context.application_args),
    ]


@with_planning(
    step_class=ApplicationStep,
    plan_class=ApplicationPlan,
    tools=tools,
    generate_plan_prompt_generator=generate_plan,
    combine_steps_prompt_generator=combine_steps,
)
async def run(
    document1: str,
    document2: str,
    document3: str,
) -> ApplicationOutput:
    pass
