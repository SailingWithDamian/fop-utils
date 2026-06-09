#!/usr/bin/env python3
import json

import click
import sys
from pathlib import PosixPath

from anki.collection import Collection


def _get_questions(path: PosixPath) -> dict:
    if not path.is_file():
        print(f"ERROR: Source questions file not found: {path}")
        sys.exit(1)

    with path.open("r") as fh:
        return json.load(fh)


def _reformat_sources(sources: str | None) -> str:
    if sources is None:
        return ""
    return "\n".join([f"{part.strip()}" for part in sources.split(".") if part.strip()])


def _create_multiple_choice_note(collection, mc_model, question):
    note = collection.new_note(mc_model)
    note["Question"] = question["question"]
    note["Title"] = question.get("topic_name", "")
    note["QType (0=kprim,1=mc,2=sc)"] = "2"
    for i, choice in enumerate(question["answers"], start=1):
        note[f"Q_{i}"] = choice
    note["Answers"] = " ".join("1" if i == question["correct"] else "0" for i in range(0, len(question["answers"]) + 1))
    note["Sources"] = _reformat_sources(question.get("explanation"))
    return note


def _create_drag_and_drop_note(collection, dnd_model, question):
    note = collection.new_note(dnd_model)

    note["Title"] = question.get("topic_name", "")
    note["Question"] = question["question"]
    note["Sources"] = _reformat_sources(question.get("explanation"))

    top_marks = {topmark["id"]: topmark["image"] for topmark in question["topmarks"]}

    for i, buoy in enumerate(question["buoys"], start=1):
        note[f"Q_{i}"] = f'<img src="{buoy["image"]}" />'
        note[f"A_{i}"] = f'<img src="{top_marks[buoy["correctTopmark"]]}" />'

    if extra_answers := [
        top_mark for top_mark in top_marks if not any(top_mark == buoy["correctTopmark"] for buoy in question["buoys"])
    ]:
        for i, top_mark in enumerate(extra_answers, start=len(question["buoys"]) + 1):
            note[f"A_{i}"] = f'<img src="{top_marks[top_mark]}" />'

    return note


def _create_deck(path: PosixPath, deck_name: str, questions: dict) -> None:
    if not path.is_file():
        print(f"ERROR: Anki database not found: {path}")
        sys.exit(1)

    collection = Collection(path)
    if any(deck_name == deck.name for deck in collection.decks.all_names_and_ids()):
        print(f"Already have deck: {deck_name}")
        sys.exit(1)

    mc_model = collection.models.by_name("Multiple Choice Extended")
    if not mc_model:
        print("Missing custom model: Multiple Choice Extended")
        sys.exit(1)

    dnd_model = collection.models.by_name("Drag & Drop")
    if not dnd_model:
        print("Missing custom model: Drag & Drop")
        sys.exit(1)

    print(f"Creating deck: {deck_name}")
    deck_id = collection.decks.add_normal_deck_with_name(deck_name).id
    try:
        for question in questions:
            question_type = question.get("questionType")
            match question_type:
                case "multiple_choice":
                    note = _create_multiple_choice_note(collection, mc_model, question)
                    collection.add_note(note, deck_id)
                case "dragdrop":
                    note = _create_drag_and_drop_note(collection, dnd_model, question)
                    collection.add_note(note, deck_id)
                case _:
                    print(f"Skipping unsupported questionType: {question_type}")
    finally:
        collection.close()


def _auto_detect_profile(base_path: PosixPath) -> str | None:
    if profiles := [path.parent.stem for path in base_path.glob("*/collection.anki2")]:
        if len(profiles) == 1:
            return profiles[0]
        print(f"Found multiple profiles in {base_path}")
    return None


@click.command()
@click.option("--source-path", type=click.Path(), default="~/Downloads/m200-quiz-A.json")
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
@click.option(
    "--deck-name",
    default="M200 Part A",
    show_default=True,
    help="Deck name to use",
)
def main(source_path: str, anki_path: str, profile: str, deck_name: str) -> None:
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

    questions = _get_questions(PosixPath(source_path).expanduser())
    _create_deck(collection_path, deck_name, questions)


if __name__ == "__main__":
    main()
