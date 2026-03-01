# GameMed MVP Skeleton

This repository hosts the initial Flet-based MVP for GameMed, the gamified medication reminder app described in `docs/ENGINEERING_BLUEPRINT.md`.

## Tech stack

- Python 3.11
- Flet (Flutter renderer)
- SQLite (local, offline-first)

## Getting started

1. Install Poetry (or use pip) and dependencies:
   ```bash
   poetry install
   ```
2. Run the app in debug:
   ```bash
   poetry run python -m app.main
   ```
3. The initial run seeds the SQLite database from `data/schema.sql`.

## Project layout

See the engineering blueprint for the directory structure, domain rules, and UI spec. The current codebase ships a scaffold with placeholder implementations so you can iterate feature-by-feature.

## Next steps

- Flesh out repositories and domain engines using the provided interfaces.
- Implement ReminderEvent flows (taken/snooze/missed) and integrate the Undo manager.
- Replace placeholder UI elements with production designs from the blueprint.
