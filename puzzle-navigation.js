(() => {
  const titleRow = document.querySelector('.title-share-row');
  const title = document.querySelector('#puzzleTitle');
  const share = document.querySelector('#topShareBtn');
  const data = window.GAMEGRID_DATA;
  if (!titleRow || !title || !share || !data?.puzzles || !window.GameGridNavigation) return;

  const mode = () => document.querySelector('.mode-tab.active')?.dataset.mode || 'Classic';
  const currentId = () => (title.textContent.match(/#(\d+)/) || [])[1] || '';
  const grids = () => data.puzzles
    .filter(puzzle => puzzle.mode === mode())
    .slice()
    .sort((a, b) => String(a.date).localeCompare(String(b.date)) || Number(a.id) - Number(b.id));
  const londonToday = () => {
    const parts = new Intl.DateTimeFormat('en-CA', {
      timeZone: 'Europe/London', year: 'numeric', month: '2-digit', day: '2-digit',
    }).formatToParts(new Date());
    const value = type => parts.find(part => part.type === type)?.value;
    return `${value('year')}-${value('month')}-${value('day')}`;
  };
  const utcToday = () => new Date().toISOString().slice(0, 10);

  const nav = document.createElement('div');
  nav.className = 'puzzle-nav';
  nav.setAttribute('aria-label', 'Browse grids');
  nav.innerHTML = '<button type="button" class="puzzle-nav-btn" id="previousPuzzleBtn" aria-label="Previous grid" title="Previous grid">‹</button><button type="button" class="puzzle-nav-btn" id="nextPuzzleBtn" aria-label="Next grid" title="Next grid">›</button>';
  share.before(nav);

  const previous = nav.querySelector('#previousPuzzleBtn');
  const next = nav.querySelector('#nextPuzzleBtn');
  const sync = () => {
    const list = grids();
    const index = list.findIndex(puzzle => String(puzzle.id) === currentId());
    const previousGrid = list[index - 1];
    const nextGrid = list[index + 1];
    previous.disabled = !previousGrid;
    next.disabled = !nextGrid;
    previous.title = previousGrid ? `Previous grid · ${previousGrid.mode} #${previousGrid.id}` : 'No earlier grid';
    next.title = nextGrid ? `Next grid · ${nextGrid.mode} #${nextGrid.id}` : 'No later grid';
  };
  previous.onclick = () => window.GameGridNavigation.go(-1);
  next.onclick = () => window.GameGridNavigation.go(1);
  const alignTodayToLondon = () => {
    const list = grids();
    const utcCurrent = list.filter(puzzle => puzzle.date <= utcToday()).at(-1);
    const londonCurrent = list.filter(puzzle => puzzle.date <= londonToday()).at(-1);
    // Preserve an explicitly opened archive grid. Only correct the app's
    // UTC-based "today" selection when London has already moved to tomorrow.
    if (utcCurrent && londonCurrent && currentId() === String(utcCurrent.id) && utcCurrent.id !== londonCurrent.id) {
      window.GameGridNavigation.go(list.indexOf(londonCurrent) - list.indexOf(utcCurrent));
    }
  };
  sync();
  new MutationObserver(sync).observe(title, { childList: true, characterData: true, subtree: true });
  document.querySelector('#modeTabs')?.addEventListener('click', () => setTimeout(() => {
    sync();
    alignTodayToLondon();
  }, 0));
  document.querySelector('.nav-btn[data-view="today"]')?.addEventListener('click', () => setTimeout(alignTodayToLondon, 0));
  requestAnimationFrame(alignTodayToLondon);
})();
