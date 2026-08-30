# GameGrid agent rules

## Published puzzle immutability

- Treat every puzzle dated today or earlier as published and immutable.
- Ordinary UI, logic, criteria and catalogue changes must apply only to future-dated puzzles.
- Do not regenerate, backfill, renumber or otherwise alter a published puzzle, including its clues, valid answers, difficulty or mode name, unless Harry explicitly asks for that specific historical change or a full schedule reset.
- Before changing puzzle-generation behaviour, preserve the existing published schedule and verify that only dates after today can change.
- Page-only updates must reuse the current published catalogue rather than rebuild it.

## Project map and maintenance

- The site is a static GitHub Pages app. `index.html`, the CSS files and browser JavaScript are the app shell; there is no server or user account system.
- `scripts/build_catalog_v3.py` creates future puzzles and fingerprinted catalogue assets. Standard future grids require at least 15 valid answers in every cell; Deep Cut and Trial intentionally use tighter pools. The catalogue workflow downloads the previously published asset first and preserves every puzzle through today.
- The browser search index is the curated union of games used by scheduled puzzle intersections, not the full raw source catalogue. `KNOWN_PUBLISHER_ALIASES` contains reviewed first-party metadata corrections for omitted maker fields; the canonical matcher and future generator both use them, while published puzzle definitions and counts remain protected. Add a regression test for each correction and do not change historical answer counts without an explicit reset request. Keep year parsing timestamp-aware because the source exports Unix timestamps.
- `catalogue.yml` publishes the catalogue artifact. `pages.yml` reuses that artifact for normal shell releases. Keep those workflows separate.
- Game state, settings and stats are local to each browser. The fingerprinted search index is also cached locally in Cache Storage to avoid repeat downloads, but it is not player data and is replaced when the manifest changes. Do not imply cloud sync, shared accounts or cross-device persistence unless those features are explicitly added.
- `mode-copy.js` owns the maintained user-facing labels, summaries and special-mode explanation copy. Keep new or changed mode wording there, then update the README when the player-facing format changes.
- Treat the browser regression suite and catalogue validation as release gates. Extend them when changing a user-visible flow or catalogue contract.
- When adding or changing a fundamental feature, mode, storage format, generation rule, deployment process or data source, update this file and the relevant README section in the same change. Do not leave instructions that describe the old architecture.
