const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

async function main() {
const source = fs.readFileSync(require.resolve('../game-index-loader.js'), 'utf8');
const listeners = new Map();
const dispatched = [];
let workerCount = 0;
let workerInstance;

class WorkerStub {
  constructor(url) {
    this.url = url;
    this.messages = [];
    workerCount++;
    workerInstance = this;
    setTimeout(() => this.onmessage?.({ data: { type: 'ready' } }), 0);
  }

  postMessage(message) {
    this.messages.push(message);
    if (message.type === 'search') {
      setTimeout(() => this.onmessage?.({ data: {
        type: 'results',
        id: message.id,
        rows: [['game-1', 'Example Game', 2020, ['PC'], ['Adventure'], 85, 100]],
      } }), 0);
    }
  }

  terminate() {}
}

const document = {
  addEventListener(type, listener) { listeners.set(type, listener); },
  dispatchEvent(event) { dispatched.push(event); },
};
const context = {
  window: {
    GAMEGRID_CATALOG_MANIFEST: {
      indexAsset: 'index.0123456789abcdef.js',
      searchAsset: 'search.0123456789abcdef.js',
    },
    GAMEGRID_DATA: { games: [{ id: 'game-1', title: 'Before', developers: ['Studio'], publishers: ['Publisher'], coverUrl: 'cover' }] },
  },
  document,
  Worker: WorkerStub,
  CustomEvent: class CustomEventShim {
    constructor(type, init) { this.type = type; this.detail = init?.detail; }
  },
  setTimeout,
  clearTimeout,
};

vm.runInNewContext(source, context);
assert.equal(workerCount, 0);
listeners.get('click')({ target: { closest: selector => selector === '#grid .cell.empty' ? {} : null } });
await new Promise(resolve => setTimeout(resolve, 5));
assert.equal(workerCount, 1);
assert.equal(workerInstance.url, './search.0123456789abcdef.js');

const results = await context.window.GameGridSearch.query('example', []);
assert.equal(results.length, 1);
assert.equal(results[0].id, 'game-1');
assert.equal(context.window.GAMEGRID_DATA.games[0].title, 'Example Game');
assert.deepEqual(context.window.GAMEGRID_DATA.games[0].developers, ['Studio']);
assert.deepEqual(context.window.GAMEGRID_DATA.games[0].publishers, ['Publisher']);
assert.equal(context.window.GAMEGRID_DATA.games[0].coverUrl, 'cover');
assert.equal(dispatched[0].type, 'gamegrid:index-ready');

console.log('game index loader passed');
}

main().catch(error => { console.error(error); process.exitCode = 1; });
