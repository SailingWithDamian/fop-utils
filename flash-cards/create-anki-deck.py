#!/usr/bin/env python3
import re
import sys

import click
from pathlib import PosixPath

import pdfplumber
from anki.collection import Collection

IGNORE_PATTERNS = [
    # Header
    re.compile(r"^Fred's M\d+ Notes$"),
    re.compile(r"^Fred's Masters Notes$"),
    re.compile(r"^fredsoralprep\.com$"),
    re.compile(r"^FW \d+\s*$"),
    re.compile(r"^FW \d+\s+fredsoralprep\.com.*$"),
    re.compile(r"^Under licence agreement for Freds Online Courses Pty Ltd$"),
    re.compile(r"^\d{1,3}$"),
    # Footer
    re.compile(r"^M200 .+"),
    re.compile(r"^Masters .+"),
    re.compile(r"^OOW .+"),
    re.compile(r"^ECDIS$"),
    re.compile(r"^Minimum [Ss]uggested Flash Card Titles$", re.IGNORECASE),
]


def _extract_text_from_pdf(pdf_path: PosixPath) -> str:
    lines = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            if text := page.extract_text(layout=False):
                for line in text.splitlines():
                    if stripped := line.strip():
                        if not any(pattern.match(stripped) for pattern in IGNORE_PATTERNS):
                            lines.append(stripped)
    return "\n".join(lines)


def _clean_value(text: str) -> str | None:
    text = re.sub(r"\s+FW\s+\d+.*$", "", text, flags=re.DOTALL)
    text = re.sub(r"\s+fredsoralprep\.com.*$", "", text, flags=re.DOTALL)
    text = re.sub(r"\s+Under licence agreement.*$", "", text, flags=re.DOTALL)
    if clean_text := " ".join(text.split()).strip():
        return clean_text
    return None


def _parse_paired_questions(text: str) -> dict:
    cards = {}
    entries = re.split(r"(?=^Front:)", text, flags=re.MULTILINE)
    for entry in entries:
        entry = entry.strip()
        if not entry:
            continue
        front_match = re.match(r"^Front:\s*(.+?)(?=\s*Back:)", entry, re.DOTALL)
        back_match = re.search(r"Back:\s*(.+)", entry, re.DOTALL)
        if front_match and back_match:
            front = _clean_value(front_match.group(1))
            back = _clean_value(back_match.group(1))
            cards[front] = back
    return cards


def _parse_bullet_point_list(text: str) -> dict:
    cards = {}
    for line in text.splitlines():
        if line := line.strip():
            if match := re.match(r"^[•\-\*]\s+(.+)", line):
                cards[_clean_value(match.group(1).strip())] = None
    return cards


def _parse_plain_list(text: str) -> dict:
    cards = {}
    for line in text.splitlines():
        if line := line.strip():
            cards[_clean_value(line)] = None
    return cards


def _extract_cards(pdf_path: PosixPath) -> dict:
    text = _extract_text_from_pdf(pdf_path)

    if re.search(r"^Front:", text, re.MULTILINE):
        return _parse_paired_questions(text)
    if re.search(r"^[•\-\*]\s+", text, re.MULTILINE):
        return _parse_bullet_point_list(text)
    return _parse_plain_list(text)


def _find_suggested_flash_cards(base_path: PosixPath) -> dict[str, dict[str, str]]:
    source_files = {}
    for section_path in base_path.iterdir():
        for course_file in section_path.iterdir():
            if course_file.suffix != ".pdf":
                continue
            if (
                course_file.stem.startswith("Flashcards ")
                or course_file.stem.startswith("M200 Flashcards ")
                or course_file.stem.startswith("OOW Flashcards ")
                or course_file.stem.startswith("OOW flashcard ")
                or "Minimum suggested Flash Card Titles" in course_file.stem
                or course_file.stem in ("updates flashcards", "Steering flashcards")
            ):
                source_files[section_path.stem.replace(" _ ", " / ")] = course_file

    return {section_name: _extract_cards(course_file) for section_name, course_file in source_files.items()}


def _calculate_deck_name(section_name: str, is_placeholder: bool) -> str:
    prefix = "Freds M200"
    if is_placeholder:
        prefix += " - Placeholder"

    if section_name.startswith("M200 "):
        return f'{prefix}::{section_name.removeprefix("M200 ")}'

    elif section_name.startswith("OOW "):
        return f'{prefix}::OOW::{section_name.removeprefix("OOW ")}'

    elif section_name.startswith("Master "):
        return f'{prefix}::Master::{section_name.removeprefix("Master ")}'

    elif section_name.endswith(" Master") and section_name not in ("Who or what is a Master",):
        return f'{prefix}::Master::{section_name.removesuffix(" Master")}'

    return f"{prefix}::{section_name}"


def _create_deck_if_missing(collection: Collection, deck_name: str, cards: dict) -> None:
    if any(deck_name == deck.name for deck in collection.decks.all_names_and_ids()):
        print(f"Already have deck for {deck_name}")
        return

    deck_id = collection.decks.add_normal_deck_with_name(deck_name).id
    note_type = collection.models.by_name("Basic")

    for front, back in cards.items():
        # Create a simple card with a front and potentially a back
        note = collection.new_note(note_type)
        note["Front"] = front
        note["Back"] = back or ""
        collection.add_note(note, deck_id)

        # If there is no answer, flag the card as pink so it is easy to see what needs working on
        if not back:
            collection.set_user_flag_for_cards(5, collection.card_ids_of_note(note.id))


def _auto_detect_profile(base_path: PosixPath) -> str | None:
    if profiles := [path.parent.stem for path in base_path.glob("*/collection.anki2")]:
        if len(profiles) == 1:
            return profiles[0]
        print(f"Found multiple profiles in {base_path}")
    return None


@click.command()
@click.argument("source_path", type=click.Path())
@click.option(
    "--anki-path",
    type=click.Path(),
    default="~/Library/Application Support/Anki2",
    show_default=True,
    help="Path to the Anki storage location",
)
@click.option(
    "--profile",
    default=None,
    show_default=True,
    help="Profile to target",
)
def main(source_path: str, anki_path: str, profile: str) -> None:
    base_path = PosixPath(anki_path).expanduser()
    if not base_path.is_dir():
        print(f"Config path does not exist: {base_path}")
        sys.exit(1)

    if not profile:
        if profile := _auto_detect_profile(base_path):
            print(f"Using auto detected profile: {profile}")
        else:
            print(f"Failed to auto detect profile in {base_path}")
            sys.exit(1)

    collection_path = base_path / profile / "collection.anki2"
    if not collection_path.is_file():
        print(f"Collection path does not appear valid: {collection_path}")
        sys.exit(1)

    collection = Collection(collection_path.as_posix())
    try:
        for section, entries in _find_suggested_flash_cards(PosixPath(source_path)).items():
            deck_name = _calculate_deck_name(section, all(value is None for value in entries.values()))
            print(f"[{section}] Creating {len(entries)} under {deck_name}")
            _create_deck_if_missing(collection, deck_name, entries)
    finally:
        collection.close()


if __name__ == "__main__":
    main()
