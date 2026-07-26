from pathlib import PosixPath

import click

import freds_oral_prep.anki.quiz.morse_code.cmd
import freds_oral_prep.anki.quiz.signal_flags.cmd
import freds_oral_prep.anki.quiz.fred_app.cmd
import freds_oral_prep.anki.quiz.minimum_flash_cards.cmd
import freds_oral_prep.anki.exam_setup.cmd
import freds_oral_prep.anki.setup_templates
from freds_oral_prep.anki.helpers import load_collection


@click.group()
@click.option(
    "--anki-path",
    type=click.Path(),
    default="~/Library/Application Support/Anki2",
    show_default=True,
    help="Path to the Anki storage location",
)
@click.option(
    "--anki-profile",
    default=None,
    show_default=True,
    help="Anki Profile to target",
)
@click.pass_context
def anki(ctx, anki_path: str, anki_profile: str) -> None:
    """Commands that read/write an Anki collection directly."""
    ctx.ensure_object(dict)
    ctx.obj["anki_collection"] = load_collection(
        PosixPath(anki_path).expanduser(),
        anki_profile,
    )
    ctx.call_on_close(ctx.obj["anki_collection"].close)


@click.group()
@click.pass_context
def create_quiz(ctx) -> None:
    """Generate quiz decks from external sources."""
    ctx.ensure_object(dict)


@click.group()
@click.pass_context
def import_quiz(ctx) -> None:
    """Import quiz decks from external sources."""
    ctx.ensure_object(dict)


anki.add_command(create_quiz, name="create-quiz")
create_quiz.add_command(freds_oral_prep.anki.quiz.morse_code.cmd.cli, name="morse-code")
create_quiz.add_command(freds_oral_prep.anki.quiz.signal_flags.cmd.cli, name="signal-flags")

anki.add_command(import_quiz, name="import-quiz")
import_quiz.add_command(freds_oral_prep.anki.quiz.fred_app.cmd.cli, name="freds-app")
import_quiz.add_command(freds_oral_prep.anki.quiz.minimum_flash_cards.cmd.cli, name="minimum-flash-cards")

anki.add_command(freds_oral_prep.anki.exam_setup.cmd.cli, name="exam-setup")

anki.add_command(freds_oral_prep.anki.setup_templates.cli, name="setup-templates")
