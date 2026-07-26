import logging

import click

import anki_drag_and_drop
import anki_multiple_choice
import anki_ordering
import anki_dynamic_image

logger = logging.getLogger(__name__)


@click.command()
@click.pass_context
def cli(ctx) -> None:
    """Create or update every Anki note type our quiz/exam-setup commands depend on."""
    collection = ctx.obj["anki_collection"]
    for package in (anki_drag_and_drop, anki_multiple_choice, anki_ordering, anki_dynamic_image):
        logger.info(f"Syncing note type: {package.MODEL_NAME}")
        package.sync(collection)
