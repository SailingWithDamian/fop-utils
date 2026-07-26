import logging

import click

from freds_oral_prep.anki.exam_setup.helpers import filtered_deck_search_strings

logger = logging.getLogger(__name__)

@click.command()
@click.pass_context
def cli(ctx) -> None:
    """Prints the search strings for building cram / leech filtered decks manually in the Anki GUI."""
    parent_deck = ctx.obj["exam_parent_deck"]
    click.echo(
        "The anki library can't create filtered decks directly, so build these "
        "by hand: Tools -> Create Filtered Deck, then paste the search:"
    )
    for description, search in filtered_deck_search_strings(parent_deck).items():
        click.echo(f"\n{description}:")
        click.echo(f"  {search}")
