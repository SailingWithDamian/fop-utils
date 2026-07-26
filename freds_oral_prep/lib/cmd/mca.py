import click

import freds_oral_prep.mca.exam_finder.cmd


@click.group()
@click.pass_context
def mca(ctx) -> None:
    """Commands for the MCA (Maritime and Coastguard Agency) exam portal."""
    ctx.ensure_object(dict)


mca.add_command(freds_oral_prep.mca.exam_finder.cmd.cli, name="find-exam")
