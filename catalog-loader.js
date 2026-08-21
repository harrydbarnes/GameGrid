(() => {
  const manifest=window.GAMEGRID_CATALOG_MANIFEST;
  const asset=manifest?.dataAsset,indexAsset=manifest?.indexAsset,searchAsset=manifest?.searchAsset;
  const validHash=value=>typeof value==='string'&&/^[a-f0-9]{16}$/.test(value);
  const fail=message=>{
    window.GAMEGRID_CATALOG_INVALID=message;
    document.write('<script src="./catalog-integrity.js"><\/script>');
  };
  if(manifest?.development===true&&asset==='data.js'){
    document.write('<script src="./data.js"><\/script>');
    return;
  }
  if(!manifest||!validHash(manifest.catalogHash)||!validHash(manifest.buildHash)||!/^puzzle\.[a-f0-9]{16}\.js$/.test(asset||'')||!/^index\.[a-f0-9]{16}\.js$/.test(indexAsset||'')||!/^search\.[a-f0-9]{16}\.js$/.test(searchAsset||'')){
    fail('The GameGrid catalogue update is incomplete. Please refresh in a moment.');
    return;
  }
  // The title index is intentionally not parser-blocking. The grid only
  // needs puzzle data at boot; game-index-loader.js starts the worker when a
  // player opens an answer picker.
  document.write(`<script src="./${asset}"><\/script><script src="./catalog-integrity.js"><\/script>`);
})();
