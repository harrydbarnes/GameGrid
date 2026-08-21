(() => {
  const MIN_PARTICIPATION = 2;

  function catalogueSignal(game) {
    const count = Number(game?.ratingsCount || 0);
    const rating = Number(game?.rating || 0);
    if (!Number.isFinite(count) || count < MIN_PARTICIPATION) return null;
    const normalisedRating = rating > 10 ? rating / 10 : rating;
    return Math.log10(count + 1) * 12 + Math.max(0, normalisedRating) / 10;
  }

  function rarityFor(game, validAnswers) {
    const pool = validAnswers.filter(candidate => catalogueSignal(candidate) != null);
    const value = catalogueSignal(game);
    if (!pool.length || value == null) return null;
    const lower = pool.filter(candidate => catalogueSignal(candidate) < value).length;
    const equal = pool.filter(candidate => catalogueSignal(candidate) === value).length;
    return Math.round(((lower + equal * 0.5) / pool.length) * 1000) / 10;
  }

  function scoreAnswers(answers, pools) {
    let score = 0, unranked = 0, solved = 0;
    const rarities = [];
    answers.forEach((game, index) => {
      if (!game) {
        score += 100;
        rarities.push(null);
        return;
      }
      const rarity = rarityFor(game, pools[index] || []);
      rarities.push(rarity);
      if (Number.isFinite(rarity)) score += rarity;
      else unranked += 1;
      solved += 1;
    });
    const ranked = rarities.filter(Number.isFinite);
    return {
      score: Math.round(score), solved, unranked, rarities,
      avg: ranked.length ? Math.round(ranked.reduce((sum, rarity) => sum + rarity, 0) / ranked.length * 10) / 10 : null,
    };
  }

  const api = { MIN_PARTICIPATION, catalogueSignal, rarityFor, scoreAnswers };
  if (typeof window !== 'undefined') window.GameGridRarity = api;
  if (typeof module !== 'undefined') module.exports = api;
})();
