import logging

import click

import freds_oral_prep.anki.exam_setup.config
import freds_oral_prep.anki.exam_setup.phase
import freds_oral_prep.anki.exam_setup.reprioritize
import freds_oral_prep.anki.exam_setup.filtered_deck

logger = logging.getLogger(__name__)


@click.group()
@click.option(
    "--parent-deck",
    default="Master 200gt",
    show_default=True,
    help="Top-level deck prefix to operate on",
)
@click.pass_context
def cli(ctx, parent_deck: str) -> None:
    """Tune deck-options presets and card ordering for the run-up to the exam."""
    ctx.ensure_object(dict)
    ctx.obj["exam_parent_deck"] = parent_deck


cli.add_command(freds_oral_prep.anki.exam_setup.config.cli, name="show-config")
cli.add_command(freds_oral_prep.anki.exam_setup.phase.cli, name="setup-phase")
cli.add_command(freds_oral_prep.anki.exam_setup.reprioritize.cli, name="reprioritize-cards")
cli.add_command(freds_oral_prep.anki.exam_setup.filtered_deck.cli, name="show-filters")
