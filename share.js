(() => {
  const $ = s => document.querySelector(s);
  const sleep = ms => new Promise(r => setTimeout(r, ms));

  function currentMode(){
    const active=document.querySelector('.mode-tab.active');
    return active?.dataset.mode || active?.textContent?.trim() || 'Classic';
  }
  function currentPuzzleId(){
    const m=($('#puzzleTitle')?.textContent||'').match(/#(\d+)/);
    return m?m[1]:'';
  }
  function puzzleUrl(){
    const u=new URL(location.href);
    u.search='';u.hash='';
    u.searchParams.set('mode',currentMode());
    u.searchParams.set('puzzle',currentPuzzleId());
    return u.toString();
  }
  async function nativeOrCopy({title,text,url,label='Copied to clipboard'}){
    try{
      if(navigator.share){await navigator.share({title,text,url});return;}
    }catch(e){if(e?.name==='AbortError')return;}
    const payload=[text,url].filter(Boolean).join('\n\n');
    try{await navigator.clipboard.writeText(payload);showToast(label)}
    catch{window.prompt('Copy this link:',payload)}
  }
  function showToast(t){
    const el=$('#toast');if(!el)return;
    el.textContent=t;el.classList.add('show');setTimeout(()=>el.classList.remove('show'),1800);
  }
  function challengeText(){
    return `Try my GameGrid challenge: ${currentMode()} #${currentPuzzleId()}`;
  }
  function resultText(){
    const mode=currentMode().toUpperCase();
    const id=currentPuzzleId();
    const cells=[...document.querySelectorAll('#grid .cell')];
    let emoji='';
    cells.forEach((c,i)=>{emoji+=c.classList.contains('solved')?'🟩':'⬛';if(i%3===2)emoji+='\n';});
    const solved=$('#solvedCount')?.textContent?.trim()||'';
    const body=$('#infoBody')?.innerText||'';
    const rarity=(body.match(/([0-9]+(?:\.[0-9]+)?)\s+avg rarity/i)||[])[1];
    const time=(body.match(/(\d+:\d{2})\s+taken/i)||[])[1];
    return `🎮 GAMEGRID ${mode} #${id}\n\n${emoji}\n${solved}${rarity?` · Rarity ${rarity}`:''}${time?` · ${time}`:''}\n\nCan you beat mine?`;
  }

  function addChallengeButton(){
    const side=document.querySelector('.side-panel');
    if(!side||$('#challengeShareBtn'))return;
    const b=document.createElement('button');
    b.id='challengeShareBtn';b.className='secondary-btn share-action';b.textContent='Share this grid';
    b.onclick=()=>nativeOrCopy({title:`GameGrid ${currentMode()} #${currentPuzzleId()}`,text:challengeText(),url:puzzleUrl(),label:'Challenge link copied'});
    side.appendChild(b);
  }

  function enhanceResults(){
    const dialog=$('#infoDialog'),body=$('#infoBody');
    if(!dialog||!body||!dialog.open)return;
    const title=$('#infoTitle')?.textContent||'';
    if(!/results/i.test(title))return;
    if($('#shareResultNativeBtn'))return;
    const old=$('#shareBtn');
    if(old){old.textContent=navigator.share?'Share result':'Copy result';old.onclick=()=>nativeOrCopy({title:`GameGrid ${currentMode()} #${currentPuzzleId()} result`,text:resultText(),url:puzzleUrl(),label:'Result copied'});old.id='shareResultNativeBtn';}
    const challenge=document.createElement('button');
    challenge.className='secondary-btn share-result-secondary';challenge.textContent='Challenge a friend';
    challenge.onclick=()=>nativeOrCopy({title:`GameGrid ${currentMode()} #${currentPuzzleId()}`,text:challengeText(),url:puzzleUrl(),label:'Challenge link copied'});
    body.appendChild(challenge);
  }

  async function restoreSharedPuzzle(){
    const params=new URLSearchParams(location.search);
    const mode=params.get('mode'),puzzle=params.get('puzzle');
    if(!mode||!puzzle)return;
    await sleep(80);
    const modeBtn=[...document.querySelectorAll('.mode-tab')].find(b=>(b.dataset.mode||b.textContent.trim()).toLowerCase()===mode.toLowerCase());
    if(modeBtn&&!modeBtn.classList.contains('active')){modeBtn.click();await sleep(80);}
    const title=($('#puzzleTitle')?.textContent||'');
    if(title.includes(`#${puzzle}`))return;
    const archiveBtn=document.querySelector('.nav-btn[data-view="archive"]');
    if(!archiveBtn)return;
    archiveBtn.click();await sleep(60);
    const item=document.querySelector(`#archiveList .archive-item[data-id="${CSS.escape(puzzle)}"]`);
    if(item){item.click();await sleep(50);}
    else{
      const todayBtn=document.querySelector('.nav-btn[data-view="today"]');todayBtn?.click();
      showToast('That shared puzzle is not available in this build');
    }
  }

  addChallengeButton();
  const observer=new MutationObserver(()=>{addChallengeButton();enhanceResults();});
  observer.observe(document.body,{subtree:true,childList:true,attributes:true,attributeFilter:['open']});
  restoreSharedPuzzle();
})();
