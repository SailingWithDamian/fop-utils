import logging
import random
from pathlib import PosixPath
from anki.collection import Collection

from freds_oral_prep.lib.anki.cards.flip_card import BasicFlipCard
from freds_oral_prep.lib.anki.cards.drag_and_drop import DragAndDropCard
from freds_oral_prep.lib.anki.cards.multiple_choice import MultipleChoiceCard
from freds_oral_prep.lib.anki.cards.ordering import OrderingCard
from freds_oral_prep.lib.anki.cards.dynamic_image import DynamicImageCard

logger = logging.getLogger(__name__)

AnyCard = BasicFlipCard | DragAndDropCard | MultipleChoiceCard | OrderingCard | DynamicImageCard


def load_collection(base_path: PosixPath, profile_name: str | None) -> Collection | None:
    base_path = PosixPath(base_path).expanduser()
    if not base_path.is_dir():
        logger.error(f"Config path does not exist: {base_path}")
        return None

    if not profile_name:
        anki_profiles = [path.parent.stem for path in base_path.glob("*/collection.anki2")]
        if len(anki_profiles) == 1:
            logger.debug(f"Selecting Anki profile: {anki_profiles[0]}")
            profile_name = anki_profiles[0]
        elif len(anki_profiles) > 1:
            logger.warning(f"Found multiple profiles in {base_path}")
            return None
        else:
            logger.error(f"Found no profiles in {base_path}")
            return None

    collection_path = base_path / profile_name / "collection.anki2"
    if not collection_path.is_file():
        logger.error(f"Invalid Anki profile path: {collection_path}")
        return None

    return Collection(collection_path)


def get_or_create_deck(collection: Collection, deck_name: str) -> int:
    for deck in collection.decks.all_names_and_ids():
        if deck.name == deck_name:
            logger.info(f"Found existing deck: {deck_name}")
            return deck.id

    logger.info(f"Creating new deck: {deck_name}")
    return collection.decks.add_normal_deck_with_name(deck_name).id


def get_card_model(collection: Collection, model_name: str) -> str:
    if model := collection.models.by_name(model_name):
        return model

    raise RuntimeError(f"Model {model_name} not found.")


def load_card_models(collection: Collection, cards: list[AnyCard]) -> dict[str, Collection]:
    card_models = {}
    for card in cards:
        if card.MODEL_NAME not in card_models:
            card_models[card.MODEL_NAME] = get_card_model(collection, card.MODEL_NAME)
    return card_models


def create_drag_and_drop_pairs(
    title: str,
    question: str,
    questions: list[tuple[str, str]],
    number_per_round: int,
    explanations: list[str] | None = None,
    tags: list[list[str]] | None = None,
) -> list[AnyCard]:
    if number_per_round > 1:
        question_groups = [questions[i : i + number_per_round] for i in range(0, len(questions), number_per_round)]
        explanation_groups = (
            [explanations[i : i + number_per_round] for i in range(0, len(explanations), number_per_round)]
            if explanations
            else None
        )
        tag_groups = [tags[i : i + number_per_round] for i in range(0, len(tags), number_per_round)] if tags else None
    else:
        question_groups = [[signal] for signal in questions]
        explanation_groups = [[e] for e in explanations] if explanations else None
        tag_groups = [[t] for t in tags] if tags else None

    expected_cards = []
    for idx, question_group in enumerate(question_groups):
        data = {"title": title, "question": question}

        if explanation_groups:
            group_exps = [e for e in explanation_groups[idx] if e]
            if group_exps:
                data["explanation"] = group_exps[0] if len(group_exps) == 1 else "<br>".join(group_exps)

        if tag_groups:
            group_tags = {tag for tags_for_question in tag_groups[idx] for tag in tags_for_question}
            if group_tags:
                data["tags"] = tuple(sorted(group_tags))

        for i, (q, answer) in enumerate(question_group, start=1):
            data |= {f"question_{i}": q, f"answer_{i}": answer}

        if number_per_round - len(question_group):
            ignore_answers = {answer for (_, answer) in question_group}
            for i in range(len(question_group) + 1, number_per_round + 1):
                answer = random.choice([answer for (_, answer) in questions if answer not in ignore_answers])
                ignore_answers.add(answer)
                data[f"answer_{i}"] = answer

        expected_cards.append(DragAndDropCard(**data))

    return expected_cards


def add_cards_to_deck(
    collection: Collection,
    deck_id: int,
    deck_name: str,
    expected_cards: list[AnyCard],
) -> tuple[int, int]:
    if not expected_cards:
        return 0, 0

    card_models = load_card_models(collection, expected_cards)

    question_keys_by_model: dict[str, set] = {}
    for card in expected_cards:
        if card.MODEL_NAME not in question_keys_by_model:
            question_keys_by_model[card.MODEL_NAME] = set()
        question_keys_by_model[card.MODEL_NAME].update(card.get_question_data().keys())

    existing_fingerprints = set()
    for existing_nid in collection.find_notes(f'deck:"{deck_name}"'):
        existing_note = collection.get_note(existing_nid)
        if question_keys := question_keys_by_model.get(existing_note.note_type()["name"], set()):
            existing_fingerprints.add(frozenset((k, existing_note[k]) for k in question_keys if existing_note[k]))

    added = skipped = 0
    for expected_card in expected_cards:
        fingerprint = frozenset((k, v) for k, v in expected_card.get_question_data().items() if v)
        if fingerprint in existing_fingerprints:
            skipped += 1
            continue
        note = collection.new_note(card_models[expected_card.MODEL_NAME])
        for k, v in expected_card.get_note_data().items():
            note[k] = v
        for tag in expected_card.tags:
            note.add_tag(tag)
        collection.add_note(note, deck_id)
        added += 1

    return added, skipped


def flag_cards_with_empty_field(collection: Collection, deck_name: str, field_name: str, flag: int) -> int:
    """Set an Anki flag (1-7, e.g. 5 for pink) on every card whose note has an empty `field_name`."""
    flagged = 0
    for nid in collection.find_notes(f'deck:"{deck_name}"'):
        note = collection.get_note(nid)
        if field_name in note and not note[field_name]:
            collection.set_user_flag_for_cards(flag, collection.card_ids_of_note(nid))
            flagged += 1
    return flagged


def create_multiple_choice_card(
    title: str,
    question: str,
    answers: list[tuple[str, bool]],
    image: str | None = None,
    explanation: str | None = None,
    tags: list[str] | None = None,
) -> MultipleChoiceCard:
    return MultipleChoiceCard(
        title=title,
        question=question,
        answers=tuple(answers),
        image=image,
        explanation=explanation,
        tags=tuple(tags or ()),
    )


def create_ordering_card(
    title: str,
    question: str,
    items: list[str],
    explanation: str | None = None,
    tags: list[str] | None = None,
) -> OrderingCard:
    return OrderingCard(
        title=title,
        question=question,
        items=tuple(items),
        explanation=explanation,
        tags=tuple(tags or ()),
    )


def create_dynamic_image_card(
    title: str,
    question: str,
    description: str,
    board_points: list[dict],
    grid_is_black: bool,
    categories: list[dict],
    explanation: str | None = None,
    tags: list[str] | None = None,
) -> DynamicImageCard:
    return DynamicImageCard(
        title=title,
        question=question,
        description=description,
        board_points=tuple(board_points),
        grid_is_black=grid_is_black,
        categories=tuple(categories),
        explanation=explanation,
        tags=tuple(tags or ()),
    )
