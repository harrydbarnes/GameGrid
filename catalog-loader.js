(() => {
  const manifest=window.GAMEGRID_CATALOG_MANIFEST;
  const asset=manifest?.dataAsset,indexAsset=manifest?.indexAsset,searchAsset=manifest?.searchAsset;
  const validHash=value=>typeof value==='string'&&/^[a-f0-9]{16}$/.test(value);
  const loadingAttribute='data-gamegrid-catalog-loading';

  function showFailure(message){
    window.GAMEGRID_CATALOG_INVALID=message;
    document.documentElement.removeAttribute(loadingAttribute);
    if(document.querySelector('.catalog-load-error'))return;
    document.body.replaceChildren(Object.assign(document.createElement('main'),{
      className:'catalog-load-error',
      innerHTML:`<p class="eyebrow">CATALOGUE UPDATE</p><h1>GameGrid is updating</h1><p>${message}</p><button type="button">Reload</button>`,
    }));
    document.querySelector('.catalog-load-error button')?.addEventListener('click',()=>location.reload());
  }

  function loadScript(src){
    return new Promise((resolve,reject)=>{
      const script=document.createElement('script');
      script.src=src;
      script.async=false;
      script.onload=()=>resolve();
      script.onerror=()=>reject(new Error(`Could not load ${src}`));
      document.head.append(script);
    });
  }

  async function start(){
    document.documentElement.setAttribute(loadingAttribute,'');
    const development=manifest?.development===true;
    if(!manifest||(development
      ? asset!=='data.js'
      : !validHash(manifest.catalogHash)||!validHash(manifest.buildHash)||
        !/^puzzle\.[a-f0-9]{16}\.js$/.test(asset||'')||
        !/^index\.[a-f0-9]{16}\.js$/.test(indexAsset||'')||
        !/^search\.[a-f0-9]{16}\.js$/.test(searchAsset||''))){
      throw new Error('The GameGrid catalogue update is incomplete. Please refresh in a moment.');
    }

    // Load the data explicitly rather than using document.write. That keeps a
    // large fingerprinted catalogue from holding the HTML parser open and
    // gives the app one unambiguous readiness point.
    await loadScript(`./${asset}`);
    if(!development){
      await loadScript('./catalog-integrity.js');
      if(window.GAMEGRID_CATALOG_INVALID)throw new Error(window.GAMEGRID_CATALOG_INVALID);
    }

    const placeholders=[...document.querySelectorAll('script[data-gamegrid-src]')];
    for(const placeholder of placeholders){
      const src=placeholder.getAttribute('data-gamegrid-src');
      if(!src)continue;
      await loadScript(src);
      placeholder.remove();
    }
    document.documentElement.removeAttribute(loadingAttribute);
    window.GAMEGRID_APP_READY=true;
    document.dispatchEvent(new CustomEvent('gamegrid:ready'));
  }

  window.GameGridCatalogReady=start().catch(error=>{
    showFailure(error?.message||'The catalogue could not be loaded. Please refresh in a moment.');
    return false;
  });
})();
