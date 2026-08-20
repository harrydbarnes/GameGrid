(() => {
  const DATA=window.GAMEGRID_DATA;
  if(!DATA)return;
  const {games,clues,puzzles}=DATA;
  const $=s=>document.querySelector(s);
  const NINTENDO=new Set(['Switch','Switch 2','Wii U','Wii','GameCube','Nintendo 64','SNES','NES','Game Boy Advance','Game Boy Color','Game Boy','Nintendo DS','Nintendo 3DS','Nintendo platform']);

  function currentMode(){return document.querySelector('.mode-tab.active')?.dataset.mode||'Classic'}
  function currentPuzzle(){
    const id=Number((($('#puzzleTitle')?.textContent||'').match(/#(\d+)/)||[])[1]);
    const mode=currentMode();
    return puzzles.find(p=>p.id===id&&p.mode===mode)||puzzles.find(p=>p.id===id)||null;
  }
  function stateFor(p){
    if(!p)return null;
    try{return JSON.parse(localStorage.getItem(`gamegrid:${p.mode}:${p.id}`)||'{}')}catch{return null}
  }
  function scopeOK(g,p){
    if(p.scope==='Retro')return g.year<=2009;
    if(p.scope==='Nintendo')return g.platforms.some(x=>NINTENDO.has(x));
    if(p.scope==='PlayStation')return g.platforms.some(x=>x.startsWith('PlayStation')||['PSP','PS Vita'].includes(x));
    if(p.scope==='Xbox')return g.platforms.some(x=>x.startsWith('Xbox'));
    return true;
  }
  function qualifies(g,p,r,c){return scopeOK(g,p)&&clues[p.rows[r]].test(g)&&clues[p.cols[c]].test(g)}
  function popularity(g){return Math.log10((g.ratingsCount||0)+1)*12+(g.rating||0)/10+(g.year>=2015?2:0)}
  function poolFor(p,r,c){return games.filter(g=>qualifies(g,p,r,c)).sort((a,b)=>popularity(b)-popularity(a))}

  // Fair rarity: percentile position inside THIS square's valid-answer pool.
  // 100 = most obvious/popular, approaches 0 = rarest/least obvious.
  // This normalises for different pool sizes, so a 5-answer square and 100-answer square are comparable.
  function rarityFor(g,p,r,c){
    const pool=poolFor(p,r,c);if(!pool.length)return null;
    const rank=pool.findIndex(x=>x.id===g.id);if(rank<0)return null;
    return Math.round(((pool.length-rank)/(pool.length+1))*1000)/10;
  }
  function cellScore(rarity){return rarity==null?0:Math.max(0,100-rarity)}
  function playerMetrics(p,state){
    const rarities=[];let score=0,solved=0;
    for(let i=0;i<9;i++){
      const id=state?.answers?.[i];if(!id){rarities.push(null);continue}
      const g=games.find(x=>x.id===id);if(!g){rarities.push(null);continue}
      const r=Math.floor(i/3),c=i%3,rar=rarityFor(g,p,r,c);rarities.push(rar);score+=cellScore(rar);solved++;
    }
    return {rarities,solved,score:Math.round(score),avgRarity:solved?Math.round(rarities.filter(Number.isFinite).reduce((a,b)=>a+b,0)/solved*10)/10:null};
  }
  function cover(g){return g?.coverUrl?`<img src="${g.coverUrl}" alt="${escapeHtml(g.title)} cover" loading="lazy">`:`<span>${escapeHtml((g?.title||'?').slice(0,2).toUpperCase())}</span>`}
  function escapeHtml(s){return String(s).replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m]))}
  function referenceGrid(p,type){
    const picks=[];
    for(let i=0;i<9;i++){
      const pool=poolFor(p,Math.floor(i/3),i%3);
      picks.push(type==='best'?pool.at(-1):pool[0]);
    }
    return picks;
  }
  function gridHTML(title,subtitle,picks,p){
    return `<section class="reference-block"><div class="reference-head"><div><h3>${title}</h3><p>${subtitle}</p></div></div><div class="reference-grid">${picks.map((g,i)=>{const rar=g?rarityFor(g,p,Math.floor(i/3),i%3):null;return `<div class="reference-cell">${g?cover(g):''}<strong>${g?escapeHtml(g.title):'No answer'}</strong>${rar!=null?`<small>Rarity ${rar}</small>`:''}</div>`}).join('')}</div></section>`;
  }
  function persistScore(p,state,metrics){
    if(!state)return;
    state.rarities=metrics.rarities;state.score=metrics.score;state.avgRarity=metrics.avgRarity;
    localStorage.setItem(`gamegrid:${p.mode}:${p.id}`,JSON.stringify(state));
    try{
      const stats=JSON.parse(localStorage.getItem('gamegrid:stats')||'{}');
      if(Array.isArray(stats.history)){
        const row=stats.history.find(x=>x.token===`${p.mode}:${p.id}`||(+x.id===+p.id&&x.mode===p.mode));
        if(row){row.score=metrics.score;row.rarity=metrics.avgRarity;localStorage.setItem('gamegrid:stats',JSON.stringify(stats));}
      }
    }catch{}
  }
  function enhance(){
    const dialog=$('#infoDialog'),body=$('#infoBody'),title=$('#infoTitle');
    if(!dialog?.open||!/results/i.test(title?.textContent||''))return;
    if(body.querySelector('.postgame-comparison'))return;
    const p=currentPuzzle(),state=stateFor(p);if(!p||!state?.finished)return;
    const metrics=playerMetrics(p,state);persistScore(p,state,metrics);
    const obvious=referenceGrid(p,'obvious'),best=referenceGrid(p,'best');
    const panel=document.createElement('div');panel.className='postgame-comparison';
    panel.innerHTML=`<section class="score-card"><span>Your score</span><strong>${metrics.score}<small>/900</small></strong><p>Higher is better. Each solved square scores up to 100 points based on how rare your answer is within that square's valid-answer pool.</p><div class="score-meta"><span>${metrics.solved}/9 solved</span><span>${metrics.avgRarity==null?'–':metrics.avgRarity} avg rarity</span></div></section><div class="reference-tabs"><button class="active" data-ref="obvious">Most obvious</button><button data-ref="best">Best rarity</button></div><div class="reference-content">${gridHTML('Most obvious completed grid','The highest-popularity valid answer for each square.',obvious,p)}</div><template id="bestReference">${gridHTML('Best rarity completed grid','The lowest-popularity valid answer for each square in the current catalogue.',best,p)}</template>`;
    body.prepend(panel);
    panel.querySelectorAll('.reference-tabs button').forEach(b=>b.onclick=()=>{panel.querySelectorAll('.reference-tabs button').forEach(x=>x.classList.toggle('active',x===b));panel.querySelector('.reference-content').innerHTML=b.dataset.ref==='best'?panel.querySelector('#bestReference').content.cloneNode(true).firstElementChild.outerHTML:gridHTML('Most obvious completed grid','The highest-popularity valid answer for each square.',obvious,p)});
  }
  const obs=new MutationObserver(enhance);obs.observe(document.body,{subtree:true,childList:true,attributes:true,attributeFilter:['open']});
  document.addEventListener('click',()=>setTimeout(enhance,0));
})();