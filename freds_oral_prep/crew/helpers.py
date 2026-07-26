import contextlib
import re
import logging
from pathlib import PosixPath
from typing import Iterator

import requests

from freds_oral_prep.crew.api import CrewApi, BaseApi

logger = logging.getLogger(__name__)


@contextlib.contextmanager
def get_authenticated_api(
    allow_interactive_login: bool = True, api_class: type[BaseApi] = CrewApi
) -> Iterator[BaseApi]:
    api = api_class()
    if not api.have_valid_login():
        logger.info("No valid login available")
        if not allow_interactive_login:
            raise RuntimeError("Require interactive authentication")

        if not api.perform_interactive_login():
            raise RuntimeError(f"Interactive authentication failed")

    yield api


def normalise_file_name(name: str) -> str:
    if mapping := {
        "part_a_exam": "Part A Exam",
        "ORAL_PREP": "Oral Prep",
        "NAV_RADAR": "Nav & RADAR",
        "vol 1 complete": "ALRS Vol 1",
        "Vol 2  NP282": "ALRS Vol 2",
        "vol 3 complete": "ALRS Vol 3",
        "vol 5 complete": "ALRS Vol 5",
        "volume 6 complate": "ALRS Vol 6",
    }.get(name):
        return mapping

    name = name.replace("   ", " - ").replace("_", " ").replace(": ", " - ").replace("/", " & ").replace("â", "-")
    name = "".join(c for c in name if c.isprintable() or c.isspace())
    name = re.sub(r" {2,}", " ", name)
    first_seg = re.split(r"\s*-\s*", name)[0].strip()
    if " " not in first_seg:
        name = re.sub(r"\s*-\s*", " ", name)
    else:
        name = re.sub(r"\s*-\s*", " - ", name)

    for find, replace in (
        ("   ", " - "),
        ("  ", " "),
        (" (With Watermark)", ""),
        (" (M+F) - ", " (M+F) "),
        ("Master s Guide", "Master's Guide"),
    ):
        name = name.replace(find, replace)

    name = name.strip()
    changed = True
    while changed:
        changed = False
        for suffix in (
            "(1)",
            "Final",
            "watermark",
            "- GOV.UK",
            "- GOV.UK -",
            "- GOV",
            "GOV.UK",
            "compressed",
            "complete",
            "- Compatibility Mode",
            "-",
            "Study buddy Tools",
            "PP 08",
            ".xlsx",
        ):
            stripped = re.sub(rf"\s*{re.escape(suffix)}$", "", name, flags=re.IGNORECASE).strip()
            if stripped != name:
                name = stripped
                changed = True

    for abbreviation in ("mgn", "lsa", "arpa"):
        name = re.sub(rf"\b{abbreviation}\b", abbreviation.upper(), name, flags=re.IGNORECASE)

    name = re.sub(r"(?:\s*-)?\s*BPG 22$", " - BPG 22", name)
    return name[:1].upper() + name[1:]
