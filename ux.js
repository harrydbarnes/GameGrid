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
})();
