(() => {
  const $=s=>document.querySelector(s);
  function mode(){return document.querySelector('.mode-tab.active')?.dataset.mode||'Classic'}
  function puzzleId(){return ((($('#puzzleTitle')?.textContent||'').match(/#(\d+)/)||[])[1]||'')}
  function puzzleUrl(){const u=new URL(location.href);u.search='';u.hash='';u.searchParams.set('mode',mode());u.searchParams.set('puzzle',puzzleId());return u.toString()}
  function toast(t){const e=$('#toast');if(!e)return;e.textContent=t;e.classList.add('show');setTimeout(()=>e.classList.remove('show'),1800)}
  async function shareGrid(){
    const grid=window.GameGridName?.(mode())||`${mode()}Grid`;
    const title=`${grid} #${puzzleId()}`;
    const text=`🎮 Today's ${grid} challenge\n${grid} #${puzzleId()}\n\nNine squares. Nine games. How low can you score?`;
    const url=puzzleUrl();
    try{if(navigator.share){await navigator.share({title,text,url});return}}catch(e){if(e?.name==='AbortError')return}
    const payload=`${text}\n\n${url}`;
    try{await navigator.clipboard.writeText(payload);toast('Challenge link copied')}
    catch{window.prompt('Copy this challenge:',payload)}
  }
  function criterionNode(target){return target.closest?.('#grid .clue:not(.corner)')||null}
  function showCriterion(node){
    if(window.GameGridCriterionHelp?.showForNode?.(node))return true;
    const data=window.GAMEGRID_DATA;if(!data)return false;
    const pMode=mode(),id=Number(puzzleId());
    const p=data.puzzles.find(x=>x.id===id&&x.mode===pMode);if(!p)return false;
    const nodes=[...document.querySelectorAll('#grid .clue:not(.corner)')],idx=nodes.indexOf(node);if(idx<0)return false;
    const clueId=idx<3?p.cols[idx]:p.rows[idx-3],c=data.clues[clueId];if(!c)return false;
    const title=$('#infoTitle'),body=$('#infoBody'),dialog=$('#infoDialog');if(!title||!body||!dialog)return false;
    title.textContent=c.label;
    body.innerHTML=`<div class="clue-explanation"><span class="eyebrow">CRITERION EXPLAINED</span><p>A valid answer must satisfy “${c.label}” according to the GameGrid catalogue data.</p></div>`;
    try{if(!dialog.open)dialog.showModal()}catch{return false}
    return true;
  }
  document.addEventListener('click',e=>{
    const share=e.target.closest?.('#topShareBtn');
    if(share){e.preventDefault();e.stopImmediatePropagation();shareGrid();return}
    const clue=criterionNode(e.target);
    if(clue){e.preventDefault();e.stopImmediatePropagation();showCriterion(clue)}
  },true);

  // Primary views replace the page's main content. Start each one at the top
  // instead of preserving an Archive scroll position on the shorter Stats or
  // Today view.
  document.addEventListener('click',event=>{
    if(!event.target.closest?.('.nav-btn[data-view]'))return;
    window.setTimeout(()=>window.scrollTo({top:0,left:0,behavior:'auto'}),0);
  });
})();
