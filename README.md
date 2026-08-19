# GameGrid

A daily 3×3 video-game grid puzzle built for GitHub Pages.

## How to play

Pick a square and choose a video game that matches both the row and column clues. You have nine guesses to complete the grid. Progress, streaks and settings are stored locally in your browser.

## Architecture

GameGrid is intentionally a static site so it can run entirely on GitHub Pages. It uses a curated local game dataset and deterministic daily puzzles. No API keys or backend are required for gameplay.

## Local development

Serve the repository with any static web server. For example:

```bash
python -m http.server 8000
```

Then open `http://localhost:8000`.

## Deployment

Pushes to `main` trigger `.github/workflows/pages.yml`, which uploads the repository as a GitHub Pages artifact and deploys it using GitHub's official Pages actions.

In repository Settings → Pages, set **Source** to **GitHub Actions** if it is not already selected.

## Data

`data.js` contains the normalised game catalogue and puzzle definitions. The validation layer is data-driven so more games, clues and puzzle modes can be added without changing the grid UI.

Global rarity is deliberately not faked. GitHub Pages has no writable database, so this build reports local stats and is structured so a legitimate remote aggregate source can be connected later.