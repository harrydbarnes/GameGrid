(() => {
  const DATA=window.GAMEGRID_DATA;if(!DATA)return;
  const {puzzles,meta={}}=DATA;
  const MODES=meta.modes||[...new Set(puzzles.map(p=>p.mode))];
  const $=s=>document.querySelector(s);
  const today=new Date().toISOString().slice(0,10);
  function past(){const p=puzzles.filter(x=>x.date<today);return p.length?p:puzzles.filter(x=>x.date<=today)}
  function openPuzzle(p){const u=new URL(location.href);u.search='';u.hash='';u.searchParams.set('mode',p.mode);u.searchParams.set('puzzle',p.id);location.href=u.toString()}
  function render(){const view=$('#archiveView'),list=$('#archiveList');if(!view||view.classList.contains('hidden')||!list)return;const all=past();list.className='archive-sections';list.innerHTML=MODES.map(mode=>{const ps=all.filter(p=>p.mode===mode).sort((a,b)=>b.date.localeCompare(a.date));if(!ps.length)return'';return `<section class="archive-mode-section"><div class="archive-mode-head"><h2>${mode}</h2><span>${ps.length} grid${ps.length===1?'':'s'}</span></div><div class="archive-mode-grid">${ps.map(p=>`<button class="archive-item archive-group-item" data-mode="${p.mode}" data-id="${p.id}"><strong>${p.mode} #${p.id}</strong><span>${new Date(p.date+'T12:00:00').toLocaleDateString('en-GB',{day:'numeric',month:'short',year:'numeric'})} · ${p.difficulty||'Classic'}</span></button>`).join('')}</div></section>`}).join('');list.querySelectorAll('.archive-group-item').forEach(b=>b.onclick=()=>{const p=puzzles.find(x=>String(x.id)===b.dataset.id&&x.mode===b.dataset.mode);if(p)openPuzzle(p)})}
  $('#randomArchiveBtn')?.addEventListener('click',()=>{const all=past();if(!all.length)return;const current=((($('#puzzleTitle')?.textContent||'').match(/#(\d+)/)||[])[1]||'');const candidates=all.filter(p=>String(p.id)!==current);const pool=candidates.length?candidates:all;openPuzzle(pool[Math.floor(Math.random()*pool.length)])});
  new MutationObserver(()=>setTimeout(render,0)).observe(document.body,{subtree:true,childList:true,attributes:true,attributeFilter:['class']});
  document.addEventListener('click',e=>{if(e.target.closest?.('[data-view="archive"]')||e.target.closest?.('#puzzleTitle'))setTimeout(render,25)});
})();