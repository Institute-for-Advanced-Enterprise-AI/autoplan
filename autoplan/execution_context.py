from pydantic import BaseModel, Field

from autoplan.models import Plan


class ExecutionContext(BaseModel):
    plan_class: type[Plan]
    tools: list
    output_model: type[BaseModel]
    generate_plan_llm_model: str = "gpt-4o-mini"
    generate_plan_llm_args: dict = Field(default_factory=dict)
    combine_steps_llm_model: str = "gpt-4o-mini"
    combine_steps_llm_args: dict = Field(default_factory=dict)
    application_args: dict = Field(default_factory=dict)
