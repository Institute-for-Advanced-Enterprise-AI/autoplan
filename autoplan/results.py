from pydantic import BaseModel

from autoplan.models import Plan, Step


class Result(BaseModel):
    """
    A result of a step or plan.
    """


class PartialPlanResult[Plan: BaseModel](Result):
    """
    An unfinished plan (e.g. a plan that is in the process of being generated).
    """

    result: Plan


class PlanResult[Plan: BaseModel](Result):
    """
    A finished plan.
    """

    result: Plan


class StepResult(Result):
    """
    A result of a step.
    """

    step: Step
    result: BaseModel | str | None


class FinalResult[Output: BaseModel](Result):
    """
    A final result of the application.
    """

    result: Output


class ExecutionResult[Output: BaseModel](Result):
    """
    A result of executing a plan, including the final result and the generated plan and step results.
    """

    result: Output
    plan: Plan
    step_results: list[StepResult]
