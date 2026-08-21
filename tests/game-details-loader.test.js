const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const source = fs.readFileSync(require.resolve('../game-details-loader.js'), 'utf8');
const listeners = new Map();
const dispatched = [];
const document = {
  addEventListener(type, listener) { listeners.set(type, listener); },
  dispatchEvent(event) { dispatched.push(event); },
  createElement() { return {}; },
  head: {
    append(script) {
      context.window.GAMEGRID_DETAILS = {
        catalogHash: 'catalog-hash',
        buildHash: 'build-hash',
        games: { 'game-1': { coverUrl: '/cover.jpg', developers: ['Studio'] } },
      };
      script.onload();
    },
  },
};
class CustomEventShim {
  constructor(type, init) { this.type = type; this.detail = init?.detail; }
}
const context = {
  window: {
    GAMEGRID_CATALOG_MANIFEST: {
      catalogHash: 'catalog-hash',
      buildHash: 'build-hash',
      detailsAsset: 'details.0123456789abcdef.js',
    },
    GAMEGRID_DATA: { games: [{ id: 'game-1', title: 'Example', developers: [], publishers: [] }] },
  },
  document,
  CustomEvent: CustomEventShim,
};

vm.runInNewContext(source, context);
listeners.get('click')({ target: { closest: () => ({}) } });

assert.equal(dispatched.length, 1);
assert.equal(dispatched[0].type, 'gamegrid:details-ready');
assert.equal(dispatched[0].detail.count, 1);
assert.deepEqual(Array.from(context.window.GAMEGRID_DATA.games[0].developers), ['Studio']);
listeners.get('click')({ target: { closest: () => ({}) } });
assert.equal(dispatched.length, 1);

function makeFailureHarness() {
  const harness = { listeners: new Map(), dispatched: [], scripts: [] };
  const context = {
    window: {
      GAMEGRID_CATALOG_MANIFEST: {
        catalogHash: 'catalog-hash',
        buildHash: 'build-hash',
        detailsAsset: 'details.0123456789abcdef.js',
      },
      GAMEGRID_DATA: { games: [{ id: 'game-1', title: 'Example', developers: [], publishers: [] }] },
    },
    document: {
      addEventListener(type, listener) { harness.listeners.set(type, listener); },
      dispatchEvent(event) { harness.dispatched.push(event); },
      createElement() { return {}; },
      head: { append(script) { harness.scripts.push(script); } },
    },
    CustomEvent: CustomEventShim,
  };
  vm.runInNewContext(source, context);
  return { ...harness, context };
}

const failureHarness = makeFailureHarness();
failureHarness.listeners.get('click')({ target: { closest: () => ({}) } });
assert.equal(failureHarness.scripts.length, 1);
failureHarness.scripts[0].onerror();
assert.equal(failureHarness.scripts.length, 2);
assert.match(failureHarness.scripts[1].src, /\?details-retry=1$/);
failureHarness.scripts[1].onerror();
assert.equal(failureHarness.scripts.length, 2);
assert.equal(failureHarness.dispatched.at(-1).type, 'gamegrid:details-unavailable');
assert.equal(failureHarness.dispatched.at(-1).detail.reason, 'load');

const staleHarness = makeFailureHarness();
staleHarness.listeners.get('click')({ target: { closest: () => ({}) } });
staleHarness.context.window.GAMEGRID_DETAILS = {
  catalogHash: 'old-catalog-hash',
  buildHash: 'old-build-hash',
  games: {},
};
staleHarness.scripts[0].onload();
assert.equal(staleHarness.scripts.length, 2);
assert.match(staleHarness.scripts[1].src, /\?details-retry=1$/);
staleHarness.scripts[1].onload();
assert.equal(staleHarness.scripts.length, 2);
assert.equal(staleHarness.dispatched.at(-1).type, 'gamegrid:details-unavailable');
assert.equal(staleHarness.dispatched.at(-1).detail.reason, 'stale');
assert.equal(staleHarness.context.window.GameGridDetails.unavailable, true);

console.log('game details loader passed');
