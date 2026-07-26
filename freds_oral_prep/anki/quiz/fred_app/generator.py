import base64
import json
import logging
import mimetypes
import re
from pathlib import PosixPath

from freds_oral_prep.lib.anki.cards.drag_and_drop import DragAndDropCard
from freds_oral_prep.lib.anki.cards.multiple_choice import MultipleChoiceCard
from freds_oral_prep.lib.anki.cards.ordering import OrderingCard
from freds_oral_prep.lib.anki.cards.dynamic_image import DynamicImageCard
from freds_oral_prep.anki.helpers import (
    AnyCard,
    create_multiple_choice_card,
    create_ordering_card,
    create_dynamic_image_card,
)

logger = logging.getLogger(__name__)

_SMARTIE_BOARD_COLORS = {
    1: "#2ecc71",  # green sidelight
    2: "#e74c3c",  # red sidelight
    3: "#ffffff",  # white masthead/stern/all-round light
    4: "#f1c40f",  # steady yellow
    5: "#f1c40f",  # flashing yellow
    6: "#e74c3c",  # flashing red
}
_SMARTIE_BOARD_GRID_SIZE = 10
_SMARTIE_BOARD_POINT_RE = re.compile(r"\{\s*(\d+)\s*,\s*(\d+)\s*}")


def _embed_local_image(bundle_path: PosixPath, relative_path: str) -> str:
    image_path = bundle_path / relative_path.lstrip("/")
    if not image_path.is_file():
        logger.warning(f"Missing quiz image: {image_path}")
        return ""

    mime_type = mimetypes.guess_type(image_path.name)[0] or "application/octet-stream"
    encoded = base64.b64encode(image_path.read_bytes()).decode()
    return f'<img src="data:{mime_type};base64,{encoded}" />'


def _build_multiple_choice_card(
    bundle_path: PosixPath, section: str, question: dict
) -> MultipleChoiceCard:
    image = _embed_local_image(bundle_path, question["image"]) if question.get("image") else None
    answers = [(answer["answer"], answer["correct"]) for answer in question["answers"]]
    return create_multiple_choice_card(
        title=section,
        question=question["question"],
        answers=answers,
        image=image or None,
        explanation=question.get("feedback") or None,
    )


def _build_drag_and_drop_card(bundle_path: PosixPath, section: str, question: dict) -> DragAndDropCard | None:
    correct_answer = next((a["answer"] for a in question["answers"] if a["correct"]), None)
    if not correct_answer:
        logger.warning(f"No correct answer for drag/drop question: {question['question']}")
        return None

    data = {
        "title": section,
        "question": "Match the question to the correct answer",
        "question_1": question["question"],
        "answer_1": _embed_local_image(bundle_path, correct_answer),
        "explanation": question.get("feedback") or None,
    }

    # Distractor images from this same question are shown as unmatched decoys in the answer pool.
    distractors = [a["answer"] for a in question["answers"] if not a["correct"]]
    for i, distractor in enumerate(distractors[:9], start=2):
        data[f"answer_{i}"] = _embed_local_image(bundle_path, distractor)

    return DragAndDropCard(**data)


def _build_ordering_card(section: str, question: dict) -> OrderingCard:
    items = [answer["answer"] for answer in question["answers"]]
    return create_ordering_card(
        title=section,
        question=question["question"],
        items=items,
        explanation=question.get("feedback") or None,
    )


def _smartie_board_points(smartie_board: list[dict]) -> list[dict]:
    points = []
    for point in smartie_board:
        if match := _SMARTIE_BOARD_POINT_RE.match(point["point"]):
            x, y = int(match.group(1)), int(match.group(2))
            points.append(
                {
                    "x": (x + 0.5) / _SMARTIE_BOARD_GRID_SIZE,
                    "y": (y + 0.5) / _SMARTIE_BOARD_GRID_SIZE,
                    "color": _SMARTIE_BOARD_COLORS.get(point["answer"], "#999999"),
                }
            )
    return points


def _build_dynamic_image_card(section: str, question: dict) -> DynamicImageCard:
    categories = [
        {"label": category["answer"], "options": category["options"], "correct": category["options"][0]}
        for category in question["answers"]
    ]
    return create_dynamic_image_card(
        title=section,
        question=question["question"],
        description=question.get("description") or "",
        board_points=_smartie_board_points(question.get("smartie_board", [])),
        grid_is_black=bool(question.get("grid_is_black")),
        categories=categories,
        explanation=question.get("feedback") or None,
    )


def build_expected_cards(source_path: PosixPath) -> dict[str, list[AnyCard]]:
    expected_cards = {}
    for path in (source_path / "data").glob("*.json"):
        with path.open() as fh:
            data = json.load(fh)

        section = data["name"]
        for question in data["questions"]:
            question_type = question.get("type")

            if question_type == 0:
                card = _build_multiple_choice_card(source_path, section, question)
            elif question_type == 1:
                card = _build_drag_and_drop_card(source_path, section, question)
            elif question_type == 2:
                card = _build_ordering_card(section, question)
            elif question_type == 4:
                card = _build_dynamic_image_card(section, question)
            else:
                logger.warning(f"Skipping question with unknown type {question_type!r}: {question['question']}")
                continue

            if card:
                expected_cards.setdefault(section, []).append(card)

    return expected_cards
