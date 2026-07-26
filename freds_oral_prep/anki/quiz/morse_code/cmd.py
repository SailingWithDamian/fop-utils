import logging

import click

from freds_oral_prep.anki.helpers import add_cards_to_deck, get_or_create_deck
from freds_oral_prep.anki.quiz.morse_code.generator import build_expected_cards


@click.command()
@click.option("--questions-per-round", default=4, type=int, help="Number of letters to match per drag-and-drop card")
@click.option(
    "--priority-cards", default=False, is_flag=True, help="Only build cards for request/danger/colreg letters"
)
@click.option("--deck-name", default=None, help="Deck to add cards to [default: Signals::Morse Code]")
@click.pass_context
def cli(ctx, questions_per_round: int, priority_cards: bool, deck_name: str | None) -> None:
    """Build a Morse code letter-matching deck from Wikipedia."""
    if deck_name is None:
        deck_name = f"{'Priority ' if priority_cards else ''}Signals::Morse Code"

    expected_cards = build_expected_cards(priority_cards, questions_per_round)

    collection = ctx.obj["anki_collection"]
    deck_id = get_or_create_deck(collection, deck_name)
    added, skipped = add_cards_to_deck(collection, deck_id, deck_name, expected_cards)
    logging.info(f"Done: {added} added, {skipped} skipped (already exist)")
