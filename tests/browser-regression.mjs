#!/usr/bin/env node
/**
 * Small browser-level smoke suite for the server-free GameGrid app.
 *
 * Local runs use a deterministic production-shaped fixture because generated
 * catalogue assets are intentionally not committed. CI sets
 * GAMEGRID_BROWSER_USE_GENERATED=1 after the catalogue build so these same
 * flows run against the real fingerprinted assets.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import vm from 'node:vm';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const HASHES = {
  catalogHash: 'aaaaaaaaaaaaaaaa',
  buildHash: 'bbbbbbbbbbbbbbbb',
};
const ASSETS = {
  dataAsset: `puzzle.${HASHES.buildHash}.js`,
  indexAsset: `index.${HASHES.buildHash}.js`,
  searchAsset: `search.${HASHES.buildHash}.js`,
  detailsAsset: `details.${HASHES.buildHash}.js`,
};

function manifestSource(manifest) {
  return `window.GAMEGRID_CATALOG_MANIFEST=${JSON.stringify(manifest)};\n`;
}

function parseManifest(source) {
  const match = source.match(/window\.GAMEGRID_CATALOG_MANIFEST=(\{.*\});/s);
  if (!match) return null;
  try { return JSON.parse(match[1]); } catch { return null; }
}

function fallbackData() {
  const source = fs.readFileSync(path.join(ROOT, 'data.js'), 'utf8');
  const sandbox = { window: {} };
  vm.runInNewContext(source, sandbox, { filename: 'data.js' });
  return { source, data: sandbox.window.GAMEGRID_DATA };
}

function makeFixture() {
  const { source, data } = fallbackData();
  const manifest = { ...HASHES, ...ASSETS };
  const meta = {
    gameCount: data.games.length,
    puzzleGameCount: data.games.length,
    playableGameCount: data.games.length,
    clueCount: Object.keys(data.clues).length,
    puzzleCount: data.puzzles.length,
    modes: ['Classic'],
    source: 'browser regression fixture',
    ...HASHES,
    ...ASSETS,
  };
  const marker = 'return {games,clues,puzzles};';
  assert.ok(source.includes(marker), 'fallback data return shape changed');
  const dataAsset = source.replace(marker, `
  games.forEach(game => { game.developers = []; game.publishers = []; });
  puzzles.forEach(puzzle => Object.assign(puzzle, ${JSON.stringify(HASHES)}));
  const futurePuzzle = { ...puzzles.filter(puzzle => puzzle.mode === 'Classic').at(-1), id: 999, date: '2099-01-01' };
  Object.assign(futurePuzzle, ${JSON.stringify(HASHES)});
  puzzles.push(futurePuzzle);
  return {games,clues,puzzles,meta:${JSON.stringify(meta)}};
`);
  const rows = data.games.map(game => [
    game.id,
    game.title,
    game.year,
    game.platforms,
    game.tags,
    game.rating ?? 0,
    game.ratingsCount ?? 0,
  ]);
  const indexAsset = `globalThis.GAMEGRID_INDEX=${JSON.stringify(rows)};\n`;
  const searchAsset = `const INDEX_ASSET=${JSON.stringify(`./${ASSETS.indexAsset}`)};
importScripts(INDEX_ASSET);
const rows=Array.isArray(self.GAMEGRID_INDEX)?self.GAMEGRID_INDEX:[];
function normalise(value){return String(value??'').toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').replace(/[^a-z0-9 ]/g,' ').replace(/\\s+/g,' ').trim()}
function score(row,q){const title=normalise(row[1]);if(!q)return 1;if(title===q)return 10000;if(title.startsWith(q))return 8000;if(title.includes(q))return 5000;return -1}
self.postMessage({type:'ready',count:rows.length});
self.onmessage=event=>{const message=event.data||{};if(message.type!=='search')return;const query=normalise(message.query),excluded=new Set(message.excluded||[]);const result=rows.filter(row=>!excluded.has(row[0])).map(row=>({row,score:score(row,query)})).filter(item=>item.score>=0).sort((a,b)=>b.score-a.score||String(a.row[1]).localeCompare(String(b.row[1]))).map(item=>item.row);self.postMessage({type:'results',id:message.id,rows:result.slice(0,20)});};
`;
  const detailGames = Object.fromEntries(data.games.map(game => [game.id, {
    developers: game.developers || [],
    publishers: game.publishers || [],
    ...(game.id === 'bioshock' ? { coverUrl: 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="40" height="54"%3E%3Crect width="40" height="54" fill="%23ff5a36"/%3E%3C/svg%3E' } : {}),
  }]));
  const detailsAsset = `window.GAMEGRID_DETAILS=${JSON.stringify({ ...HASHES, games: detailGames })};\n`;
  const richIds = Object.entries(detailGames)
    .filter(([, detail]) => detail.developers.length || detail.publishers.length)
    .map(([id]) => id);
  return { manifest, richIds, files: {
    [ASSETS.dataAsset]: dataAsset,
    [ASSETS.indexAsset]: indexAsset,
    [ASSETS.searchAsset]: searchAsset,
    [ASSETS.detailsAsset]: detailsAsset,
  } };
}

function generatedRichIds(manifest) {
  try {
    const source = fs.readFileSync(path.join(ROOT, manifest.detailsAsset), 'utf8');
    const match = source.match(/window\.GAMEGRID_DETAILS=(\{.*\});/s);
    const details = match && JSON.parse(match[1]);
    return Object.entries(details?.games || {})
      .filter(([, detail]) => detail?.developers?.length || detail?.publishers?.length)
      .map(([id]) => id);
  } catch {
    return [];
  }
}

function contentType(name) {
  if (name.endsWith('.html')) return 'text/html; charset=utf-8';
  if (name.endsWith('.css')) return 'text/css; charset=utf-8';
  if (name.endsWith('.js')) return 'application/javascript; charset=utf-8';
  if (name.endsWith('.json')) return 'application/json; charset=utf-8';
  if (name.endsWith('.svg')) return 'image/svg+xml';
  return 'application/octet-stream';
}

function startServer() {
  const fixture = makeFixture();
  const generatedManifest = parseManifest(fs.readFileSync(path.join(ROOT, 'catalog-manifest.js'), 'utf8'));
  const useGenerated = process.env.GAMEGRID_BROWSER_USE_GENERATED === '1'
    && generatedManifest?.catalogHash
    && generatedManifest?.dataAsset
    && fs.existsSync(path.join(ROOT, generatedManifest.dataAsset));
  const active = useGenerated
    ? { manifest: generatedManifest, richIds: generatedRichIds(generatedManifest), files: null, mode: 'generated' }
    : { ...fixture, mode: 'fixture' };
  let releaseVersion = active.mode === 'generated' ? 'generated-release-a' : 'fixture-release-a';
  if (active.mode === 'generated') {
    const shell = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');
    const match = shell.match(/GAMEGRID_RELEASE_VERSION\s*=\s*(["'])(.*?)\1/);
    if (match?.[2] && !match[2].includes('__GAMEGRID_RELEASE_VERSION__')) releaseVersion = match[2];
  }
  const server = http.createServer((request, response) => {
    const pathname = decodeURIComponent(new URL(request.url || '/', 'http://127.0.0.1').pathname);
    if (pathname === '/catalog-manifest.js') {
      response.writeHead(200, { 'content-type': 'application/javascript; charset=utf-8' });
      response.end(manifestSource(active.manifest));
      return;
    }
    if (pathname === '/release-version.json') {
      response.writeHead(200, { 'content-type': 'application/json; charset=utf-8' });
      response.end(JSON.stringify({ version: releaseVersion }));
      return;
    }
    const relative = pathname === '/' ? 'index.html' : pathname.replace(/^\/+/, '');
    if (active.files?.[relative]) {
      response.writeHead(200, { 'content-type': contentType(relative) });
      response.end(active.files[relative]);
      return;
    }
    if (relative === 'index.html') {
      let source = fs.readFileSync(path.join(ROOT, relative), 'utf8');
      source = source.replace(
        /(GAMEGRID_RELEASE_VERSION\s*=\s*["'])(.*?)(["'])/,
        (_match, prefix, _oldVersion, suffix) => `${prefix}${releaseVersion}${suffix}`,
      );
      response.writeHead(200, { 'content-type': contentType(relative) });
      response.end(source);
      return;
    }
    const target = path.resolve(ROOT, relative);
    if (target !== ROOT && !target.startsWith(`${ROOT}${path.sep}`)) {
      response.writeHead(404); response.end(); return;
    }
    fs.stat(target, (error, stat) => {
      if (error || !stat.isFile()) { response.writeHead(404); response.end(); return; }
      response.writeHead(200, { 'content-type': contentType(relative) });
      fs.createReadStream(target).pipe(response);
    });
  });
  return new Promise(resolve => {
    server.listen(0, '127.0.0.1', () => {
      const address = server.address();
      resolve({
        base: `http://127.0.0.1:${address.port}/`,
        active,
        setReleaseVersion: value => { releaseVersion = value; },
        getReleaseVersion: () => releaseVersion,
        close: () => new Promise(done => server.close(done)),
      });
    });
  });
}

async function releaseVersionPrompt(browser, server) {
  const { context, page } = await boot(browser, server);
  assert.equal(await page.locator('.update-prompt').count(), 0, JSON.stringify({
    expected: await page.evaluate(() => window.GAMEGRID_RELEASE_VERSION),
    served: server.getReleaseVersion(),
  }));
  server.setReleaseVersion('fixture-release-b');
  await page.evaluate(() => window.GameGridRelease?.check?.());
  await page.locator('.update-prompt').waitFor();
  assert.match(await page.locator('.update-prompt').innerText(), /New version available.*refresh/i);
  await page.getByRole('button', { name: 'Refresh' }).click();
  await page.waitForURL(/release=fixture-release-b/);
  await page.waitForSelector('#grid');
  assert.equal(await page.locator('.update-prompt').count(), 0);
  await context.close();
}

async function boot(browser, server, options = {}) {
  const context = await browser.newContext(options);
  const page = await context.newPage();
  await page.goto(server.base, { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('#grid');
  await page.waitForFunction(() => Boolean(window.GAMEGRID_DATA?.games?.length));
  return { context, page };
}

async function findReachableRichCandidate(page, richIds) {
  return page.evaluate(ids => {
    const today = new Date().toISOString().slice(0, 10);
    const grids = window.GAMEGRID_DATA.puzzles
      .filter(puzzle => puzzle.mode === 'Classic')
      .slice()
      .sort((a, b) => String(a.date).localeCompare(String(b.date)) || Number(a.id) - Number(b.id));
    const current = grids.reduce((latest, puzzle, index) => puzzle.date <= today ? index : latest, -1);
    for (let gridIndex = Math.max(0, current); gridIndex < grids.length; gridIndex++) {
      const puzzle = grids[gridIndex];
      for (let rowIndex = 0; rowIndex < 3; rowIndex++) {
        for (let columnIndex = 0; columnIndex < 3; columnIndex++) {
          const row = window.GAMEGRID_DATA.clues[puzzle.rows[rowIndex]];
          const column = window.GAMEGRID_DATA.clues[puzzle.cols[columnIndex]];
          const game = window.GAMEGRID_DATA.games.find(item => ids.includes(item.id) && row.test(item) && column.test(item));
          if (game) return { id: game.id, title: game.title, index: rowIndex * 3 + columnIndex, offset: gridIndex - Math.max(0, current) };
        }
      }
    }
    return null;
  }, richIds);
}

async function openCandidateGrid(page, candidate) {
  if (candidate.offset) await page.evaluate(offset => {
    for (let step = 0; step < offset; step++) window.GameGridNavigation.go(1);
  }, candidate.offset);
}

async function malformedStorageBoot(browser, server) {
  const context = await browser.newContext();
  await context.addInitScript(() => {
    localStorage.setItem('gamegrid:stats', '{not-json');
  });
  const page = await context.newPage();
  await page.goto(server.base, { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('#grid');
  const state = await page.evaluate(() => ({
    stats: window.GameGridStats.read(),
    raw: localStorage.getItem('gamegrid:stats'),
  }));
  assert.equal(state.stats.schemaVersion, 1);
  assert.equal(state.stats.played, 0);
  assert.deepEqual(state.stats.history, []);
  assert.doesNotMatch(state.raw, /not-json/);
  await context.close();
}

async function statsNormalisationAndReset(browser, server) {
  const { context, page } = await boot(browser, server);
  const dialogs = [];
  page.on('dialog', async dialog => {
    dialogs.push(dialog.type());
    if (dialog.type() === 'confirm') await dialog.accept();
    else await dialog.dismiss();
  });
  await page.locator('.stats-text-btn').click();
  await page.locator('.stats-storage').waitFor();
  const backup = {
    schemaVersion: 999,
    played: 3,
    wins: 99,
    streak: 99,
    best: 99,
    completed: ['Classic:1', 'Classic:1'],
    history: [{ token: 'Classic:1', id: 1, mode: 'Classic', date: '2026-08-23', solved: 9, win: true, guessesUsed: 1, timeSec: 10, rarity: 20 }, { broken: true }],
  };
  // Exercise the persisted-data normaliser directly. Synthetic file uploads have
  // proved browser-dependent in CI, while the import handler uses this same store.
  assert.equal(await page.evaluate(value => window.GameGridStats.write(value), backup), true);
  await page.waitForFunction(() => window.GameGridStats.read().played === 3);
  const imported = await page.evaluate(() => window.GameGridStats.read());
  assert.equal(imported.wins, 3);
  assert.equal(imported.streak, 3);
  assert.equal(imported.best, 3);
  assert.deepEqual(imported.completed, ['Classic:1']);
  assert.equal(imported.history.length, 1);
  // The storage controls are already mounted in this view. Re-clicking its
  // active nav button makes Playwright wait on a synchronous view re-render,
  // without adding coverage for the normalisation or reset behaviour.
  await page.locator('[data-stats-reset]').click();
  // Reset deliberately refreshes the current Stats view in place. It no
  // longer reloads the page or returns the player to the grid.
  await page.waitForFunction(() => !document.querySelector('#statsView')?.classList.contains('hidden'));
  await page.waitForFunction(() => Boolean(window.GameGridStats));
  await page.waitForFunction(() => window.GameGridStats.read().played === 0);
  const reset = await page.evaluate(() => window.GameGridStats.read());
  assert.equal(reset.wins, 0);
  assert.deepEqual(reset.completed, []);
  assert.ok(dialogs.includes('confirm'));
  await context.close();
}

async function firstLazyDetailClick(browser, server) {
  const { context, page } = await boot(browser, server);
  const detailsUrl = new URL(server.active.manifest.detailsAsset, server.base).href;
  let detailRequests = 0;
  page.on('request', request => {
    if (request.url() === detailsUrl) detailRequests++;
  });
  assert.equal(await page.evaluate(() => Boolean(window.GAMEGRID_DETAILS)), false);
  const candidate = await findReachableRichCandidate(page, server.active.richIds);
  assert.ok(candidate?.title, 'fixture must provide a valid answer cell');
  await openCandidateGrid(page, candidate);
  await page.locator('#grid .cell.empty').nth(candidate.index).click();
  await page.locator('#searchDialog[open]').waitFor();
  await page.locator('#gameSearch').fill(candidate.title);
  const result = page.locator('.result').filter({ hasText: candidate.title }).first();
  await result.waitFor();
  await result.click();
  await page.waitForFunction(() => !document.querySelector('#searchDialog')?.open);
  await page.waitForFunction(() => Boolean(window.GAMEGRID_DETAILS));
  await page.waitForFunction(id => {
    const game = window.GAMEGRID_DATA.games.find(item => item.id === id);
    return Boolean(game?.developers?.length && game?.publishers?.length);
  }, candidate.id);
  const rich = await page.evaluate(id => window.GAMEGRID_DATA.games.find(item => item.id === id), candidate.id);
  await page.locator('#grid .cell.solved').first().click();
  await page.locator('#infoDialog[open]').waitFor();
  const detailText = await page.locator('#infoDialog').innerText();
  assert.match(detailText, new RegExp(candidate.title.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')));
  assert.match(detailText, new RegExp(String(rich.developers[0]).replace(/[.*+?^${}()|[\]\\]/g, '\\$&')));
  assert.equal(detailRequests, 1);
  await context.close();
}

async function mobileAnswerSearch(browser, server) {
  const { context, page } = await boot(browser, server, { viewport: { width: 390, height: 844 }, hasTouch: true });
  const indexUrl = new URL(server.active.manifest.indexAsset, server.base).href;
  assert.equal(await page.locator('#searchDialog[open]').count(), 0, 'answer sheet must stay hidden until a grid cell is selected');
  const indexLoaded = page.waitForRequest(request => request.url() === indexUrl);
  await page.locator('#grid .cell.empty').first().click();
  await page.locator('#searchDialog[open]').waitFor();
  await indexLoaded;
  assert.equal(await page.locator('#searchResults .result').count(), 0);
  assert.match(await page.locator('#searchResults').innerText(), /Start typing to search games/i);
  await page.locator('#gameSearch').fill('BioShock');
  const result = page.locator('.result').filter({ hasText: 'BioShock' }).first();
  await result.waitFor();
  assert.equal(await page.locator('#gameSearch').evaluate(element => document.activeElement === element), true);
  const geometry = await page.locator('#searchDialog').evaluate(element => {
    const box = element.getBoundingClientRect();
    const visualHeight = window.visualViewport?.height || window.innerHeight;
    const resultBox = element.querySelector('.result')?.getBoundingClientRect();
    return { height: box.height, bottom: box.bottom, visualHeight, resultBottom: resultBox?.bottom || 0 };
  });
  assert.ok(geometry.height >= geometry.visualHeight * 0.7, `mobile search sheet is too short: ${JSON.stringify(geometry)}`);
  assert.ok(geometry.bottom <= geometry.visualHeight + 2, `mobile search sheet is clipped: ${JSON.stringify(geometry)}`);
  assert.ok(geometry.resultBottom <= geometry.bottom + 1, `mobile result is clipped: ${JSON.stringify(geometry)}`);
  await context.close();
}

async function modeExplainer(browser, server) {
  const { context, page } = await boot(browser, server, { viewport: { width: 390, height: 844 }, hasTouch: true });
  const activeMode = page.locator('.mode-tab.active');
  assert.match(await activeMode.getAttribute('aria-label'), /any era, any platform/i);
  assert.match(await page.locator('#modeLabel').innerText(), /ANY ERA/i);
  await page.locator('#helpBtn').click();
  const help = await page.locator('#infoBody').innerText();
  assert.match(help, /Modern\s+—\s+PS2 onwards/i);
  assert.match(help, /Retro\s+—\s+pre-PS2/i);
  const trial = page.locator('.mode-tab[data-mode="Trial"]');
  if (await trial.count()) {
    await page.locator('#infoDialog button[aria-label="Close"]').click();
    await trial.click();
    await page.waitForFunction(() => document.querySelector('.mode-tab.active')?.dataset.mode === 'Trial');
    assert.match(await page.locator('#modeLabel').innerText(), /MAKER.*FACTS/i);
    assert.match(await page.locator('#challengeCopy').innerText(), /Rows are makers/i);
  }
  await context.close();
}

async function onboardingWalkthrough(browser, server) {
  const context = await browser.newContext();
  const page = await context.newPage();
  await page.goto(`${server.base}?onboarding=1`, { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('#grid');
  const tour = page.locator('.gamegrid-onboarding');
  await tour.waitFor();
  assert.equal(await tour.locator('.gamegrid-onboarding-progress span').count(), 4);
  assert.match(await tour.locator('h2').innerText(), /One grid/i);
  await tour.getByRole('button', { name: 'Next' }).click();
  assert.match(await tour.locator('h2').innerText(), /Classic is the all-rounder/i);
  assert.match(await tour.locator('.gamegrid-onboarding-body').innerText(), /Modern.*platform-specific/i);
  assert.equal(await page.locator('#modeTabs .mode-tab.active.onboarding-clue-highlight').count(), 1);
  await tour.getByRole('button', { name: 'Next' }).click();
  assert.match(await tour.locator('h2').innerText(), /Criteria explain themselves/i);
  await tour.getByRole('button', { name: 'Next' }).click();
  assert.match(await tour.locator('h2').innerText(), /less obvious/i);
  await context.close();
}

async function puzzleNavigation(browser, server) {
  const { context, page } = await boot(browser, server, { viewport: { width: 390, height: 844 }, hasTouch: true });
  const previous = page.locator('#previousPuzzleBtn');
  const next = page.locator('#nextPuzzleBtn');
  await previous.waitFor();
  const current = await page.locator('#puzzleTitle').innerText();
  const navigation = await page.evaluate(() => {
    const mode = document.querySelector('.mode-tab.active')?.dataset.mode || 'Classic';
    const id = Number((document.querySelector('#puzzleTitle')?.textContent.match(/#(\d+)/) || [])[1]);
    const list = window.GAMEGRID_DATA.puzzles.filter(puzzle => puzzle.mode === mode).slice().sort((a, b) => String(a.date).localeCompare(String(b.date)) || Number(a.id) - Number(b.id));
    const index = list.findIndex(puzzle => Number(puzzle.id) === id);
    return { expectedNext: list[index + 1]?.id, nextIsLast: index + 1 === list.length - 1 };
  });
  assert.ok(navigation.expectedNext, 'fixture must provide a later grid');
  assert.equal(await next.isDisabled(), false);
  await next.click();
  await page.waitForFunction(id => document.querySelector('#puzzleTitle')?.textContent.includes(`#${id}`), navigation.expectedNext);
  assert.equal(await next.isDisabled(), navigation.nextIsLast);
  await previous.click();
  await page.waitForFunction(title => document.querySelector('#puzzleTitle')?.textContent === title, current);
  await context.close();
}

async function splitActionLayout(browser, server) {
  const { context, page } = await boot(browser, server, { viewport: { width: 390, height: 844 }, hasTouch: true });
  const action = page.locator('.game-actions');
  await action.waitFor();
  const initial = await action.evaluate(element => ({
    visible: [...element.querySelectorAll('button')].filter(button => !button.hidden && getComputedStyle(button).display !== 'none').length,
    height: element.getBoundingClientRect().height,
  }));
  assert.equal(initial.visible, 1);
  assert.ok(initial.height <= 52, `hidden Reset should not reserve a second row: ${JSON.stringify(initial)}`);
  await page.evaluate(() => {
    const mode = document.querySelector('.mode-tab.active')?.dataset.mode || 'Classic';
    const id = (document.querySelector('#puzzleTitle')?.textContent.match(/#(\d+)/) || [])[1];
    const key = `gamegrid:${mode}:${id}`;
    const state = JSON.parse(localStorage.getItem(key) || '{}');
    state.guesses = 8;
    state.finished = false;
    localStorage.setItem(key, JSON.stringify(state));
  });
  await page.reload({ waitUntil: 'domcontentloaded' });
  await page.waitForSelector('#grid');
  await action.waitFor();
  const buttons = action.locator('button:visible');
  assert.equal(await buttons.count(), 2);
  const widths = await buttons.evaluateAll(elements => elements.map(element => element.getBoundingClientRect().width));
  assert.ok(Math.abs(widths[0] / widths[1] - 2) < 0.08, `expected a 2:1 Give up/Reset ratio, got ${widths.join(':')}`);
  await page.evaluate(() => {
    const mode = document.querySelector('.mode-tab.active')?.dataset.mode || 'Classic';
    const id = (document.querySelector('#puzzleTitle')?.textContent.match(/#(\d+)/) || [])[1];
    const key = `gamegrid:${mode}:${id}`;
    const state = JSON.parse(localStorage.getItem(key) || '{}');
    state.finished = true;
    localStorage.setItem(key, JSON.stringify(state));
  });
  await page.reload({ waitUntil: 'domcontentloaded' });
  await page.waitForSelector('#grid');
  await action.waitFor();
  assert.equal(await action.locator('button:visible').count(), 1);
  assert.equal(await action.locator('.restart-btn').isVisible(), true);
  await context.close();
}

async function deferredDetailsFailure(browser, server) {
  const { context, page } = await boot(browser, server);
  let detailRequests = 0;
  await page.route(`**/${server.active.manifest.detailsAsset}*`, async route => {
    detailRequests++;
    await route.fulfill({
      status: 200,
      contentType: 'application/javascript',
      body: 'window.GAMEGRID_DETAILS={catalogHash:"stale-catalog-hash",buildHash:"stale-build-hash",games:{}};',
    });
  });
  const candidate = await findReachableRichCandidate(page, server.active.richIds);
  assert.ok(candidate?.title, 'fixture must provide a valid answer cell');
  await openCandidateGrid(page, candidate);
  await page.locator('#grid .cell.empty').nth(candidate.index).click();
  await page.locator('#searchDialog[open]').waitFor();
  await page.locator('#gameSearch').fill(candidate.title);
  const result = page.locator('.result').filter({ hasText: candidate.title }).first();
  await result.waitFor();
  await result.click();
  await page.waitForFunction(() => Boolean(window.GameGridDetails?.unavailable));
  assert.equal(detailRequests, 2);
  assert.equal(await page.evaluate(() => Boolean(window.GAMEGRID_CATALOG_INVALID)), false);
  await page.locator('#grid .cell.solved').first().click();
  await page.locator('#infoDialog[open]').waitFor();
  await page.locator('.details-fallback').waitFor();
  assert.match(await page.locator('#infoDialog').innerText(), /additional details are unavailable right now/i);
  await context.close();
}

async function staleAssetMismatch(browser, server) {
  const context = await browser.newContext();
  const page = await context.newPage();
  const stale = { ...server.active.manifest, catalogHash: 'cccccccccccccccc', buildHash: 'dddddddddddddddd' };
  await page.route('**/catalog-manifest.js', route => route.fulfill({
    status: 200,
    contentType: 'application/javascript',
    body: manifestSource(stale),
  }));
  await page.goto(server.base, { waitUntil: 'domcontentloaded' });
  await page.locator('.catalog-load-error').waitFor();
  const message = await page.locator('.catalog-load-error').innerText();
  assert.match(message, /catalogue and puzzle schedule do not match/i);
  await context.close();
}

const tests = [
  ['malformed storage boot', malformedStorageBoot],
  ['stats normalisation and reset', statsNormalisationAndReset],
  ['first lazy-detail click', firstLazyDetailClick],
  ['answer search on a mobile viewport', mobileAnswerSearch],
  ['mode explainer', modeExplainer],
  ['introduction walkthrough', onboardingWalkthrough],
  ['past and future puzzle navigation', puzzleNavigation],
  ['give up and reset split layout', splitActionLayout],
  ['deferred details fallback', deferredDetailsFailure],
  ['stale asset mismatch', staleAssetMismatch],
  ['release version prompt', releaseVersionPrompt],
];

async function main() {
  const server = await startServer();
  let browser;
  const failures = [];
  console.log(`Browser regression server: ${server.base} (${server.active.mode} assets)`);
  try {
    browser = await chromium.launch({ headless: true, executablePath: process.env.PLAYWRIGHT_EXECUTABLE_PATH || chromium.executablePath() });
    for (const [name, test] of tests) {
      try {
        await test(browser, server);
        console.log(`PASS ${name}`);
      } catch (error) {
        failures.push({ name, error });
        console.error(`FAIL ${name}: ${error.stack || error}`);
      }
    }
  } finally {
    await browser?.close();
    await server.close();
  }
  if (failures.length) process.exitCode = 1;
}

main().catch(error => {
  console.error(error.stack || error);
  process.exitCode = 1;
});
