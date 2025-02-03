from pydantic import BaseModel, Field
from story_generator.tools.you_search import you_search

from autoplan import Plan, Step, with_planning


class CharacterPlanStep(Step):
    rationale: str = Field(
        description="Layout a detailed rationale for the current step. Explain why it is important and how it contributes to the overall plan. Be objective, don't make up any information, don't rely on your general knowledge."
    )
    objective: str = Field(
        description="Describe the objective of the current step in a single sentence. Start each objective with a verb."
    )


class CharacterPlan(Plan):
    steps: list[CharacterPlanStep] = Field(
        description="The list of steps that make up this plan."
    )


def generate_plan(execution_context, application_args) -> list[str]:
    return [
        "Research the character, using web search",
        application_args["character_request"],
    ]


class CharacterOutput(BaseModel):
    character_name: str
    character_description: str


def combine_steps(
    execution_context, plan: CharacterPlan, steps: list[CharacterPlanStep]
) -> list[str]:
    return [
        "Produce a character name and description",
        str(steps),
    ]


@with_planning(
    step_class=CharacterPlanStep,
    plan_class=CharacterPlan,
    tools=[you_search],
    generate_plan_prompt_generator=generate_plan,
    combine_steps_prompt_generator=combine_steps,
)
async def create_character(
    character_request: str,
) -> CharacterOutput:
    pass


class StoryPlanStep(Step):
    rationale: str = Field(
        description="Layout a detailed rationale for the current step. Explain why it is important and how it contributes to the overall plan. Be objective, don't make up any information, don't rely on your general knowledge."
    )
    objective: str = Field(
        description="Describe the objective of the current step in a single sentence. Start each objective with a verb."
    )


class StoryPlan(Plan):
    steps: list[StoryPlanStep] = Field(
        description="The list of steps that make up this plan."
    )


class StoryOutput(BaseModel):
    story_text: str

    display_title: str = Field(
        description="A short title that summarizes the output to be displayed in the UI."
    )


tools = [
    you_search,
]


def generate_plan(execution_context, application_args) -> list[str]:
    return [
        "Given a story description, request descriptions for some characters",
        application_args["story_description"],
    ]


def combine_steps(
    execution_context, plan: StoryPlan, steps: list[StoryPlanStep]
) -> list[str]:
    return [
        "How would you combine different story elements into a coherent and engaging narrative?",
        str(steps),
    ]


@with_planning(
    step_class=StoryPlanStep,
    plan_class=StoryPlan,
    tools=[create_character],
    generate_plan_prompt_generator=generate_plan,
    combine_steps_prompt_generator=combine_steps
)
async def run(
    story_description: str,
) -> StoryOutput:
    pass
