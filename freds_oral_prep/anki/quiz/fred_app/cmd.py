import logging
import sys
from pathlib import PosixPath

import click

from freds_oral_prep.anki.helpers import add_cards_to_deck, get_or_create_deck
from freds_oral_prep.anki.quiz.fred_app.generator import build_expected_cards


@click.command()
@click.option("--deck-name", default=None, help="Deck to add cards to [default: Fred::Offline Quiz]")
@click.option(
    "--app-path",
    type=click.Path(),
    default="/Applications/Fred's Quiz App.app",
    show_default=True,
    help="Path to the installed offline quiz app bundle",
)
@click.pass_context
def cli(ctx, app_path: str, deck_name: str | None) -> None:
    """Build Anki decks from the questions bundled in Fred's offline quiz app."""
    if deck_name is None:
        deck_name = "Fred::Offline Quiz"

    source_path = PosixPath(app_path) / "Wrapper" / "FOPQuiz.app" / "FOPQuizOnly.bundle"
    if not source_path.is_dir():
        print(f"Failed to find source path: {source_path}")
        sys.exit(1)

    expected_cards = build_expected_cards(source_path)

    collection = ctx.obj["anki_collection"]
    for section_name, section_cards in expected_cards.items():
        deck_id = get_or_create_deck(collection, f'{deck_name}::{section_name}')
        added, skipped = add_cards_to_deck(collection, deck_id, deck_name, section_cards)
        logging.info(f"Done: {added} added, {skipped} skipped (already exist)")
