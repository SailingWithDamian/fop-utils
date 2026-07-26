import logging

import click

from freds_oral_prep.anki.exam_setup.helpers import PHASES, get_topic_decks, get_or_create_shared_config, \
    apply_phase_settings

logger = logging.getLogger(__name__)


@click.command()
@click.argument("phase", type=click.Choice(sorted(PHASES.keys())))
@click.pass_context
def cli(ctx, phase: str) -> None:
    """Apply a study PHASE's deck-options preset (new-card limits, retention, leech handling) to all subdecks."""
    collection = ctx.obj["anki_collection"]
    parent_deck = ctx.obj["exam_parent_deck"]
    shared_config_name = f"{parent_deck} Config"
    decks = get_topic_decks(collection, parent_deck)
    config = get_or_create_shared_config(collection, decks, shared_config_name)
    config = apply_phase_settings(config, phase)
    collection.decks.update_config(config)

    logger.info(
        f"Applied '{phase}' phase settings to {len(decks)} decks under '{parent_deck}' "
        f"(shared config: '{shared_config_name}')."
    )
    logger.info(f"  desiredRetention  -> {config.get('desiredRetention')}")
    logger.info(f"  new.perDay        -> {config['new']['perDay']}")
    logger.info(f"  new.delays        -> {config['new']['delays']}")
    logger.info(f"  rev.maxIvl        -> {config['rev']['maxIvl']}")
    logger.info(f"  lapse.leechAction -> {config['lapse']['leechAction']}")
