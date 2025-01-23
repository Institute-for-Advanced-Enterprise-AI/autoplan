# AutoPlan

AutoPlan is an open-source Python framework that provides a powerful pattern for implementing agentic AI applications, leveraging dynamic plan generation to select and use external tools based on the task's context.


## Installation

AutoPlan requires Python 3.12 or higher.

Install using pip:

```
pip install -U autoplan
```


## Quick start

The best way to start using AutoPlan is to create a new application. AutoPlan has a command-line interface that allows you to do that. To create your own application, you can use the following command:

```bash
autoplan generate \
  --name "my_app" \
  --description "Given a situation described by the user, generate a joke about it." \ 
  --outdir .
```

Note that you can also leave the parameters empty and let the CLI prompt you for the information, which will help you get started with bootstrapping your application.

This command line will create a new folder named `my_app` with the basic structure of an AutoPlan application. You can then go in the application folder and run it with the following command:

```bash
cd my_app
poetry install
poetry run python my_app/app.py
```

This will start a Gradio interface that allows you to interact with the application without any additional effort. You can now use your browser and go to `http://localhost:7860` to see the application.

> [!NOTE]
> By default AutoPlan will use Open AI models and will include a search tool based on [you.com](http://api.you.com), which require API keys. You can set the `OPENAI_API_KEY` and `YDC_API_KEY` environment variables to your OpenAI and You API keys to use your own accounts .

## Why use AutoPlan?

Agentic AI applications are an emerging AI paradigm where LLMs use external tools to accomplish tasks that are beyond their own capabilities while keeping control over how to use those tools so that their abilities are not limited to predefined workflows. Building agentic applications requires a system design that allows plans to be dynamically generated, tools to be efficiently executed, and data flowing between tools to be properly channeled to provide a coherent output. AutoPlan provides just that.

AutoPlan is organized around three core components, each serving a specific purpose to enable dynamic planning, execution, and integration required for building an agentic application:

**Tools** can be any typed Python function — they can be procedural code, LLM calls, or AutoPlan applications themselves. Tools can be composed from smaller tools.

**Planners** are LLM-based components that generate the sequence of tools to be executed and the arguments to be passed to each tool to solve a given task. 

**Composers** integrate tool outputs based on the planner’s strategy to produce a final output.

![pdoc architecture](docs/img/architecture.png)


## Developer docs

### Type checking

For the planning framework: `poetry run pyright autoplan`

### Generating docs

Run a web server to view the docs:
`poetry run pdoc autoplan`

Generate the docs:
`poetry run pdoc autoplan --output build-docs`

### Running unit tests

`poetry run pytest tests`

