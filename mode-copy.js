(() => {
  const helpButton = document.querySelector('#helpBtn');
  const infoDialog = document.querySelector('#infoDialog');
  const infoTitle = document.querySelector('#infoTitle');
  const infoBody = document.querySelector('#infoBody');
  if (!helpButton || !infoDialog || !infoTitle || !infoBody) return;

  const modeTags = {
    Classic: 'ANY ERA',
    Retro: 'PRE-PS2',
    Modern: 'PS2+',
    Nintendo: 'NINTENDO ONLY',
    PlayStation: 'PS FAMILY',
    Xbox: 'XBOX ONLY',
    'Deep Cut': 'LESS OBVIOUS',
    Trial: 'MAKER × FACTS',
  };
  const modeSummaries = {
    Classic: 'Any era, any platform — the full catalogue.',
    Retro: 'Pre-PS2 throwbacks, pixel dust included.',
    Modern: 'PS2 onwards — newer-school adventures.',
    Nintendo: 'Nintendo platforms only.',
    PlayStation: 'PlayStation-family platforms only.',
    Xbox: 'Xbox-family platforms only.',
    'Deep Cut': 'Tighter pools, deeper cuts.',
    Trial: 'Rows are makers; columns are game facts.',
  };
  const modeLabel = document.querySelector('#modeLabel');
  const difficultyLabel = document.querySelector('#difficultyLabel');
  const syncModeLabel = () => {
    const mode = document.querySelector('.mode-tab.active')?.dataset.mode || 'Classic';
    const difficulty = difficultyLabel?.textContent?.trim();
    const next = `DAILY ${mode.toUpperCase()} · ${modeTags[mode] || 'MIXED BAG'}${difficulty && difficulty !== '–' ? ` · ${difficulty.toUpperCase()}` : ''}`;
    if (modeLabel && modeLabel.textContent !== next) modeLabel.textContent = next;
  };
  syncModeLabel();
  if (modeLabel) new MutationObserver(syncModeLabel).observe(modeLabel, { childList: true, characterData: true, subtree: true });

  const modeTabs = document.querySelector('#modeTabs');
  const syncModeTabs = () => modeTabs?.querySelectorAll('.mode-tab').forEach(tab => {
    const mode = tab.dataset.mode || tab.textContent.trim();
    const summary = modeSummaries[mode];
    if (summary) {
      tab.setAttribute('aria-label', `${mode}: ${summary}`);
      tab.title = summary;
    }
  });
  syncModeTabs();
  if (modeTabs) new MutationObserver(syncModeTabs).observe(modeTabs, { childList: true, subtree: true });

  const challengeTitle = document.querySelector('#challengeTitle');
  const challengeCopy = document.querySelector('#challengeCopy');
  const syncTrialCopy = () => {
    if (document.querySelector('.mode-tab.active')?.dataset.mode !== 'Trial') return;
    if (challengeTitle) challengeTitle.textContent = 'Backstage pass';
    if (challengeCopy) challengeCopy.textContent = 'Rows are makers. Columns are platform, genre, era or ratings.';
  };
  syncTrialCopy();
  if (modeTabs) new MutationObserver(syncTrialCopy).observe(modeTabs, { childList: true, subtree: true, attributes: true, attributeFilter: ['class'] });

  helpButton.onclick = () => {
    infoTitle.textContent = 'How to play';
    infoBody.innerHTML = '<p>Find a video game that matches <strong>both clues</strong> for each square.</p><div class="mode-help-list"><p><strong>Classic</strong> — any era, any platform.</p><p><strong>Retro</strong> — pre-PS2 throwbacks.</p><p><strong>Modern</strong> — PS2 onwards.</p><p><strong>Nintendo, PlayStation or Xbox</strong> — that platform family only.</p><p><strong>Deep Cut</strong> — tighter pools, deeper cuts.</p><p><strong>Trial</strong> — rows are makers; columns are game facts.</p></div><p>You have nine guesses and each game can only be used once per grid.</p><p>Rarity is an estimated obscurity score for a correct answer within that square. Lower scores represent less obvious answers.</p>';
    infoDialog.showModal();
  };
})();
