(() => {
  const helpButton = document.querySelector('#helpBtn');
  const infoDialog = document.querySelector('#infoDialog');
  const infoTitle = document.querySelector('#infoTitle');
  const infoBody = document.querySelector('#infoBody');
  if (!helpButton || !infoDialog || !infoTitle || !infoBody) return;

  // The maintained source of user-facing mode descriptions. app.js has
  // legacy first-paint fallbacks, but this file owns all rendered copy.
  const modes = Object.freeze({
    Classic: { tag: 'ANY ERA', summary: 'Any era, any platform, the full catalogue.' },
    Retro: { tag: 'PRE-PS2', summary: 'Pre-PS2 throwbacks, pixel dust included.' },
    Modern: { tag: 'PS2+', summary: 'PS2 onwards, newer-school adventures.' },
    Nintendo: { tag: 'NINTENDO ONLY', summary: 'Nintendo platforms only.' },
    PlayStation: { tag: 'PS FAMILY', summary: 'PlayStation-family platforms only.' },
    Xbox: { tag: 'XBOX ONLY', summary: 'Xbox-family platforms only.' },
    'Deep Cut': { tag: 'HARD MODE', summary: 'Hard mode: smaller pools and less familiar picks.', challengeTitle: 'Hard mode', challengeCopy: 'Smaller answer pools and less familiar games. Take your time.' },
    Trial: { tag: 'EXPERT FORMAT', summary: 'Expert format: maker rows, fact columns and tight pools.', challengeTitle: 'Expert format', challengeCopy: 'Rows are makers. Columns are platform, genre, era or ratings.' },
  });
  window.GameGridModeCopy = modes;
  const modeLabel = document.querySelector('#modeLabel');
  const difficultyLabel = document.querySelector('#difficultyLabel');
  const syncModeLabel = () => {
    const mode = document.querySelector('.mode-tab.active')?.dataset.mode || 'Classic';
    const difficulty = difficultyLabel?.textContent?.trim();
    const next = `DAILY ${mode.toUpperCase()} · ${modes[mode]?.tag || 'MIXED BAG'}${difficulty && difficulty !== '–' ? ` · ${difficulty.toUpperCase()}` : ''}`;
    if (modeLabel && modeLabel.textContent !== next) modeLabel.textContent = next;
  };
  syncModeLabel();
  if (modeLabel) new MutationObserver(syncModeLabel).observe(modeLabel, { childList: true, characterData: true, subtree: true });

  const modeTabs = document.querySelector('#modeTabs');
  const syncModeTabs = () => modeTabs?.querySelectorAll('.mode-tab').forEach(tab => {
    const mode = tab.dataset.mode || tab.textContent.trim();
    const summary = modes[mode]?.summary;
    if (summary) {
      tab.setAttribute('aria-label', `${mode}: ${summary}`);
      tab.title = summary;
    }
  });
  syncModeTabs();
  if (modeTabs) new MutationObserver(syncModeTabs).observe(modeTabs, { childList: true, subtree: true });

  const challengeTitle = document.querySelector('#challengeTitle');
  const challengeCopy = document.querySelector('#challengeCopy');
  const syncSpecialModeCopy = () => {
    const mode = document.querySelector('.mode-tab.active')?.dataset.mode;
    const copy = modes[mode];
    if (!copy?.challengeTitle) return;
    if (challengeTitle) challengeTitle.textContent = copy.challengeTitle;
    if (challengeCopy) challengeCopy.textContent = copy.challengeCopy;
  };
  syncSpecialModeCopy();
  if (modeTabs) new MutationObserver(syncSpecialModeCopy).observe(modeTabs, { childList: true, subtree: true, attributes: true, attributeFilter: ['class'] });

  helpButton.onclick = () => {
    infoTitle.textContent = 'How to play';
    infoBody.innerHTML = '<p>Find a video game that matches <strong>both clues</strong> for each square.</p><div class="mode-help-list"><p><strong>Classic</strong> — any era, any platform.</p><p><strong>Retro</strong> — pre-PS2 throwbacks.</p><p><strong>Modern</strong> — PS2 onwards.</p><p><strong>Nintendo, PlayStation or Xbox</strong> — that platform family only.</p><p><strong>Deep Cut</strong> — hard mode with smaller pools and less familiar picks.</p><p><strong>Trial</strong> — expert format: makers on rows, game facts on columns and tight answer pools.</p></div><p>You have nine guesses and each game can only be used once per grid.</p><p>Rarity is an estimated obscurity score for a correct answer within that square. Lower scores represent less obvious answers.</p>';
    infoDialog.showModal();
  };
})();
