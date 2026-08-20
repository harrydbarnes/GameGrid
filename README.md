# GameGrid

A daily 3×3 video-game grid puzzle built for GitHub Pages.

## How to play

Pick a square and choose a video game that matches both the row and column clues. You have nine guesses to complete the grid. Progress, streaks and settings are stored locally in your browser.

## Production data

The GitHub Pages workflow builds the production data before every deployment. `scripts/build_catalog.py` downloads the open PlayMyData research dataset (IGDB-derived), normalises and deduplicates it, and retains every eligible record rather than applying a popularity cut-off. It also backfills a small, reviewed set of major recent releases so the fixed research snapshot cannot omit obvious modern answers.

The generator defines 40–60 data-driven clue types across platforms, release eras, genres, ratings and title properties. Mode-aware generation creates Classic, Retro, Nintendo, PlayStation, Xbox and Deep Cut daily puzzles through 31 December 2026.

Every generated puzzle is validated before deployment. Each of its nine intersections must have multiple valid answers in the deployed catalogue. The generated `catalog-report.json` records catalogue size, clue counts, schedule range and clue coverage for auditing.

The small `data.js` committed to the repository is a fallback for local/offline development. It includes a representative set of landmark games (including the recent-release spot checks); the GitHub Actions build replaces it with the full generated production catalogue in the Pages deployment artifact.

## Real game artwork (free)

GameGrid can enrich the production catalogue with real cover artwork from IGDB at build time. IGDB is free for non-commercial use and requires a free Twitch developer application.

1. Sign in/create a Twitch account and enable two-factor authentication.
2. Register a confidential application in the Twitch Developer Console. IGDB's documentation says `localhost` can be used as the OAuth redirect URL.
3. Generate a client secret.
4. In this GitHub repository, open **Settings → Secrets and variables → Actions**.
5. Add repository secrets named `IGDB_CLIENT_ID` and `IGDB_CLIENT_SECRET`.
6. Re-run **Deploy GameGrid to Pages** from the Actions tab, or push a commit to `main`.

`scripts/enrich_covers.py` uses those secrets only inside GitHub Actions, retrieves IGDB cover image IDs for the generated catalogue, and adds public IGDB Image CDN URLs to the deployed data. The credentials are never included in the GitHub Pages JavaScript. If the secrets are absent, deployment still succeeds and the existing letter-art fallback is used.

## Local development

Serve the repository with any static web server:

```bash
python -m http.server 8000
```

For the full production-sized dataset, run the generator/validator scripts before starting the server. The production build requires internet access because it retrieves upstream data.

## Deployment

Pushes to `main`, manual workflow dispatches and the weekly scheduled build trigger `.github/workflows/pages.yml`. The workflow generates the catalogue, optionally enriches it with IGDB artwork, validates it, uploads the static artifact and deploys through GitHub Pages.

No Netlify/Vercel/other web host is used.

## Rarity

GameGrid uses a static **catalogue-rarity** score within each square's valid answer pool. It ranks games by the source dataset's review/poll participation count, using the game rating only as a small tie-breaker; lower percentile scores are less documented in that catalogue and therefore score better. It is not a measure of how often GameGrid players guessed a title.

This is intentionally server-free: the score is recalculated deterministically from the deployed data, so all players see the same result for the same puzzle. Games without a source participation count are shown as **catalogue rank unavailable**, rather than misleadingly assigning them the tied midpoint (50); they incur the standard 100-point unranked penalty in a completed grid. True community rarity would require a writable aggregate data source.

## Data source

Production catalogue generation uses the PlayMyData multi-platform video-game research dataset published on GitHub by Riccardo Rubei et al. The source project describes the dataset as containing 99,864 unique games gathered from IGDB across Nintendo, PC, PlayStation and Xbox ecosystems. GameGrid downloads it only at build time and deploys the complete eligible, normalised index, plus the documented recent-release backfill.
