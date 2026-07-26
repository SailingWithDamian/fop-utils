import logging
from pathlib import PosixPath

import click

from freds_oral_prep.crew.helpers import normalise_file_name, get_authenticated_api

logger = logging.getLogger(__name__)


@click.command()
@click.option("--target-path", type=click.Path(), required=True, help="Directory to save downloaded files into")
@click.option("--overwrite/--no-overwrite", default=False, help="Overwrite existing quiz files")
@click.pass_context
def cli(ctx, target_path: str, overwrite: bool) -> None:
    """Download every document attached to your active courses' outlines as PDFs."""
    base_target = PosixPath(target_path).expanduser().resolve()

    with get_authenticated_api() as api:
        courses = api.fetch_active_courses()
        logger.info(f"Found {len(courses)} active course(s)")

        for course in courses:
            for module in api.fetch_course_outline(course["courseType"]):
                if not module["documents"]:
                    continue

                section = normalise_file_name(module["title"])
                for document in module["documents"]:
                    target = (
                        base_target / course["courseType"] / section / f"{normalise_file_name(document["name"])}.pdf"
                    )
                    if target.exists() and not overwrite:
                        logger.info(f"Skipping {target.relative_to(base_target)}")
                        continue

                    logger.info(f"Downloading {target.relative_to(base_target)}")
                    content = api.download_lms_file(document["docId"])
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(content)
