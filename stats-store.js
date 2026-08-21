(() => {
  const SCHEMA_VERSION = 1, KEY = 'gamegrid:stats', MAX_HISTORY = 100, MAX_COMPLETED = 200;
  const empty = () => ({ schemaVersion: SCHEMA_VERSION, played: 0, wins: 0, streak: 0, best: 0, completed: [], history: [] });
  const integer = value => Number.isFinite(Number(value)) ? Math.max(0, Math.floor(Number(value))) : 0;
  function normalise(value) {
    const source = value && typeof value === 'object' ? value : {};
    const history = Array.isArray(source.history) ? source.history.filter(item => item && typeof item === 'object').slice(-MAX_HISTORY) : [];
    const completed = Array.isArray(source.completed) ? source.completed.filter(item => typeof item === 'string').slice(-MAX_COMPLETED) : [];
    return { schemaVersion: SCHEMA_VERSION, played: integer(source.played), wins: integer(source.wins), streak: integer(source.streak), best: integer(source.best), completed, history };
  }
  function parse(raw) { try { return normalise(JSON.parse(raw || 'null')); } catch { return empty(); } }
  function read() { return parse(localStorage.getItem(KEY)); }
  function write(value) { localStorage.setItem(KEY, JSON.stringify(normalise(value))); }
  function download() {
    const blob = new Blob([JSON.stringify(read(), null, 2)], { type: 'application/json' });
    const link = Object.assign(document.createElement('a'), { href: URL.createObjectURL(blob), download: 'gamegrid-stats-backup.json' });
    link.click(); setTimeout(() => URL.revokeObjectURL(link.href), 0);
  }
  function installControls() {
    const view = document.querySelector('#statsView'); if (!view || view.querySelector('.stats-storage')) return;
    const section = document.createElement('section'); section.className = 'stats-section stats-storage';
    section.innerHTML = '<div class="stats-section-head"><div><p class="eyebrow">YOUR DATA</p><h2>Local profile</h2></div></div><p class="muted">Stats are stored only in this browser and device. Export a backup to move them; clearing site data removes them. GameGrid does not offer sign-in or cloud sync.</p><div class="stats-storage-actions"><button class="secondary-btn" data-stats-export>Export</button><button class="secondary-btn" data-stats-import>Import</button><button class="danger-btn" data-stats-reset>Reset</button><input type="file" accept="application/json" hidden data-stats-file></div>';
    view.append(section);
    section.querySelector('[data-stats-export]').onclick = download;
    const file = section.querySelector('[data-stats-file]');
    section.querySelector('[data-stats-import]').onclick = () => file.click();
    file.onchange = event => { const selected = event.target.files?.[0]; if (!selected) return; const reader = new FileReader(); reader.onload = () => { try { write(parse(reader.result)); location.reload(); } catch { alert('That backup could not be imported.'); } }; reader.readAsText(selected); };
    section.querySelector('[data-stats-reset]').onclick = () => { if (confirm('Reset all GameGrid stats on this device?')) { localStorage.removeItem(KEY); location.reload(); } };
  }
  const api = { SCHEMA_VERSION, empty, normalise, parse, read, write };
  if (typeof window !== 'undefined') {
    const originalSet = Storage.prototype.setItem;
    Storage.prototype.setItem = function(key, value) {
      if (this === localStorage && key === KEY) return originalSet.call(this, key, JSON.stringify(parse(value)));
      return originalSet.call(this, key, value);
    };
    // Repair legacy/malformed state before app.js reads it.
    try { write(read()); } catch {}
    document.addEventListener('DOMContentLoaded', installControls);
    new MutationObserver(installControls).observe(document.documentElement, { childList: true, subtree: true });
    window.GameGridStats = api;
  }
  if (typeof module !== 'undefined') module.exports = api;
})();
