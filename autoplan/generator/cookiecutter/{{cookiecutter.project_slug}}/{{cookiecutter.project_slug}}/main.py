from pydantic import BaseModel, Field

from autoplan import Plan, Step, with_planning
from {{cookiecutter.project_slug}}.tools.you_search import you_search




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
    [% for output, type in config.outputs.items() %]
    [[output]]: [[type]]
    [% endfor %]

    display_title: str = Field(description="A short title that summarizes the output to be displayed in the UI.")

tools = [
    you_search,
]



def generate_plan(execution_context, application_args) -> list[str]:
    return [
        "[[config.generating_plan_prompt]]",
        [% for input in config.inputs %]
        application_args["[[input]]"],
        [% endfor %]
    ]

def combine_steps(execution_context, plan: ApplicationPlan, steps: list[ApplicationStep]) -> list[str]:
    return [
        "[[config.combining_steps_prompt]]",
        str(steps),
    ]

@with_planning(
    step_class=ApplicationStep,
    plan_class=ApplicationPlan,
    tools=tools,
    generate_plan_prompt_generator=generate_plan,
    combine_steps_prompt_generator=combine_steps,
)
async def run([% for input, type in config.inputs.items() %]
    [[input]]: [[type]],
    [% endfor %]) -> ApplicationOutput:
    pass
