(() => {
  const grid = document.querySelector('#grid');
  if (!grid) return;

  let pointerDownTarget = null;
  let pointerDownX = 0;
  let pointerDownY = 0;

  grid.addEventListener('pointerdown', e => {
    if (e.pointerType !== 'touch' && e.pointerType !== 'pen') return;
    pointerDownTarget = e.target;
    pointerDownX = e.clientX;
    pointerDownY = e.clientY;
  }, { passive: true });

  grid.addEventListener('pointerup', e => {
    if (e.pointerType !== 'touch' && e.pointerType !== 'pen') return;
    if (!pointerDownTarget) return;

    const moved = Math.hypot(e.clientX - pointerDownX, e.clientY - pointerDownY);
    pointerDownTarget = null;
    if (moved > 12) return;

    const clue = e.target.closest?.('.clue:not(.corner)');
    if (clue) {
      // clue-help.js listens for click in the capture phase. Triggering click
      // explicitly makes criterion help reliable even when mobile browsers
      // suppress the synthetic click after touch interaction.
      e.preventDefault();
      clue.click();
      return;
    }

    const cell = e.target.closest?.('button.cell');
    if (cell && !cell.disabled) {
      // Preserve the existing app.js cell handler rather than duplicating game
      // state/search logic here. A programmatic click invokes the exact same
      // openSearch/showGame path used on desktop.
      e.preventDefault();
      cell.click();
    }
  }, { passive: false });
})();
