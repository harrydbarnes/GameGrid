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
  function stateFor(p){if(!p)return null;try{return JSON.parse(localStorage.getItem(`gamegrid:${p.mode}:${p.id}`)||'{}')}catch{return null}}
  function scopeOK(g,p){
    if(p.scope==='Retro')return g.year<=2009;
    if(p.scope==='Nintendo')return g.platforms.some(x=>NINTENDO.has(x));
    if(p.scope==='PlayStation')return g.platforms.some(x=>x.startsWith('PlayStation')||['PSP','PS Vita'].includes(x));
    if(p.scope==='Xbox')return g.platforms.some(x=>x.startsWith('Xbox'));
    return true;
  }
  function qualifies(g,p,r,c){return scopeOK(g,p)&&clues[p.rows[r]].test(g)&&clues[p.cols[c]].test(g)}
  function engagement(g){return Number(g.ratingsCount||0)}
  function poolFor(p,r,c){return games.filter(g=>qualifies(g,p,r,c)).sort((a,b)=>engagement(b)-engagement(a)||String(a.title).localeCompare(String(b.title)))}

  /*
   * Estimated rarity = engagement percentile within the exact square.
   * Lower is rarer/better. Ratings count is used as the popularity proxy because
   * review score and release recency measure quality/age rather than obviousness.
   * Ties use a midpoint percentile so equal-engagement games score equally.
   */
  function rarityFor(g,p,r,c){
    const pool=poolFor(p,r,c);if(!pool.length)return null;
    const value=engagement(g);
    const lower=pool.filter(x=>engagement(x)<value).length;
    const equal=pool.filter(x=>engagement(x)===value).length;
    const percentile=((lower+(equal*0.5))/pool.length)*100;
    return Math.round(percentile*10)/10;
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
  function escapeHtml(s){return String(s).replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m]))}
  function cover(g){return g?.coverUrl?`<img src="${g.coverUrl}" alt="${escapeHtml(g.title)} cover" loading="lazy">`:`<span>${escapeHtml((g?.title||'?').slice(0,2).toUpperCase())}</span>`}
  function referenceGrid(p,type){
    const picks=[];
    for(let i=0;i<9;i++){
      const pool=poolFor(p,Math.floor(i/3),i%3);
      picks.push(type==='best'?pool.at(-1):pool[0]);
    }
    return picks;
  }
  function gridHTML(title,subtitle,picks,p){
    return `<section class="reference-block"><div class="reference-head"><h3>${title}</h3><p>${subtitle}</p></div><div class="reference-grid">${picks.map((g,i)=>{const rar=g?rarityFor(g,p,Math.floor(i/3),i%3):null;return `<div class="reference-cell">${g?cover(g):''}<strong>${g?escapeHtml(g.title):'No answer'}</strong>${rar!=null?`<small>Rarity ${rar}</small>`:''}</div>`}).join('')}</div></section>`;
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
  function enhanceResults(){
    const dialog=$('#infoDialog'),body=$('#infoBody'),title=$('#infoTitle');
    if(!dialog?.open||!/results/i.test(title?.textContent||''))return;
    if(body.querySelector('.postgame-comparison'))return;
    const p=currentPuzzle(),state=stateFor(p);if(!p||!state?.finished)return;
    const metrics=playerMetrics(p,state);persistScore(p,state,metrics);
    const obvious=referenceGrid(p,'obvious'),best=referenceGrid(p,'best');
    const panel=document.createElement('div');panel.className='postgame-comparison';
    panel.innerHTML=`<section class="score-card"><span>Your score</span><strong>${metrics.score}<small>/900</small></strong><p>Higher is better. Each solved square is worth up to 100 points. A rarer answer earns more points, and an unanswered square earns 0.</p><div class="score-meta"><span>${metrics.solved}/9 solved</span><span>${metrics.avgRarity==null?'–':metrics.avgRarity} avg rarity</span></div></section><p class="rarity-note">Estimated rarity is the game's ratings-count percentile among valid answers for that exact square. Lower means less commonly known. This is fairer than using review score or recency, but real player-choice frequency will be the better long-term measure once available.</p><div class="reference-tabs"><button class="active" data-ref="obvious">Most obvious</button><button data-ref="best">Best rarity</button></div><div class="reference-content">${gridHTML('Most obvious completed grid','The most widely rated valid game for each square.',obvious,p)}</div><template id="bestReference">${gridHTML('Best rarity completed grid','The least widely rated valid game for each square in the current catalogue.',best,p)}</template>`;
    body.prepend(panel);
    panel.querySelectorAll('.reference-tabs button').forEach(b=>b.onclick=()=>{
      panel.querySelectorAll('.reference-tabs button').forEach(x=>x.classList.toggle('active',x===b));
      panel.querySelector('.reference-content').innerHTML=b.dataset.ref==='best'?panel.querySelector('#bestReference').content.cloneNode(true).firstElementChild.outerHTML:gridHTML('Most obvious completed grid','The most widely rated valid game for each square.',obvious,p);
    });
  }
  function avg(list,key){const vals=list.map(x=>x[key]).filter(Number.isFinite);return vals.length?Math.round(vals.reduce((a,b)=>a+b,0)/vals.length):null}
  function enhanceStats(){
    const view=$('#statsView');if(!view||view.classList.contains('hidden'))return;
    let stats;try{stats=JSON.parse(localStorage.getItem('gamegrid:stats')||'{}')}catch{return}
    const h=stats.history||[];if(!h.length)return;
    const weekAgo=Date.now()-7*86400000,w=h.filter(x=>new Date(x.playedAt||x.date).getTime()>=weekAgo);
    const comparison=$('#scoreComparison');
    if(comparison&&!comparison.dataset.scoreEnhanced){
      comparison.dataset.scoreEnhanced='1';
      comparison.insertAdjacentHTML('afterbegin',`<div class="compare-card"><span>This week</span><strong>${avg(w,'score')??'–'}</strong><small>Average score / 900</small></div><div class="compare-card"><span>All time</span><strong>${avg(h,'score')??'–'}</strong><small>Average score / 900</small></div>`);
    }
    const history=$('#resultHistory');if(history&&!history.dataset.scoreEnhanced){
      history.dataset.scoreEnhanced='1';
      [...history.querySelectorAll('.history-row')].forEach((row,i)=>{const item=h.slice().reverse()[i];if(item&&Number.isFinite(item.score))row.insertAdjacentHTML('beforeend',`<div><strong>${item.score}</strong><span>score</span></div>`)});
    }
  }
  const obs=new MutationObserver(()=>{enhanceResults();enhanceStats()});
  obs.observe(document.body,{subtree:true,childList:true,attributes:true,attributeFilter:['open','class']});
  document.addEventListener('click',()=>setTimeout(()=>{enhanceResults();enhanceStats()},0));
})();