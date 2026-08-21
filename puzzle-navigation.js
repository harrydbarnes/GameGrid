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
  sync();
  new MutationObserver(sync).observe(title, { childList: true, characterData: true, subtree: true });
  document.querySelector('#modeTabs')?.addEventListener('click', () => setTimeout(sync, 0));
})();
