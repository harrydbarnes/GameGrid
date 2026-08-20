(() => {
  const DATA=window.GAMEGRID_DATA;if(!DATA)return;
  const $=s=>document.querySelector(s);
  const {puzzles}=DATA;
  const mode=document.querySelector('.mode-tab.active')?.dataset.mode||localStorage.getItem('gamegrid:mode')||'Classic';
  const id=Number((($('#puzzleTitle')?.textContent||'').match(/#(\d+)/)||[])[1]);
  const p=puzzles.find(x=>x.id===id&&x.mode===mode)||puzzles.find(x=>x.id===id);
  if(!p)return;
  const storageKey=`gamegrid:${p.mode}:${p.id}`;
  const fingerprint=[p.date,p.mode,(p.rows||[]).join(','),(p.cols||[]).join(',')].join('|');
  const fpKey=`${storageKey}:fingerprint`;
  const priorFp=localStorage.getItem(fpKey);
  let state=null;try{state=JSON.parse(localStorage.getItem(storageKey)||'null')}catch{}
  // A completed grid is always marked finished by app.js. An unfinished state
  // with no lives is therefore a stranded write from an older build; reset it
  // rather than leaving every empty cell disabled forever.
  if(state&&!state.finished&&Number(state.guesses)<=0){
    localStorage.removeItem(storageKey);
    state=null;
  }
  // Old builds stored state only by mode + numeric id. If that id now points to regenerated
  // clue content, an old finished state can lock the new grid. Reset only that puzzle state,
  // never the player's aggregate stats/history.
  if(state && !priorFp){
    localStorage.removeItem(storageKey);
    localStorage.setItem(fpKey,fingerprint);
    if(!sessionStorage.getItem('gamegrid:migrated:'+storageKey)){
      sessionStorage.setItem('gamegrid:migrated:'+storageKey,'1');
      location.reload();
      return;
    }
  } else if(priorFp && priorFp!==fingerprint){
    localStorage.removeItem(storageKey);
    localStorage.setItem(fpKey,fingerprint);
    if(!sessionStorage.getItem('gamegrid:migrated:'+storageKey+':'+fingerprint)){
      sessionStorage.setItem('gamegrid:migrated:'+storageKey+':'+fingerprint,'1');
      location.reload();
      return;
    }
  } else if(!priorFp){
    localStorage.setItem(fpKey,fingerprint);
  }
})();
