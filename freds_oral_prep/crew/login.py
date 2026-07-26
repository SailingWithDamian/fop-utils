import logging
import sys

import click

from freds_oral_prep.crew.api import CrewApi

logger = logging.getLogger(__name__)


@click.command()
@click.option("--force/--no-force", default=False)
@click.pass_context
def cli(ctx, force: bool) -> None:
    """Log in to the crew portal and cache the session cookies for later commands."""
    api = CrewApi()
    if api.have_valid_login() and not force:
        click.echo("Have existing valid login")
        return

    api.perform_interactive_login()
    if api.have_valid_login():
        click.echo("Login successful")
        return

    click.echo("Invalid login")
    sys.exit(1)
