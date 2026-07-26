import logging
from base64 import b64encode
from pathlib import PosixPath

import requests
import wikitextparser

from freds_oral_prep.lib.anki.cards.flip_card import BasicFlipCard
from freds_oral_prep.lib.anki.cards.drag_and_drop import DragAndDropCard
from freds_oral_prep.anki.helpers import create_drag_and_drop_pairs

logger = logging.getLogger(__name__)

MEDIA_PATH = PosixPath(__file__).parent.parent.parent.parent.parent / "media"
USER_AGENT = "SailingWithDamian/freds-oral-prep/quiz/signal-flags"
PRIORITY_LETTERS = ("A", "O", "U", "L", "D", "G", "W", "P", "T", "M", "R")


def fetch_wiki_text(session: requests.Session) -> wikitextparser.WikiText | None:
    r = session.get(
        "https://en.wikipedia.org/w/api.php",
        params={
            "action": "query",
            "prop": "revisions",
            "rvslots": "main",
            "rvprop": "content",
            "titles": "International_maritime_signal_flags",
            "format": "json",
        },
    )
    r.raise_for_status()
    if page := next(iter(r.json()["query"]["pages"].values()), None):
        if page["revisions"]:
            return wikitextparser.parse(page["revisions"][0]["slots"]["main"]["*"])

    logger.error(f"Failed to get text from Wikipedia API: [{r.status_code}] {r.text}")
    return None


def fetch_commons_url(session: requests.Session, source_name: str) -> str | None:
    r = session.get(
        "https://commons.wikipedia.org/w/api.php",
        params={
            "action": "query",
            "titles": source_name,
            "prop": "imageinfo",
            "iiprop": "url",
            # The full-size "url" is served from a heavily rate-limited endpoint - request the
            # largest available thumbnail instead, which is served from a much less restricted path.
            "iiurlwidth": 2000,
            "format": "json",
        },
    )
    r.raise_for_status()
    if page := next(iter(r.json()["query"]["pages"].values()), None):
        if image_info := page.get("imageinfo"):
            return image_info[0].get("thumburl") or image_info[0]["url"]

    logger.error(f"Failed to get file from Commons API: [{r.status_code}] {r.text}")
    return None


def download_file(session: requests.Session, source_url: str, target: PosixPath) -> None:
    r = session.get(source_url)
    r.raise_for_status()
    target.write_bytes(r.content)


def embedded_img(path: PosixPath) -> str:
    return f'<img src="data:image/png;base64,{b64encode(path.read_bytes()).decode()}" />'


def parse_signals(session: requests.Session, wiki_text: wikitextparser.WikiText) -> tuple[list, list]:
    MEDIA_PATH.mkdir(parents=True, exist_ok=True)
    flags, numbers = [], []

    for table in wiki_text.tables:
        if table.caption == "Letter flags and ICS meanings":
            for row in table.data()[1:]:
                text = wikitextparser.remove_markup(row[0])
                letter, phonetic = text[0].upper(), text[1:].strip()
                wiki_link = wikitextparser.parse(row[1]).wikilinks[0].target
                meaning = wikitextparser.remove_markup(row[3].split('"')[1])

                target_file = MEDIA_PATH / f"letter-{letter}.png"
                if not target_file.is_file():
                    if url := fetch_commons_url(session, wiki_link):
                        download_file(session, url, target_file)

                flags.append(
                    {
                        "letter": letter,
                        "phonetic": phonetic,
                        "image": target_file,
                        "explanation": meaning.rstrip(".").strip(),
                    }
                )

        elif table.caption == "NATO number flags":
            for row in table.data()[1:]:
                text = wikitextparser.remove_markup(row[0])
                letter, phonetic = text[0], text[1:]
                wiki_link = wikitextparser.parse(row[2]).wikilinks[0].target

                target_file = MEDIA_PATH / f"number-{letter}.png"
                if not target_file.is_file():
                    if url := fetch_commons_url(session, wiki_link):
                        download_file(session, url, target_file)

                numbers.append({"letter": letter, "phonetic": phonetic, "image": target_file})

    return flags, numbers


def build_expected_cards(
    signals: list,
    title: str,
    questions_per_round: int,
    priority_letters: tuple[str, ...] = (),
) -> list[BasicFlipCard | DragAndDropCard]:
    available_signals = [s for s in signals if s["image"].is_file()]
    pairs = [(s["phonetic"], embedded_img(s["image"])) for s in available_signals]
    explanations = [
        f"{s['phonetic']}: {s['explanation']}" if s.get("explanation") else None for s in available_signals
    ]
    tags = [["priority::high"] if s["letter"] in priority_letters else [] for s in available_signals]
    return create_drag_and_drop_pairs(
        title, "Identify the matching flags", pairs, questions_per_round, explanations, tags
    )
