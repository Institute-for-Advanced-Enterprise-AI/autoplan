from pydantic import BaseModel, Field

from autoplan.models import Plan


class ExecutionContext(BaseModel):
    plan_class: type[Plan]
    tools: list
    output_model: type[BaseModel]
    planning_llm_model: str = "gpt-4o-mini"
    planning_llm_args: dict = Field(default_factory=dict)
    step_llm_model: str = "gpt-4o-mini"
    step_llm_args: dict = Field(default_factory=dict)
    summary_llm_model: str = "gpt-4o-mini"
    summary_llm_args: dict = Field(default_factory=dict)
    application_args: dict = Field(default_factory=dict)
