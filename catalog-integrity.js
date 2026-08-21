(() => {
  const fail=message=>{
    window.GAMEGRID_CATALOG_INVALID=message;
    delete window.GAMEGRID_DATA;
    document.body.replaceChildren(Object.assign(document.createElement('main'),{
      className:'catalog-load-error',
      innerHTML:`<p class="eyebrow">CATALOGUE UPDATE</p><h1>GameGrid is updating</h1><p>${message}</p><button type="button">Reload</button>`
    }));
    document.querySelector('.catalog-load-error button')?.addEventListener('click',()=>location.reload());
  };
  if(window.GAMEGRID_CATALOG_INVALID){fail(window.GAMEGRID_CATALOG_INVALID);return}
  const manifest=window.GAMEGRID_CATALOG_MANIFEST,data=window.GAMEGRID_DATA,meta=data?.meta;
  const valid=manifest&&data&&meta&&
    meta.catalogHash===manifest.catalogHash&&
    meta.buildHash===manifest.buildHash&&
    meta.dataAsset===manifest.dataAsset&&
    meta.indexAsset===manifest.indexAsset&&
    meta.detailsAsset===manifest.detailsAsset&&
    Array.isArray(data.games)&&data.games.length===meta.gameCount&&
    Array.isArray(data.puzzles)&&
    data.puzzles.every(p=>p.catalogHash===manifest.catalogHash&&p.buildHash===manifest.buildHash);
  if(!valid)fail('The catalogue and puzzle schedule do not match. Please refresh in a moment.');
})();
