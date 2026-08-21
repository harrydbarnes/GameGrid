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

console.log('game details loader passed');
