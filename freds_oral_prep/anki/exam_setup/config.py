import logging

import click
from freds_oral_prep.anki.exam_setup.helpers import get_topic_decks

logger = logging.getLogger(__name__)


@click.command()
@click.pass_context
def cli(ctx) -> None:
    """Show the subdecks under the parent deck and their current deck-options preset."""
    collection = ctx.obj["anki_collection"]
    parent_deck = ctx.obj["exam_parent_deck"]
    decks = get_topic_decks(collection, parent_deck)
    config = collection.decks.get_config(collection.decks.get(decks[0].id)["conf"])

    click.echo(f"Subdecks under '{parent_deck}': {len(decks)}")
    for deck in decks:
        click.echo(f"  - {deck.name}")

    click.echo("")
    click.echo("Current config for this group:")
    for key in ("name", "desiredRetention", "new", "rev", "lapse"):
        if key in config:
            click.echo(f"  {key}: {config[key]}")
