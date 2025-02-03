import http.client
import json
import os
from typing import Literal

from jinja2 import Environment
from pydantic import BaseModel, Field


class Tool:
    name: str


class ApplicationConfig(BaseModel):
    inputs: dict[str, Literal["str", "int"]]
    outputs: dict[str, Literal["str", "int"]]

    generating_plan_prompt: str = Field(
        description="A prompt for generating a plan for the application."
    )
    combining_steps_prompt: str = Field(
        description="A prompt for combining steps into a final output."
    )


OPENAI_URL = "api.openai.com"


def generate_application_config():
    conn = http.client.HTTPSConnection(OPENAI_URL)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
    }

    conn.request(
        "POST",
        "/v1/chat/completions",
        headers=headers,
        body=json.dumps(
            {
                "model": "gpt-4o",
                "messages": [
                    {
                        "role": "system",
                        "content": f"""
You are helping to generate a configuration object for an application that uses an agentic planning framework.

You will be given a description of the application, and you need to generate a configuration object for the application,
which matches the following JSON schema:
{ApplicationConfig.model_json_schema()}

Return only the JSON object without any other formatting, and nothing else.
""",
                    },
                    {
                        "role": "user",
                        "content": f"Goal of the application: {{cookiecutter.description}}",
                    },
                ],
            }
        ),
    )

    response = conn.getresponse()

    data = json.loads(response.read().decode())

    conn.close()

    return ApplicationConfig.model_validate_json(
        data["choices"][0]["message"]["content"]
    )


def apply_application_config(config: ApplicationConfig):
    # cookiecutter itself uses jinja2 and will have already applied the template,
    # so we define our own custom syntax for this additional layer of templating
    # in our custom syntax, "{"" is replaced with "["
    custom_syntax = {
        "block_start_string": "[%",
        "block_end_string": "%]",
        "variable_start_string": "[[",
        "variable_end_string": "]]",
        "comment_start_string": "[#",
        "comment_end_string": "#]",
    }

    env = Environment(**custom_syntax)

    directory = "{{ cookiecutter.project_slug }}"

    for file in os.listdir(directory):
        if file.endswith(".py"):
            with open(os.path.join(directory, file), "r") as f:
                content = f.read()

            template = env.from_string(content)
            rendered = template.render(config=config)

            with open(os.path.join(directory, file), "w") as f:
                f.write(rendered)


if __name__ == "__main__":
    config = generate_application_config()
    apply_application_config(config)
