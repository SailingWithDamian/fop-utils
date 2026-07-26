import logging
from pathlib import PosixPath

import click

from freds_oral_prep.anki.helpers import add_cards_to_deck, get_or_create_deck, flag_cards_with_empty_field
from freds_oral_prep.anki.quiz.minimum_flash_cards.generator import build_expected_cards

logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--source-path",
    type=click.Path(),
    required=True,
    help="Directory of downloaded course files to scan for minimum suggested flash card PDFs",
)
@click.pass_context
def cli(ctx, source_path: str) -> None:
    """Build minimum-suggested flash card decks from downloaded course PDFs, one deck per section."""
    collection = ctx.obj["anki_collection"]

    for section, expected_cards in build_expected_cards(PosixPath(source_path).expanduser()).items():
        deck_name = f"Fred::Minimum Flash Cards::{section}"
        logger.info(f"[{section}] Found {len(expected_cards)} card(s)")

        deck_id = get_or_create_deck(collection, deck_name)
        added, skipped = add_cards_to_deck(collection, deck_id, deck_name, expected_cards)
        flagged = flag_cards_with_empty_field(collection, deck_name, "Back", flag=5)
        logger.info(f"{deck_name}: {added} added, {skipped} skipped (already exist), {flagged} flagged pink (no content)")
