const assert = require('node:assert/strict');
const rarity = require('../rarity-rules.js');

const ranked = { id: 'ranked', ratingsCount: 20, rating: 80 };
const unranked = { id: 'unranked', ratingsCount: 0, rating: 80 };

assert.equal(rarity.catalogueSignal(unranked), null, 'zero-participation games must not be ranked');
assert.equal(rarity.scoreAnswers([unranked], [[ranked, unranked]]).score, 0, 'unranked correct answers are score-neutral');
assert.equal(rarity.scoreAnswers([null], [[ranked]]).score, 100, 'unanswered squares retain their penalty');

console.log('rarity rules passed');
