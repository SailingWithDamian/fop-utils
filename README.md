# Oral prep utilities

Helper scripts for preparing with Fred for an oral exam.

Entry point: `fred-oral-prep <group> <command> [options]`

Global options:
- `--debug/--no-debug` (enable DEBUG level logging, otherwise INFO level)

## `crew` — Crew portal

Downloads content from the Crew Academy learning platform. Requires logging in first.

| Command | Purpose |
|---|---|
| `crew login [--force/--no-force]` | Logs in to the crew portal and caches the session cookies; `--force` re-authenticates even if a valid login is cached. |
| `crew course download-resources --target-path PATH [--overwrite/--no-overwrite]` | Downloads every document attached to your active courses' outlines as PDFs. |

## `anki` — Anki deck management

All `anki` subcommands open your Anki collection directly (via the `anki` library),
so Anki must be closed while they run.

Global options:
- `--anki-path PATH` (default `~/Library/Application Support/Anki2`)
- `--anki-profile NAME` (auto-detected if you only have one profile)

### `anki create-quiz` — generate flashcard decks from external sources

| Command | Purpose |
|---|---|
| `anki create-quiz morse-code [--questions-per-round N] [--priority-cards] [--deck-name NAME]` | Builds a Morse code letter-matching deck from Wikipedia. `--priority-cards` only builds cards for request/danger/colreg letters. Default deck `Signals::Morse Code`. |
| `anki create-quiz signal-flags [--questions-per-round N] [--priority-cards]` | Builds International Code of Signals flag-matching decks from Wikipedia. `--priority-cards` tags cards covering a priority letter with `priority::high` instead of filtering them out. |

### `anki import-quiz` — import quiz decks from downloaded/bundled sources

| Command | Purpose |
|---|---|
| `anki import-quiz freds-app [--deck-name NAME] [--app-path PATH]` | Builds Anki decks from the questions bundled in Fred's offline quiz app (default app path `/Applications/Fred's Quiz App.app`). |
| `anki import-quiz minimum-flash-cards --source-path PATH` | Builds minimum-suggested flash card decks from downloaded course PDFs, one deck per section. Cards with no back content are flagged pink so they're easy to spot. |

### `anki exam-setup` — tune deck scheduling for exam prep

Group option: `--parent-deck NAME` (default `Master 200gt`)

| Command | Purpose |
|---|---|
| `anki exam-setup show-config` | Shows the subdecks under the parent deck and their current deck-options preset. |
| `anki exam-setup setup-phase {intro\|steady\|consolidate}` | Applies a study phase's deck-options preset (new-card limits, retention, leech handling) to all subdecks via one shared config preset. |
| `anki exam-setup reprioritize-cards` | Pushes cards tagged `priority::high` to the front of the new-card queue, then `priority::medium`, then everything else. Run any time after adding/tagging new cards. |
| `anki exam-setup show-filters` | Prints search strings for building cram/leech filtered decks manually in the Anki GUI (filtered decks can't be created programmatically). |

**Phases:**
- `intro` — introduce new cards (40/day), retention 0.88.
- `steady` — stop introducing new cards, pure review, retention 0.90.
- `consolidate` — trickle of stragglers (5/day), tighter learning steps, retention 0.90.

### `anki setup-templates` — install/update the custom Anki note types

Creates or updates the note types (`Drag & Drop`, `Multiple Choice`, `Ordering`, `Dynamic Image`) that
the `create-quiz`/`import-quiz`/`exam-setup` commands above rely on.

Run this once after installing dependencies, and again whenever those note-type templates change.

## `mca` — MCA exam finder

| Command | Purpose |
|---|---|
| `mca find-exam --seafarer-reference-number NUM --date-of-birth DD/MM/YYYY [--look-ahead-weeks N]` | Searches for available MCA oral exam slots and prints them, grouped by date. |
