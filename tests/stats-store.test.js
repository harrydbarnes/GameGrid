const assert = require('node:assert/strict');
const stats = require('../stats-store.js');

const malformed = stats.parse('{not json');
assert.equal(malformed.schemaVersion, 1);

const history = Array.from({ length: 230 }, (_, id) => ({ token: `Classic:${id}`, id, mode: 'Classic', date: '2026-08-21', solved: 9 }));
const normalised = stats.normalise({ played: 230, history, completed: history.map(item => item.token) });
assert.equal(normalised.schemaVersion, 1);
assert.equal(normalised.history.length, 100);
assert.equal(normalised.completed.length, 200);

const repaired = stats.normalise({
  played: 2,
  wins: 9,
  streak: 12,
  best: 4,
  completed: ['Classic:1', 'Classic:1', '', 'Classic:2'],
  history: [
    { token: 'Classic:1', id: 1, mode: 'Classic', date: '2026-08-21', solved: 9, win: true },
    null,
    { token: 42, id: 'bad', mode: {}, solved: 'bad' },
  ],
});
assert.equal(repaired.played, 2);
assert.equal(repaired.wins, 2);
assert.equal(repaired.streak, 2);
assert.equal(repaired.best, 2);
assert.deepEqual(repaired.completed, ['Classic:1', 'Classic:2']);
assert.equal(repaired.history.length, 1);
assert.equal(repaired.history[0].token, 'Classic:1');
assert.equal(repaired.history[0].solved, 9);

console.log('stats store passed');
