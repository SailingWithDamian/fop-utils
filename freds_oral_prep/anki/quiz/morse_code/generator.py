import logging

import requests
import wikitextparser

from freds_oral_prep.lib.anki.cards.flip_card import BasicFlipCard
from freds_oral_prep.lib.anki.cards.drag_and_drop import DragAndDropCard
from freds_oral_prep.anki.helpers import create_drag_and_drop_pairs

logger = logging.getLogger(__name__)
USER_AGENT = "SailingWithDamian/freds-oral-prep/quiz/morse-code"
PRIORITY_LETTERS = (
    # Single letter (request, danger, colregs)
    "A",
    "O",
    "U",
    "L",
    "D",
    "G",
    "W",
    "P",
    # Colreg fog signals
    "T",
    "M",
    "D",
    "R",
)


def fetch_wiki_text(session: requests.Session) -> str | None:
    r = session.get(
        "https://en.wikipedia.org/w/api.php",
        params={
            "action": "query",
            "prop": "revisions",
            "rvslots": "main",
            "rvprop": "content",
            "titles": "Morse_code",
            "format": "json",
        },
    )
    r.raise_for_status()
    if page := next(iter(r.json()["query"]["pages"].values()), None):
        if page["revisions"]:
            return page["revisions"][0]["slots"]["main"]["*"]

    logger.error(f"Failed to get text from Wikipedia API: [{r.status_code}] {r.text}")
    return None


def parse_signals(wiki_text: str) -> list:
    signals = []
    parsed_text = wikitextparser.parse(wiki_text)
    for table in parsed_text.tables:
        if table.data()[0] == ["Category", "Character", "Code"]:
            for row in table.data()[1:]:
                if row[0] == "Letters":
                    letter = wikitextparser.parse(row[1]).wikilinks[0].target
                    sequence = None
                    for template in wikitextparser.parse(row[2]).templates:
                        if template.name == "morse":
                            sequence = " ".join(
                                [
                                    {
                                        "dash": "—",
                                        "dot": ".",
                                    }[argument.value]
                                    for argument in template.arguments
                                ]
                            )

                    if letter and sequence:
                        signals.append(
                            {
                                "letter": letter,
                                "sequence": sequence,
                            }
                        )
    return signals


def build_expected_cards(only_priority_cards: bool, questions_per_round: int) -> list[BasicFlipCard | DragAndDropCard]:
    with requests.Session() as session:
        session.headers["User-Agent"] = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/149.0.0.0 Safari/537.36"
        )
        wiki_text = fetch_wiki_text(session)

    if not wiki_text:
        logger.error(f"Failed to get text from Wikipedia API: [{wiki_text}]")
        return []

    signals = parse_signals(wiki_text)
    if not signals:
        logger.error(f"Found no signals in page: [{wiki_text}]")
        return []

    if only_priority_cards:
        signals = [signal for signal in signals if signal["letter"] in PRIORITY_LETTERS]

    return create_drag_and_drop_pairs(
        "International Code Signals",
        "Identify The Morse Code Letter",
        [(signal["letter"], signal["sequence"]) for signal in signals],
        questions_per_round,
    )
