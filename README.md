# GameGrid

A daily 3×3 video-game grid puzzle built for GitHub Pages.

## How to play

Pick a square and choose a video game that matches both the row and column clues. You have nine guesses to complete the grid. Progress, streaks and settings are stored locally in your browser.

## Production data

The GitHub Pages workflow builds the production data before every deployment. `scripts/build_catalog.py` downloads the open PlayMyData research dataset (IGDB-derived), normalises and deduplicates it, then produces a browser-friendly catalogue capped at 6,000 games.

The generator defines 40–60 data-driven clue types across platforms, release eras, genres, ratings and title properties. It also creates daily Classic puzzles from 17 August through 31 December 2026.

Every generated puzzle is validated before deployment. Each of its nine intersections must have at least three valid answers in the deployed catalogue. The generated `catalog-report.json` records catalogue size, clue counts, schedule range and clue coverage for auditing.

The small `data.js` committed to the repository is a fallback for local/offline development. The GitHub Actions build replaces it with the generated production catalogue in the Pages deployment artifact.

## Local development

Serve the repository with any static web server:

```bash
python -m http.server 8000
```

For the full production-sized dataset, run:

```bash
python scripts/build_catalog.py
python scripts/validate_catalog.py
python -m http.server 8000
```

The build step requires internet access because it retrieves the upstream research CSVs.

## Deployment

Pushes to `main`, manual workflow dispatches and the weekly scheduled build trigger `.github/workflows/pages.yml`. The workflow generates the catalogue, validates it, uploads the static artifact and deploys through GitHub Pages.

No Netlify/Vercel/other web host is used.

## Rarity

Global rarity is deliberately not faked. GitHub Pages has no writable database, so this build reports local stats and is structured so a legitimate remote aggregate source can be connected later.

## Data source

Production catalogue generation uses the PlayMyData multi-platform video-game research dataset published on GitHub by Riccardo Rubei et al. The source project describes the dataset as containing 99,864 unique games gathered from IGDB across Nintendo, PC, PlayStation and Xbox ecosystems. GameGrid downloads it only at build time and deploys a substantially smaller normalised index.
