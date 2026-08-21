const assert = require('node:assert/strict');
const stats = require('../stats-store.js');

const malformed = stats.parse('{not json');
assert.equal(malformed.schemaVersion, 1);

const history = Array.from({ length: 230 }, (_, id) => ({ token: `Classic:${id}`, id, solved: 9 }));
const normalised = stats.normalise({ played: 230, history, completed: history.map(item => item.token) });
assert.equal(normalised.schemaVersion, 1);
assert.equal(normalised.history.length, 100);
assert.equal(normalised.completed.length, 200);

console.log('stats store passed');
