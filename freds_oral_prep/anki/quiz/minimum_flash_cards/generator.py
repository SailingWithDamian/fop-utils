import logging
import re
from pathlib import PosixPath

import pdfplumber

from freds_oral_prep.lib.anki.cards.flip_card import BasicFlipCard

logger = logging.getLogger(__name__)

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

FLASH_CARD_FILENAME_PREFIXES = (
    "Flashcards ",
    "M200 Flashcards ",
    "OOW Flashcards ",
    "OOW flashcard ",
)
FLASH_CARD_FILENAME_EXACT = ("updates flashcards", "Steering flashcards")


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


def _find_suggested_flash_card_files(base_path: PosixPath) -> dict[str, PosixPath]:
    source_files = {}
    for course_file in base_path.rglob("*.pdf"):
        if (
            course_file.stem.startswith(FLASH_CARD_FILENAME_PREFIXES)
            or "Minimum suggested Flash Card Titles" in course_file.stem
            or course_file.stem in FLASH_CARD_FILENAME_EXACT
        ):
            section = course_file.parent.stem.replace(" _ ", " / ")
            source_files[section] = course_file

    return source_files


def build_expected_cards(base_path: PosixPath) -> dict[str, list[BasicFlipCard]]:
    cards_by_section = {}

    for section, course_file in _find_suggested_flash_card_files(base_path).items():
        cards_by_section[section] = [
            BasicFlipCard(front=front, back=back or "")
            for front, back in _extract_cards(course_file).items()
        ]

    return cards_by_section
