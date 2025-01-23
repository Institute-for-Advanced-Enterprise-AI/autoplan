import asyncio
import os
from typing import AsyncGenerator

import gradio as gr
import inflect
import trafilatura

from {{cookiecutter.project_slug}}.main import run
from {{cookiecutter.project_slug}} import dependencies
from autoplan import (
    FinalResult,
    PartialPlanResult,
    PlanResult,
    StepResult,
)

Inflect = inflect.engine()

example_links = {}

# custom css for the output
css = """
.annotations .textspan:not(.no-cat) {
    background-color: white !important;
}
.annotations .textspan:not(.no-cat) .text {
    color: black !important;
    background-color: #f2f2f2 !important;
}
.annotations .textspan .label {
    color: cornflowerblue !important;
    text-transform: inherit !important;
    background-color: white !important;
    font-family: Georgia, serif !important;
    font-weight: normal !important;
}
"""


# We want each value returned by "download" to be unique, in order to allow the user to re-run the analysis
# even when the value is unchanged, so we wrap it in this class
class StatefulItem:
    def __init__(self, value: str):
        self.value = value


async def generate(
    [% for input, type in config.inputs.items() %]
    [[input]]: [[type]] | StatefulItem,
    [% endfor %]
) -> AsyncGenerator[tuple[str, str], None]:
    [% for input in config.inputs %]
    if isinstance([[input]], StatefulItem):
        [[input]] = [[input]].value
        setattr(dependencies, "[[input]]", [[input]])
    [% endfor %]

    yield "Generating a  plan...", "..."



    # queue of steps to show in the UI while wait
    plan_steps_queue = []

    result = None

    async def run_and_populate():
        nonlocal result
        async for r in run([% for input in config.inputs %]
            [[input]],
        [% endfor %]):
            if isinstance(r, PartialPlanResult):
                for step in r.result.steps or []:
                    if step not in plan_steps_queue:
                        plan_steps_queue.append(step)

            elif isinstance(r, PlanResult):
                for step in r.result.steps or []:
                    if step not in plan_steps_queue:
                        plan_steps_queue.append(step)

            elif isinstance(r, StepResult):
                pass

            elif isinstance(r, FinalResult):
                result = r.result

    # start the analysis in the background
    asyncio.create_task(run_and_populate())

    # how often to switch steps in the UI
    step_display_interval = 2

    # how often to check if the analysis is complete or if the step should be switched
    check_interval = 0.1

    # counter to determine if step switching should occur
    counter = 0

    while True:
        await asyncio.sleep(check_interval)

        if result:
            summary = ""

            for index, key in enumerate(list(result.__fields__.keys())):
                if index > 0:
                    summary += "\n\n"

                summary += getattr(result, key)

            yield result.display_title, summary
            return
        else:
            if counter % (step_display_interval / check_interval) == 0:
                # show an unseen step
                if plan_steps_queue:
                    step = plan_steps_queue.pop(0)

                    objective = step.objective

                    # add "ing" to the first word (e.g. "Find" -> "Finding")
                    words = objective.split()
                    words[0] = Inflect.present_participle(words[0])

                    yield (
                        " ".join(words),
                        ""
                    )

        counter += 1


async def download(title_or_link: str) -> StatefulItem:
    if title_or_link in example_links:
        link = example_links[title_or_link]
    else:
        link = title_or_link

    downloaded_item = trafilatura.fetch_url(link)
    text = trafilatura.extract(
        downloaded_item,
        include_links=True,
        include_images=True,
        include_tables=True,
        include_formatting=True,
    )
    return StatefulItem(text)

async def download_many(
    *args
):
    results = []    
    for arg in args:
        results.append(await download(arg))

    if len(results) == 1:
        return results[0]
    else:
        return results

def main():
    with gr.Blocks(css=css) as app:
        with gr.Tabs():
            with gr.Tab("Web Link"):
                with gr.Row():
                    with gr.Column():
                        
                        [% for input in config.inputs %]
                        input_box_[[input]]_1 = gr.Dropdown(
                            label="Link for [[input]]".capitalize(),
                            choices=[
                                # empty string as first choice to allow the user to enter their own link
                                "",
                            ]
                            + list(example_links.keys()),
                            allow_custom_value=True,
                        )

                        # This should really just be `document1 = gr.Markdown(label="Document")`
                        # but there is a bug in Gradio (reported by others on Github issues but unfixed)
                        # where it causes an infinite loop if you add a `.change` handler to it,
                        # so I added a layer of indirection via `gr.State()`
                        document_[[input]]_1 = gr.State()

                        @gr.render(inputs=document_[[input]]_1)
                        def render_document_[[input]](item: StatefulItem | None):
                            return gr.Markdown(
                                label="[[input]]".capitalize(),
                                value=item.value if item else "",
                            )

                        [% endfor %]
                        run_button1 = gr.Button("Download & Run")

                    with gr.Column():
                        output_label1 = gr.Label(label="Output")
                        output1 = gr.Markdown(label="Output")
    

            with gr.Tab("Edit"):
                with gr.Row():
                    with gr.Column():
                        [% for input in config.inputs %]
                        document_[[input]]_2 = gr.Textbox(
                            label="[[input]]".capitalize(), max_lines=40, lines=20
                        )
                        [% endfor %]
                        run_button2 = gr.Button("Run")

                    with gr.Column():
                        output_label2 = gr.Label(label="Output")
                        output2 = gr.Markdown(label="Output")

        run_button1.click(fn=download_many, inputs=[ [% for input in config.inputs %]
            input_box_[[input]]_1,
        [% endfor %] ], outputs=[ [% for input in config.inputs %]
            document_[[input]]_1,   
        [% endfor %] ])
        document_[[config.inputs.keys() | first]]_1.change(
            fn=generate,
            inputs=[ [% for input in config.inputs %]
                document_[[input]]_1,
            [% endfor %] ],
            outputs=[output_label1, output1],
        )
        run_button2.click(
            fn=generate,
            inputs=[ [% for input in config.inputs %]
                document_[[input]]_2,
            [% endfor %] ],
            outputs=[output_label2, output2],
        )

    app.launch(
        server_name=os.environ.get(
            "HOST",
            # localhost by default
            "127.0.0.1",
        ),
        server_port=int(os.environ.get("PORT", 7860)),
    )


if __name__ == "__main__":
    main()
