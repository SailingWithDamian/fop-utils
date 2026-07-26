import logging

import click


@click.group()
@click.option(
    "--debug/--no-debug",
    default=False,
    show_default=True,
    help="Enable debug level logging",
)
@click.pass_context
def cli(ctx, debug: bool) -> None:
    """Fred's oral prep utilities: course downloads, quiz generation, and Anki deck maintenance."""
    logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)
