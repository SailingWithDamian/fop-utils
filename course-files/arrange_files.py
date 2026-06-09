#!/usr/bin/env python3
import click
from pathlib import PosixPath
from urllib.parse import unquote
from base64 import b64decode


def _clean_file_name(name: str) -> str:
    name = unquote(name)
    for find, replace in (("   ", " - "), ("  ", " "), (" (With Watermark) ", " ")):
        if find in name:
            name = name.replace(find, replace).strip()
    return name.strip()


def _clean_target_path(encoded_target_path: str) -> PosixPath:
    target_path = PosixPath(b64decode(encoded_target_path).decode("utf-8"))
    return target_path.parent / f"{_clean_file_name(target_path.stem)}{target_path.suffix}"


def _find_source_files(source_folder: PosixPath) -> set[tuple[PosixPath, PosixPath]]:
    return {
        (source_path, _clean_target_path(source_path.stem.split("~~")[2]))
        for source_path in source_folder.glob("Fred~~M200~~*.pdf")
    }


@click.command()
@click.argument("source_folder", type=click.Path())
@click.argument("target_folder", type=click.Path())
def main(source_folder: PosixPath, target_folder: PosixPath) -> None:
    source_files = _find_source_files(PosixPath(source_folder))
    for source_path, relative_path in source_files:
        target_path = target_folder / relative_path
        if not target_path.absolute().is_relative_to(target_folder):
            print(f"Skipping file with path transversal: {target_path}")
            continue

        print(f"Moving {source_path} to {target_path.relative_to(target_folder)}")
        target_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.move(target_path)


if __name__ == "__main__":
    main()
