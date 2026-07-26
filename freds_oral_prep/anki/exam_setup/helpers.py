import logging
from typing import Any

from anki.collection import Collection
from anki.decks import DeckNameId

logger = logging.getLogger(__name__)

PRIORITY_TAGS = [
    "priority::high",
    "priority::medium",
    "priority::low",
]

PHASES = {
    # Everything (priority topics first)
    "intro": {
        "desiredRetention": 0.88,
        "new_per_day": 40,
        "learning_steps_minutes": [10, 1440],
        "max_review_interval_days": 30,
        "leech_action": "mark",
    },
    # Nothing new (review)
    "steady": {
        "desiredRetention": 0.90,
        "new_per_day": 0,
        "learning_steps_minutes": [10, 1440],
        "max_review_interval_days": 30,
        "leech_action": "mark",
    },
    # Stragglers
    "consolidate": {
        "desiredRetention": 0.90,
        "new_per_day": 5,
        "learning_steps_minutes": [1, 10, 1440],
        "max_review_interval_days": 14,
        "leech_action": "mark",
    },
}


def get_topic_decks(collection: Collection, parent_deck: str) -> list[DeckNameId]:
    matches = [
        deck
        for deck in collection.decks.all_names_and_ids()
        if deck.name == parent_deck or deck.name.startswith(parent_deck + "::")
    ]
    if not matches:
        raise RuntimeError(f"No decks found matching '{parent_deck}' or '{parent_deck}::*'.")
    return matches


def get_or_create_shared_config(
    collection: Collection,
    decks: list[DeckNameId],
    shared_config_name: str,
) -> dict[str, Any]:
    first_deck_dict = collection.decks.get(decks[0].id)
    first_config = collection.decks.get_config(first_deck_dict["conf"])

    if first_config["name"] != shared_config_name:
        logger.info(f"Creating shared config preset '{shared_config_name}'...")
        config_id = collection.decks.add_config_returning_id(shared_config_name, clone_from=first_config)
        config = collection.decks.get_config(config_id)
    else:
        config = first_config

    for deck in decks:
        collection.decks.set_config_id_for_deck_dict(collection.decks.get(deck.id), config["id"])

    return config


def apply_phase_settings(config: dict[str, Any], phase_name: str) -> dict[str, Any]:
    if "desiredRetention" in config:
        config["desiredRetention"] = PHASES[phase_name]["desiredRetention"]
    else:
        logger.warning("'desiredRetention' key not found in config - make sure FSRS is enabled in Deck Options first.")

    config.setdefault("new", {})
    config["new"]["perDay"] = PHASES[phase_name]["new_per_day"]
    config["new"]["delays"] = PHASES[phase_name]["learning_steps_minutes"]

    config.setdefault("rev", {})
    config["rev"]["maxIvl"] = PHASES[phase_name]["max_review_interval_days"]

    config.setdefault("lapse", {})
    config["lapse"]["leechAction"] = 1 if PHASES[phase_name]["leech_action"] == "mark" else 0

    return config


def tag_bucket(collection: Collection, card_id: int) -> int:
    tags = collection.get_card(card_id).note().tags
    for i, wanted_tag in enumerate(PRIORITY_TAGS):
        if wanted_tag in tags:
            return i
    return len(PRIORITY_TAGS)


def reprioritize_new_cards(collection: Collection, parent_deck: str) -> dict[str, int]:
    card_ids = collection.find_cards(f'deck:"{parent_deck}" is:new')
    if not card_ids:
        return {}

    ordered_card_ids = sorted(card_ids, key=lambda cid: collection.get_card(cid).due)
    ordered_card_ids.sort(key=lambda cid: tag_bucket(collection, cid))

    collection.sched.reposition_new_cards(
        ordered_card_ids,
        starting_from=0,
        step_size=1,
        randomize=False,
        shift_existing=False,
    )

    labels = PRIORITY_TAGS + ["untagged/other"]
    counts: dict[str, int] = {}
    for card_id in ordered_card_ids:
        label = labels[tag_bucket(collection, card_id)]
        counts[label] = counts.get(label, 0) + 1

    return counts


def filtered_deck_search_strings(parent_deck: str) -> dict[str, str]:
    return {
        "Weak-spot deck (lapsed cards due for review)": f"deck:{parent_deck} is:due prop:lapses>=2",
        "Priority weak-spot deck": f"deck:{parent_deck} tag:priority::high prop:lapses>=1",
        "Final full cram pass (ignore due dates, everything, oldest seen first)": (
            f"deck:{parent_deck} -is:suspended"
        ),
    }
