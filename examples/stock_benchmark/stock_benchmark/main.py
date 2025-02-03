from pydantic import BaseModel, Field
from stock_benchmark.tools.calculate_statistics import calculate_statistics
from stock_benchmark.tools.combine_ticker_data import combine_ticker_data
from stock_benchmark.tools.download_ticker import download_ticker

from autoplan import Plan, Step, with_planning


class ApplicationStep(Step):
    rationale: str = Field(
        description="Layout a detailed rationale for the current step. Explain why it is important and how it contributes to the overall plan. Be objective, don't make up any information, don't rely on your general knowledge."
    )
    objective: str = Field(
        description="Describe the objective of the current step in a single sentence. Start each objective with a verb."
    )


class ApplicationPlan(Plan):
    rationale: str = Field(
        description="Layout a detailed rationale for the plan, referring back to the example plans"
    )
    steps: list[ApplicationStep] = Field(
        description="The list of steps that make up this plan."
    )


class ApplicationOutput(BaseModel):
    custom_benchmark: str

    comparison_results: str

    display_title: str = Field(
        description="A short title that summarizes the output to be displayed in the UI."
    )


tools = [
    calculate_statistics,
    download_ticker,
]


def generate_plan(execution_context, application_args) -> list[str]:
    return [
        f"""Generate a plan to answer the user's query about stock market benchmarks. 
        You cannot rely on your general knowledge to answer these questions.
        You will be probided with a list of additional tools to reason abuot the user's query. Youmust use these tools provided to generate the best plan possible to answer the user's query.
        
        The list of tools and how to use them is defined by the json schema below:
        {execution_context.plan_class.model_json_schema()}

        When creating the plan, you must pay special attention to the step indices of other tool calls any step depends on. 
          - Note that they are numbered starting from 0. 
          - You must insure that no tool call depends on itself. This would be a circular dependency and it is not allowed.
          - If an input parameter of a tool call depends on the result of another tool call, you must set its parameter to be a PriorResult class and specify its index to refer to the specific output of another specific tool call. This is illustrated in the below examples.

        Apply the following plan to solve for the user's query:
        - Download the data for the tickers that are relevant to the user's query.
        - Run the calculate statistics tool for every downloaded ticker data.
        
        Follow these recommendations for generating the plan:
        - If the user mentioned specific stocks, you should download the data for those stocks.
        - If the user's query about general benchmarks, or market trends, you should also download the data for major indexes that are relevant to the user's query. For instance, if the user's query is about one or more technology or finance stocks, you shoulddownload major indexes like the S&P 500 (^GSPC), Dow (^DJI), and Nasdaq (^IXIC).
        - You are provided with a tool to combine the data for the tickers. You should use this tool when there are multiple tickers to reason about.
        - You are also provided with a tool to calculate financial statistics. You must use that tool to calculate specific metrics than just the ticket data to make sure you can answer the user's question accurately.
        - Don't try reducing the number of steps. The more steps you have, the more accurate the final output will be.

        Only download data that you will use in the benchmark or comparison

        Example 1 (big pharma):
        - Step 0: download_ticker(ticker="^GSPC")
        - Step 1: download_ticker(ticker="PFE")
        - Step 2: download_ticker(ticker="JNJ")
        - Step 3: download_ticker(ticker="ABBV")
        - Step 4: calculate_statistics(data=PriorResult(index=0))
        - Step 5: calculate_statistics(data=PriorResult(index=1))
        - Step 6: calculate_statistics(data=PriorResult(index=2))
        - Step 7: calculate_statistics(data=PriorResult(index=3))

        Example 2 (materials):
        - Step 0: download_ticker(ticker="^GSPC")
        - Step 1: download_ticker(ticker="NEM")
        - Step 2: download_ticker(ticker="RIO")
        - Step 3: download_ticker(ticker="BHP")
        - Step 4: calculate_statistics(data=PriorResult(index=4))
        - Step 5: calculate_statistics(data=PriorResult(index=1))
        - Step 6: calculate_statistics(data=PriorResult(index=2))
        - Step 7: calculate_statistics(data=PriorResult(index=3))

        """,
        "The user's query: " + application_args["description"],
    ]


def combine_steps(
    execution_context, plan: ApplicationPlan, steps: list[ApplicationStep]
) -> list[str]:
    return [
        """Summarize the results coming out of the tool executions in the following way:
        1. Answer the user's query, explaining the rationale behind the metrics and data used.
        2. Explain the meaning of the metrics and basis for the benchmark comparison.
        If the data is empty, tell the user that you couldn't find any information about this query 
        in the stock market databases and you are only trained to answer questions about the stock performance in the markets.
        """,
        str(steps),
    ]


@with_planning(
    step_class=ApplicationStep,
    plan_class=ApplicationPlan,
    tools=tools,
    generate_plan_prompt_generator=generate_plan,
    combine_steps_prompt_generator=combine_steps,
)
async def run(
    description: str,
) -> ApplicationOutput:
    pass
