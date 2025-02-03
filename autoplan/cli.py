import importlib.resources as resources

import click
from cookiecutter.main import cookiecutter

import autoplan


@click.group()
def cli():
    pass


@cli.command(short_help="Generate an application using the planning framework")
@click.option("--name", prompt="Project name")
@click.option("--description", prompt="Project description")
@click.option("--outdir", prompt="Output directory")
def generate(name, description, outdir):
    template_path = resources.files(autoplan).joinpath("generator/cookiecutter")

    cookiecutter(
        str(template_path),
        output_dir=outdir,
        extra_context={
            "project_name": name,
            "description": description,
        },
        no_input=True,
    )


cli.add_command(generate)

if __name__ == "__main__":
    cli()
