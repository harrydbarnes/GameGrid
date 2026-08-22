(() => {
  const $=s=>document.querySelector(s);

  // Keep the visible lives counter synced to the existing internal guesses hook.
  const internalLives=$('#guessesLeft'),visibleLives=$('#livesLeft');
  const syncLives=()=>{if(internalLives&&visibleLives)visibleLives.textContent=internalLives.textContent||'9'};
  syncLives();
  if(internalLives)new MutationObserver(syncLives).observe(internalLives,{subtree:true,childList:true,characterData:true});

  // Normal mode deliberately hides metadata that can reveal whether a game fits a clue.
  // The original metadata remains rendered in app.js so a future Easy mode can reveal it again.
  document.documentElement.dataset.searchHints='off';

  // Move sharing to the top-right action. The existing sharing layer remains the source of truth.
  const topShare=$('#topShareBtn');
  if(topShare)topShare.onclick=()=>{
    const existing=$('#challengeShareBtn');
    if(existing){existing.click();return;}
    // share.js may still be initialising on a slow device.
    setTimeout(()=>$('#challengeShareBtn')?.click(),50);
  };

  // Replace the browser confirm() with an in-product modal while preserving app.js finish logic.
  const giveUpBtn=$('#giveUpBtn'),dialog=$('#giveUpDialog'),cancel=$('#cancelGiveUpBtn'),confirmBtn=$('#confirmGiveUpBtn');
  if(giveUpBtn&&dialog){
    const originalGiveUp=giveUpBtn.onclick;
    giveUpBtn.onclick=()=>dialog.showModal();
    cancel.onclick=()=>dialog.close();
    dialog.addEventListener('click',e=>{if(e.target===dialog)dialog.close()});
    confirmBtn.onclick=()=>{
      dialog.close();
      if(typeof originalGiveUp==='function'){
        const nativeConfirm=window.confirm;
        try{window.confirm=()=>true;originalGiveUp.call(giveUpBtn)}finally{window.confirm=nativeConfirm}
      }
    };
  }

  // Restart is deliberately part of the same action group as giving up: it
  // appears after a first submitted answer, then becomes the only action once
  // the current grid has ended.
  const actionStyle=document.createElement('style');
  actionStyle.textContent='.game-actions{width:100%;display:grid}.game-actions.split{grid-template-columns:minmax(0,2fr) minmax(0,1fr);gap:8px}.game-actions .restart-btn{display:grid;place-items:center;padding:0;min-height:48px}.game-actions button[hidden]{display:none!important}.game-actions .restart-btn svg{width:20px;height:20px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}.game-actions.finished .restart-btn{width:100%}.game-actions .restart-btn:hover{border-color:var(--accent);background:color-mix(in srgb,var(--accent) 9%,var(--surface));color:var(--accent)}@media(max-width:620px){.game-actions.split{grid-template-columns:minmax(0,2fr) minmax(0,1fr)}.game-actions .restart-btn{min-height:46px}}';
  document.head.append(actionStyle);
  const actionMode=()=>document.querySelector('.mode-tab.active')?.dataset.mode||'Classic';
  const actionPuzzleId=()=>((($('#puzzleTitle')?.textContent||'').match(/#(\d+)/)||[])[1]||'');
  const actionState=()=>{try{return JSON.parse(localStorage.getItem(`gamegrid:${actionMode()}:${actionPuzzleId()}`)||'{}')}catch{return {}}};
  let actionWrap,restartBtn;
  function ensureGameActions(){
    if(!giveUpBtn)return;
    if(!actionWrap){
      actionWrap=document.createElement('div');actionWrap.className='game-actions';
      giveUpBtn.parentNode.insertBefore(actionWrap,giveUpBtn);actionWrap.append(giveUpBtn);
      restartBtn=document.createElement('button');restartBtn.type='button';restartBtn.className='secondary-btn restart-btn';restartBtn.setAttribute('aria-label','Restart this grid');restartBtn.title='Restart this grid';restartBtn.innerHTML='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 12a9 9 0 1 0 3-6.7M3 4v5h5"/></svg>';
      restartBtn.onclick=()=>{
        const key=`gamegrid:${actionMode()}:${actionPuzzleId()}`;
        localStorage.setItem(key,JSON.stringify({answers:Array(9).fill(null),rarities:Array(9).fill(null),guesses:9,started:Date.now(),finished:false,gaveUp:false,restarted:true}));
        location.reload();
      };
      actionWrap.append(restartBtn);
    }
    const s=actionState(),madeGuess=Number(s.guesses)<9;
    actionWrap.classList.toggle('split',!s.finished&&madeGuess);
    actionWrap.classList.toggle('finished',Boolean(s.finished));
    giveUpBtn.hidden=Boolean(s.finished);
    restartBtn.hidden=!s.finished&&!madeGuess;
  }
  ensureGameActions();
  new MutationObserver(ensureGameActions).observe(document.body,{subtree:true,childList:true,characterData:true});

  // app.js owns answer validation, but its viewport-level toast sits beneath an
  // open modal. Mirror invalid-answer feedback into the active search dialog,
  // immediately below the text field, where it remains readable on desktop and
  // mobile bottom-sheet layouts.
  const searchDialog=$('#searchDialog'),searchBox=searchDialog?.querySelector('.search-box'),searchInput=$('#gameSearch'),toast=$('#toast');
  const searchResults=$('#searchResults');
  if(searchDialog&&searchInput&&searchResults){
    const emptyPrompt='Start typing to search games…';
    const hideEmptySearchResults=()=>{
      if(searchInput.value.trim()||searchResults.textContent.trim()===emptyPrompt&&!searchResults.querySelector('.result'))return;
      searchResults.innerHTML=`<p class="muted search-prompt">${emptyPrompt}</p>`;
    };
    new MutationObserver(hideEmptySearchResults).observe(searchResults,{subtree:true,childList:true,characterData:true});
    searchInput.addEventListener('input',hideEmptySearchResults);
    document.addEventListener('click',event=>{if(event.target.closest?.('#grid .cell.empty'))queueMicrotask(hideEmptySearchResults)},true);
  }
  if(searchDialog&&searchBox&&toast){
    const feedback=document.createElement('p');
    feedback.className='search-feedback';feedback.hidden=true;feedback.setAttribute('role','alert');
    searchBox.insertAdjacentElement('afterend',feedback);
    const feedbackStyle=document.createElement('style');
    feedbackStyle.textContent='.search-feedback{margin:9px 2px 0;color:var(--bad);font-size:13px;font-weight:750;line-height:1.35}';
    document.head.append(feedbackStyle);
    const clearFeedback=()=>{feedback.hidden=true;feedback.textContent=''};
    const mirrorInvalidAnswer=()=>{
      const message=toast.textContent||'';
      if(searchDialog.open&&toast.classList.contains('show')&&/doesn't match both clues/.test(message)){
        feedback.textContent=message;feedback.hidden=false;toast.classList.remove('show');
      }
    };
    new MutationObserver(mirrorInvalidAnswer).observe(toast,{subtree:true,childList:true,characterData:true,attributes:true,attributeFilter:['class']});
    searchInput?.addEventListener('input',clearFeedback);
    searchDialog.addEventListener('close',clearFeedback);
  }
})();
