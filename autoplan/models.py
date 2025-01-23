from typing import Annotated, Sequence, Union

from pydantic import BaseModel, Field

from autoplan.tool import TYPE_FIELD, Tool


class Step(BaseModel):
    """
    A step in the plan, using a specific tool.
    """

    tool_call: Tool


class Plan(BaseModel):
    """
    A plan for achieving the application's goal, composed of steps.
    """

    rationale: str = Field(
        description="Layout a detailed rationale for the plan, detailing step by step the tools that should be called, where their inputs should come from, and how the results can be used."
    )
    steps: Sequence[Step]


def create_plan_class(
    step_class: type[Step],
    plan_class: type[Plan],
    tools: list[type[Tool]],
):
    """
    Create a plan class with the specific tool calls.
    """

    # redefine Step with the specific tool calls
    class Step(step_class):
        """
        A step in the plan.
        """

        tool_call: Annotated[Union[tuple(tools)], Field(discriminator=TYPE_FIELD)] = (  # type: ignore
            Field(description="The tool call to be made for the current step.")
        )

    # redefine Plan with the specific Step class
    class Plan(plan_class):
        """
        A plan for achieving the application's goal, composed of steps.
        """

        steps: Sequence[Step] = Field(  # type: ignore
            description="The list of steps that make up this plan."
        )

    return Plan
