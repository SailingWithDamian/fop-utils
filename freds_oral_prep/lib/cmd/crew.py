import click

import freds_oral_prep.crew.login
import freds_oral_prep.crew.course.download_resources


@click.group()
@click.pass_context
def crew(ctx) -> None:
    """Commands for the MCA online courses ("crew") portal."""
    ctx.ensure_object(dict)


@click.group()
@click.pass_context
def course(ctx) -> None:
    """Course-related downloads."""
    ctx.ensure_object(dict)


crew.add_command(freds_oral_prep.crew.login.cli, name="login")
course.add_command(freds_oral_prep.crew.course.download_resources.cli, name="download-resources")
crew.add_command(course)
