#!/usr/bin/env python3
from freds_oral_prep.lib.cmd.general import cli
from freds_oral_prep.lib.cmd.crew import crew
from freds_oral_prep.lib.cmd.anki import anki
from freds_oral_prep.lib.cmd.mca import mca

cli.add_command(crew)
cli.add_command(anki)
cli.add_command(mca)

try:
    from freds_oral_prep.private.cmd import private
except ImportError:
    pass
else:
    cli.add_command(private)


if __name__ == "__main__":
    cli()
