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

  // app.js owns answer validation, but its viewport-level toast sits beneath an
  // open modal. Mirror invalid-answer feedback into the active search dialog,
  // immediately below the text field, where it remains readable on desktop and
  // mobile bottom-sheet layouts.
  const searchDialog=$('#searchDialog'),searchBox=searchDialog?.querySelector('.search-box'),searchInput=$('#gameSearch'),toast=$('#toast');
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
