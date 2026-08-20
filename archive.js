(() => {
  const DATA=window.GAMEGRID_DATA;if(!DATA)return;
  const {puzzles,meta={}}=DATA;
  const MODES=meta.modes||[...new Set(puzzles.map(p=>p.mode))];
  const $=s=>document.querySelector(s);
  const today=new Date().toISOString().slice(0,10);

  function past(){
    const p=puzzles.filter(x=>x.date<today);
    return p.length?p:puzzles.filter(x=>x.date<=today);
  }

  // Open through app.js's existing archive handler instead of reloading the page.
  // This preserves state and avoids the shared-puzzle URL restore loop.
  function openPuzzle(p){
    if(!p)return;

    const modeBtn=[...document.querySelectorAll('#modeTabs .mode-tab')].find(b=>(b.dataset.mode||b.textContent.trim())===p.mode);
    if(modeBtn&&!modeBtn.classList.contains('active'))modeBtn.click();

    const archiveNav=document.querySelector('.nav-btn[data-view="archive"]');
    if(!archiveNav)return;

    // app.js renders its own mode-specific archive synchronously when this is clicked.
    archiveNav.click();
    const nativeItem=[...document.querySelectorAll('#archiveList .archive-item')].find(b=>String(b.dataset.id)===String(p.id));
    if(nativeItem){
      nativeItem.click();
      const u=new URL(location.href);
      u.search='';u.hash='';
      u.searchParams.set('mode',p.mode);
      u.searchParams.set('puzzle',p.id);
      history.replaceState(null,'',u.toString());
      return;
    }

    // Defensive fallback: leave the archive visible rather than entering a reload loop.
    render();
  }

  function render(){
    const view=$('#archiveView'),list=$('#archiveList');
    if(!view||view.classList.contains('hidden')||!list)return;
    const all=past();
    list.className='archive-sections';
    list.innerHTML=MODES.map(mode=>{
      const ps=all.filter(p=>p.mode===mode).sort((a,b)=>b.date.localeCompare(a.date));
      if(!ps.length)return'';
      return `<section class="archive-mode-section"><div class="archive-mode-head"><h2>${mode}</h2><span>${ps.length} grid${ps.length===1?'':'s'}</span></div><div class="archive-mode-grid">${ps.map(p=>`<button class="archive-item archive-group-item" data-mode="${p.mode}" data-id="${p.id}"><strong>${p.mode} #${p.id}</strong><span>${new Date(p.date+'T12:00:00').toLocaleDateString('en-GB',{day:'numeric',month:'short',year:'numeric'})} · ${p.difficulty||'Classic'}</span></button>`).join('')}</div></section>`;
    }).join('');
    list.querySelectorAll('.archive-group-item').forEach(b=>b.onclick=()=>{
      const p=puzzles.find(x=>String(x.id)===b.dataset.id&&x.mode===b.dataset.mode);
      openPuzzle(p);
    });
  }

  $('#randomArchiveBtn')?.addEventListener('click',e=>{
    e.preventDefault();
    e.stopPropagation();
    const all=past();if(!all.length)return;
    const currentMode=document.querySelector('.mode-tab.active')?.dataset.mode||'';
    const currentId=((($('#puzzleTitle')?.textContent||'').match(/#(\d+)/)||[])[1]||'');
    const candidates=all.filter(p=>!(p.mode===currentMode&&String(p.id)===currentId));
    const pool=candidates.length?candidates:all;
    openPuzzle(pool[Math.floor(Math.random()*pool.length)]);
  });

  new MutationObserver(()=>setTimeout(render,0)).observe(document.body,{subtree:true,childList:true,attributes:true,attributeFilter:['class']});
  document.addEventListener('click',e=>{
    if(e.target.closest?.('[data-view="archive"]')||e.target.closest?.('#puzzleTitle'))setTimeout(render,25);
  });
})();
