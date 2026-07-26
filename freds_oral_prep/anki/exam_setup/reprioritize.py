import logging

import click

from freds_oral_prep.anki.exam_setup.helpers import reprioritize_new_cards

logger = logging.getLogger(__name__)

@click.command()
@click.pass_context
def cli(ctx) -> None:
    """
    Pushes cards tagged priority::high to the front of the new-card queue,
    then priority::med, then everything else. Run this any time after
    adding/tagging new cards.
    """
    collection = ctx.obj["anki_collection"]
    parent_deck = ctx.obj["exam_parent_deck"]
    counts = reprioritize_new_cards(collection, parent_deck)
    if not counts:
        logger.info("No new cards found to reorder.")
        return

    logger.info(f"Reordered {sum(counts.values())} new cards under '{parent_deck}':")
    for label, count in counts.items():
        logger.info(f"  {label}: {count} cards")
