(() => {
  const SCHEMA_VERSION = 1;
  const KEY = 'gamegrid:stats';
  const MAX_HISTORY = 100;
  const MAX_COMPLETED = 200;
  const MAX_COUNTER = 1_000_000;
  const MAX_TOKEN_LENGTH = 120;

  const empty = () => ({
    schemaVersion: SCHEMA_VERSION,
    played: 0,
    wins: 0,
    streak: 0,
    best: 0,
    completed: [],
    history: [],
  });

  function integer(value, maximum = MAX_COUNTER) {
    const number = Number(value);
    return Number.isFinite(number) ? Math.max(0, Math.min(maximum, Math.floor(number))) : 0;
  }

  function text(value, maximum) {
    return typeof value === 'string' ? value.trim().slice(0, maximum) : '';
  }

  function dateText(value) {
    const date = text(value, 64);
    return /^\d{4}-\d{2}-\d{2}(?:T.*)?$/.test(date) ? date : '';
  }

  function historyRow(value) {
    if (!value || typeof value !== 'object' || Array.isArray(value)) return null;
    const token = text(value.token, MAX_TOKEN_LENGTH);
    const mode = text(value.mode, 40);
    const date = dateText(value.date);
    const id = Number(value.id);
    if (!token || !mode || !date || !Number.isSafeInteger(id) || id < 0) return null;
    const solved = integer(value.solved, 9);
    const rarity = Number(value.rarity);
    return {
      token,
      id,
      mode,
      date,
      playedAt: dateText(value.playedAt) || date,
      solved,
      win: value.win === true && solved === 9,
      guessesUsed: integer(value.guessesUsed, 9),
      timeSec: integer(value.timeSec, 86_400),
      rarity: Number.isFinite(rarity) && rarity >= 0 && rarity <= 100 ? rarity : null,
    };
  }

  function uniqueStrings(value, maximum) {
    if (!Array.isArray(value)) return [];
    return [...new Set(value.map(item => text(item, MAX_TOKEN_LENGTH)).filter(Boolean))].slice(-maximum);
  }

  function normalise(value) {
    const source = value && typeof value === 'object' && !Array.isArray(value) ? value : {};
    const played = integer(source.played);
    const streak = Math.min(played, integer(source.streak));
    const history = Array.isArray(source.history)
      ? source.history.map(historyRow).filter(Boolean).slice(-MAX_HISTORY)
      : [];
    const completed = uniqueStrings(source.completed, MAX_COMPLETED);
    return {
      schemaVersion: SCHEMA_VERSION,
      played,
      wins: Math.min(played, integer(source.wins)),
      streak,
      best: Math.min(played, Math.max(streak, integer(source.best))),
      completed,
      history,
    };
  }

  function parse(raw) {
    try {
      return normalise(JSON.parse(raw || 'null'));
    } catch {
      return empty();
    }
  }

  function read() {
    try {
      return parse(localStorage.getItem(KEY));
    } catch {
      return empty();
    }
  }

  function write(value) {
    try {
      localStorage.setItem(KEY, JSON.stringify(normalise(value)));
      return true;
    } catch {
      return false;
    }
  }

  function reset() {
    try {
      localStorage.removeItem(KEY);
      return true;
    } catch {
      return false;
    }
  }

  function download() {
    const blob = new Blob([JSON.stringify(read(), null, 2)], { type: 'application/json' });
    const link = Object.assign(document.createElement('a'), {
      href: URL.createObjectURL(blob),
      download: 'gamegrid-stats-backup.json',
    });
    link.click();
    setTimeout(() => URL.revokeObjectURL(link.href), 0);
  }

  function refreshStatsView() {
    window.dispatchEvent(new Event('gamegrid:stats-updated'));
    // Import and reset can only be initiated from the stats screen. Reopen it
    // through the app's existing handler so its counters and history repaint
    // without disrupting the player with a page reload.
    document.querySelector('.nav-btn[data-view="stats"]')?.click();
  }

  function installControls() {
    const view = document.querySelector('#statsView');
    if (!view || view.querySelector('.stats-storage')) return;
    const section = document.createElement('section');
    section.className = 'stats-section stats-storage';
    section.innerHTML = '<div class="stats-section-head"><div><p class="eyebrow">YOUR DATA</p><h2>Local profile</h2></div></div><p class="muted">Stats are stored only in this browser and device. Export a backup to move them; clearing site data removes them. GameGrid does not offer sign-in or cloud sync.</p><div class="stats-storage-actions"><button class="secondary-btn" data-stats-export>Export</button><button class="secondary-btn" data-stats-import>Import</button><button class="danger-btn" data-stats-reset>Reset</button><input type="file" accept="application/json" hidden data-stats-file></div>';
    view.append(section);
    section.querySelector('[data-stats-export]').onclick = download;
    const file = section.querySelector('[data-stats-file]');
    section.querySelector('[data-stats-import]').onclick = () => file.click();
    file.onchange = event => {
      const selected = event.target.files?.[0];
      if (!selected) return;
      const reader = new FileReader();
      reader.onload = () => {
        try {
          const imported = normalise(JSON.parse(reader.result));
          if (!write(imported)) throw new Error('Storage unavailable');
          refreshStatsView();
        } catch {
          alert('That backup could not be imported.');
        }
      };
      reader.readAsText(selected);
    };
    section.querySelector('[data-stats-reset]').onclick = () => {
      if (confirm('Reset all GameGrid stats on this device?')) {
        if (!reset()) alert('GameGrid could not reset its local stats.');
        else refreshStatsView();
      }
    };
  }

  function installStatsCardFormatting() {
    const cards = document.querySelector('#statsCards');
    if (!cards || cards.dataset.gamegridFormatting) return;
    cards.dataset.gamegridFormatting = 'true';
    const format = () => cards.querySelectorAll('.stat').forEach(card => {
      const label = card.querySelector('span');
      const value = card.querySelector('strong');
      if (!label || !value || !['Games indexed', 'Searchable games'].includes(label.textContent.trim())) return;
      label.textContent = 'Searchable games';
      const number = Number(value.textContent.replace(/,/g, ''));
      const searchable = Number(window.GAMEGRID_DATA?.meta?.searchableGameCount);
      const count = Number.isFinite(searchable) ? searchable : number;
      if (Number.isFinite(count)) value.textContent = new Intl.NumberFormat('en-GB').format(count);
    });
    format();
    new MutationObserver(format).observe(cards, { childList: true, subtree: true, characterData: true });
  }

  const api = { SCHEMA_VERSION, empty, normalise, parse, read, write, reset };
  if (typeof window !== 'undefined') {
    // Repair legacy or malformed state before app.js reads it, without
    // changing Storage globally or intercepting unrelated localStorage keys.
    write(read());
    document.addEventListener('DOMContentLoaded', () => { installControls(); installStatsCardFormatting(); });
    new MutationObserver(() => { installControls(); installStatsCardFormatting(); }).observe(document.documentElement, { childList: true, subtree: true });
    window.GameGridStats = api;
  }
  if (typeof module !== 'undefined') module.exports = api;
})();
