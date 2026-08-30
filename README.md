# GameGrid 🎮

GameGrid is a daily 3×3 video-game puzzle. Pick a square, name a game and make sure it fits both clues. Easy to understand, surprisingly good at making you remember a weird PlayStation 2 game from 2004.

It is a static site built for GitHub Pages, with no sign-in, no server and no ads.

## How to play

Each grid has three row clues and three column clues. A correct answer must satisfy the pair for its square. Every game can be used only once, and you have nine guesses to fill all nine squares.

The main modes keep the format familiar while changing the playground:

- **GameGrid / Classic**: the full catalogue.
- **RetroGrid**: games released before 2000.
- **ModernGrid**: games released in 2000 or later.
- **NintendoGrid**, **PlayStationGrid** and **XboxGrid**: games from that platform family.
- **DeepCutGrid**: smaller, tougher intersections for people who enjoy a very specific challenge.
- **TrialGrid**: expert-format grids with maker rows, game-fact columns and tighter pools.

Lower rarity scores are better. They are based on catalogue popularity signals, not live player guesses, so they are a fun guide to obscurity rather than a global leaderboard. 🕹️

Progress, streaks and settings stay in the browser you are using. You can export your local stats as a backup, but there is no account or cloud sync.

## Daily puzzles that stay put 📅

Once a puzzle is live, it is frozen. Today’s grid and every past grid keep their clues, answers, difficulty and numbering, even when GameGrid’s rules improve later.

Changes to the generator or clue rules are used for future dates only. Reworking old grids, backfilling them or resetting the schedule is an intentional operation and only happens when explicitly requested.

## Behind the scenes

GameGrid builds its catalogue from the open PlayMyData research dataset, which is derived from IGDB. The build normalises and deduplicates the source, keeps a broad catalogue rather than a popularity cut-off, and adds a small reviewed backfill for obvious recent releases that a fixed data snapshot can miss.

Before a future grid is published, every one of its nine intersections is checked for valid answers. Standard modes require at least fifteen valid games per cell, giving you room to think without turning every square into a giveaway. Specialist modes deliberately allow tighter pools. The generator also avoids impossible time combinations and redundant nested clues.

The app loads the small puzzle data first. The answer search contains the curated set of games that can appear in the scheduled intersections, rather than noisy source records that were never counted as puzzle answers. Trial uses the same reviewed first-party corrections in generation and in the browser when the upstream snapshot omits a well-known publisher, and release timestamps are converted to their real calendar years. The search index warms quietly after the page is ready and is saved on the device by its fingerprint, so repeat visits reuse it until the catalogue changes. Covers and other rich game details stay deferred, helping the first load remain quick. ⚡

## Artwork

Where available, covers are enriched from IGDB during the build. If artwork cannot be loaded, GameGrid falls back to its letter-art treatment, so the game remains playable without any external image dependency.

To enable IGDB cover enrichment for this repository, add `IGDB_CLIENT_ID` and `IGDB_CLIENT_SECRET` as GitHub Actions secrets. They are used only during the build and are never sent to the browser.

## Development

Serve the app locally with any static web server:

```bash
python -m http.server 8000
```

The committed `data.js` is a compact offline fallback. The production catalogue is generated in GitHub Actions and requires internet access to retrieve the upstream dataset.

Useful checks:

```bash
python3 -m unittest discover -s scripts -p 'test_*.py'
npm ci
npx playwright install chromium
npm run test:browser
```

## Publishing

There are two workflows:

1. **Publish GameGrid catalogue** generates and validates the fingerprinted catalogue bundle. It first downloads the last published bundle so every live puzzle is preserved.
2. **Deploy GameGrid to Pages** reuses that bundle for normal app, design and copy updates, then deploys the site.

This separation means a button tweak does not rebuild the quiz schedule. GitHub Pages is the only host used.
