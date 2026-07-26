import logging

import click
import requests

from freds_oral_prep.anki.helpers import add_cards_to_deck, get_or_create_deck
from freds_oral_prep.anki.quiz.signal_flags.generator import (
    PRIORITY_LETTERS,
    USER_AGENT,
    build_expected_cards,
    fetch_wiki_text,
    parse_signals,
)


@click.command()
@click.option("--questions-per-round", default=3, type=int, help="Number of flags to match per drag-and-drop card")
@click.option(
    "--priority-cards",
    default=False,
    is_flag=True,
    help="Tag cards covering a priority letter with 'priority::high', instead of filtering them out",
)
@click.pass_context
def cli(ctx, questions_per_round: int, priority_cards: bool) -> None:
    """Build International Code of Signals flag-matching decks from Wikipedia."""
    with requests.Session() as session:
        session.headers["User-Agent"] = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/149.0.0.0 Safari/537.36"
        )

        wiki_text = fetch_wiki_text(session)
        if not wiki_text:
            logging.error("Failed to fetch Wikipedia article")
            return

        letter_flags, number_flags = parse_signals(session, wiki_text)

    priority_letters = PRIORITY_LETTERS if priority_cards else ()
    collection = ctx.obj["anki_collection"]

    for signals, deck_name, title in [
        (letter_flags, "Signals::Code Flags::Letters", "International Code Flags - Letters"),
        (number_flags, "Signals::Code Flags::Numbers", "International Code Flags - Numbers"),
    ]:
        if not signals:
            continue
        expected_cards = build_expected_cards(signals, title, questions_per_round, priority_letters)
        deck_id = get_or_create_deck(collection, deck_name)
        added, skipped = add_cards_to_deck(collection, deck_id, deck_name, expected_cards)
        logging.info(f"{deck_name}: {added} added, {skipped} skipped (already exist)")
