(() => {
  const manifest=window.GAMEGRID_CATALOG_MANIFEST;
  const asset=manifest?.dataAsset;
  const validHash=value=>typeof value==='string'&&/^[a-f0-9]{16}$/.test(value);
  const fail=message=>{
    window.GAMEGRID_CATALOG_INVALID=message;
    document.write('<script src="./catalog-integrity.js"><\/script>');
  };
  if(manifest?.development===true&&asset==='data.js'){
    document.write('<script src="./data.js"><\/script>');
    return;
  }
  if(!manifest||!validHash(manifest.catalogHash)||!validHash(manifest.buildHash)||!/^data\.[a-f0-9]{16}\.js$/.test(asset||'')){
    fail('The GameGrid catalogue update is incomplete. Please refresh in a moment.');
    return;
  }
  document.write(`<script src="./${asset}"><\/script><script src="./catalog-integrity.js"><\/script>`);
})();
