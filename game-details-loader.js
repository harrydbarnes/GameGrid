(() => {
  let loading = false;
  function merge() {
    const details = window.GAMEGRID_DETAILS, data = window.GAMEGRID_DATA, manifest = window.GAMEGRID_CATALOG_MANIFEST;
    if (!details || !data || details.catalogHash !== manifest?.catalogHash || details.buildHash !== manifest?.buildHash) return;
    const byId = new Map(data.games.map(game => [game.id, game]));
    Object.entries(details.games || {}).forEach(([id, detail]) => Object.assign(byId.get(id) || {}, detail));
  }
  function load() {
    if (window.GAMEGRID_DETAILS) return merge();
    if (loading) return;
    const asset = window.GAMEGRID_CATALOG_MANIFEST?.detailsAsset;
    if (!/^details\.[a-f0-9]{16}\.js$/.test(asset || '')) return;
    loading = true;
    const script = document.createElement('script'); script.src = `./${asset}`; script.onload = merge;
    document.head.append(script);
  }
  document.addEventListener('click', event => {
    if (event.target.closest('.result,.cell.solved,.answer-cell,.valid-answer')) load();
  });
})();
