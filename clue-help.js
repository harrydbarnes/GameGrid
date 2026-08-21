(() => {
  const DATA=window.GAMEGRID_DATA;if(!DATA)return;
  const {clues,puzzles}=DATA,$=s=>document.querySelector(s);
  const articleRule='Articles are treated as part of the official title unless this criterion explicitly says otherwise.';
  const rangeLetters={lettera:'A, B, C, D, E or F',letterg:'G, H, I, J, K or L',letterm:'M, N, O, P, Q or R',letters:'S, T, U, V, W, X, Y or Z'};
  const platformCopy={pc:'The game must have an official PC release.',playstation:'The game must have appeared on a PlayStation-family platform.',xbox:'The game must have appeared on an Xbox-family platform.',nintendo:'The game must have appeared on a Nintendo platform.',switch:'The game must have an official Nintendo Switch release.',switch2:'The game must have an official Nintendo Switch 2 release.',ps5:'The game must have an official PlayStation 5 release.',ps4:'The game must have an official PlayStation 4 release.',ps3:'The game must have an official PlayStation 3 release.',ps2:'The game must have an official PlayStation 2 release.',ps1:'The game must have an official original PlayStation release.',xseries:'The game must have an official Xbox Series X|S release.',xone:'The game must have an official Xbox One release.',x360:'The game must have an official Xbox 360 release.',xboxoriginal:'The game must have an official original Xbox release.',wiiu:'The game must have an official Wii U release.',wii:'The game must have an official Wii release.',gamecube:'The game must have an official GameCube release.',n64:'The game must have an official Nintendo 64 release.',snes:'The game must have an official SNES release.',nes:'The game must have an official NES release.',gba:'The game must have an official Game Boy Advance release.',gbc:'The game must have an official Game Boy Color release.',gb:'The game must have an official Game Boy release.',ds:'The game must have an official Nintendo DS release.','3ds':'The game must have an official Nintendo 3DS release.',dreamcast:'The game must have an official Dreamcast release.',megadrive:'The game must have an official Mega Drive / Genesis release.'};
  const genreCopy={rpg:'The game must be classified as a role-playing game (RPG).',shooter:'The game must be classified as a shooter.',strategy:'The game must be classified as strategy.',racing:'The game must be classified as racing.',sport:'The game must be classified as sports.',fighting:'The game must be classified as fighting.',platformer:'The game must be classified as a platformer.',puzzle:'The game must be classified as puzzle.',adventure:'The game must be classified as adventure.',simulation:'The game must be classified as simulation.',indie:'The game must be classified as indie.',arcade:'The game must be classified as arcade.'};
  const generationCopy={gen6:'The game must have released for at least one sixth-generation console: PlayStation 2, GameCube, Xbox or Dreamcast.',gen7:'The game must have released for at least one seventh-generation console: PlayStation 3, Xbox 360 or Wii.',gen8:'The game must have released for at least one eighth-generation console: PlayStation 4, Xbox One, Wii U or Switch.',gen9:'The game must have released for at least one ninth-generation console: PlayStation 5, Xbox Series X|S or Switch 2.'};

  const onboardingKey='gamegrid-onboarding-v4';
  // A coach mark should reveal the product, not replace it with a dark modal.
  // These overrides are injected after the legacy stylesheet so the tour keeps
  // the active page visible and leaves the highlighted control interactive.
  const onboardingStyle=document.createElement('style');
  onboardingStyle.textContent=`.gamegrid-onboarding{background:transparent;backdrop-filter:none;pointer-events:none;align-items:end;justify-items:end;padding:clamp(18px,3vw,42px)}.gamegrid-onboarding-card{pointer-events:auto;width:min(100%,430px);background:var(--surface);color:var(--text);border:1px solid var(--line);box-shadow:0 18px 50px rgba(25,25,25,.16)}html[data-theme=dark] .gamegrid-onboarding-card{box-shadow:0 18px 50px rgba(0,0,0,.38)}.gamegrid-onboarding-skip,.gamegrid-onboarding-back{color:var(--muted);border-color:var(--line)}.gamegrid-onboarding-progress span{background:var(--line)}.gamegrid-onboarding-progress span.active{background:var(--accent)}.gamegrid-onboarding-eyebrow{color:var(--accent)}.gamegrid-onboarding-body{color:var(--muted)}.onboarding-clue-highlight{position:relative;z-index:10001!important;outline:3px solid var(--accent);outline-offset:4px;box-shadow:0 10px 28px color-mix(in srgb,var(--accent) 28%,transparent);animation:gamegrid-onboarding-ring 1.4s ease-in-out infinite}@keyframes gamegrid-onboarding-ring{0%,100%{outline-offset:4px;box-shadow:0 8px 22px color-mix(in srgb,var(--accent) 22%,transparent)}50%{outline-offset:7px;box-shadow:0 12px 32px color-mix(in srgb,var(--accent) 38%,transparent)}}@media(max-width:640px){.gamegrid-onboarding{align-items:end;padding:12px}.gamegrid-onboarding-card{width:100%;border-radius:22px 22px 16px 16px}}`;
  document.head.appendChild(onboardingStyle);
  const criterionInteractionStyle=document.createElement('style');
  criterionInteractionStyle.textContent=`.clickable-clue{transition:background .16s ease,border-color .16s ease,box-shadow .16s ease}.clickable-clue:active{transform:none;background:color-mix(in srgb,var(--accent) 14%,var(--surface))}.clickable-clue:focus-visible{outline:2px solid var(--accent);outline-offset:-2px;background:color-mix(in srgb,var(--accent) 10%,var(--surface))}@media (hover:hover) and (pointer:fine){.clickable-clue:hover{background:color-mix(in srgb,var(--accent) 9%,var(--surface));box-shadow:inset 0 0 0 1px color-mix(in srgb,var(--accent) 34%,var(--line))}}`;
  document.head.appendChild(criterionInteractionStyle);
  const forceOnboarding=new URLSearchParams(location.search).get('onboarding')==='1';
  const onboardingSteps=[
    {eyebrow:'WELCOME TO GAMEGRID',title:'One grid. Nine great answers.',body:'Choose any +, then name a game that matches both its row and column clues. Every square has more than one valid answer.'},
    {eyebrow:'CHOOSE YOUR STARTING POINT',title:'Classic is the all-rounder.',body:'Classic mixes every era and platform — the original GameGrid challenge. When you want a twist, try Modern (PS2 onwards) or a platform-specific mode.',highlight:'mode'},
    {eyebrow:'TRY THE LIVE CLUES',title:'Criteria explain themselves.',body:'Select a highlighted row or column label to see exactly what counts. The grid stays live while you explore.',highlight:true},
    {eyebrow:'MAKE THE GRID YOURS',title:'The less obvious, the better.',body:'Complete the grid, compare your answers with the most obvious and rarest picks, then share your score. Lower scores are better.'}
  ];

  function currentPuzzle(){const mode=document.querySelector('.mode-tab.active')?.dataset.mode||'Classic',id=Number((($('#puzzleTitle')?.textContent||'').match(/#(\d+)/)||[])[1]);return puzzles.find(p=>p.id===id&&p.mode===mode)||puzzles.find(p=>p.id===id)||null}
  function yearsText(a,b){const arr=[];for(let y=a;y<=b;y++)arr.push(y);return arr.length<=11?arr.join(', '):`${a} through ${b}`}
  function description(id,label){if(platformCopy[id])return platformCopy[id];if(genreCopy[id])return genreCopy[id]+' Genre classification follows the GameGrid catalogue metadata.';if(id==='pre1990')return 'The game must have first released before 1990. 1989 qualifies; 1990 does not.';if(id==='pre2000')return 'The game must have first released before 2000. 1999 qualifies; 2000 does not.';if(id==='post2015')return 'The game must have first released in 2015 or later. 2015 is included.';if(id==='y1990s')return `The first release year must be within the 1990s, inclusive: ${yearsText(1990,1999)}.`;if(id==='y2000s')return `The first release year must be within the 2000s, inclusive: ${yearsText(2000,2009)}.`;if(id==='y2010s')return `The first release year must be within the 2010s, inclusive: ${yearsText(2010,2019)}.`;if(id==='y2020s')return `The first release year must be within the 2020s, inclusive: ${yearsText(2020,2029)}.`;if(id==='oneword')return 'The official title must contain exactly one word. Leading articles such as “The”, “A” and “An” count as words, so “The Sims” does not qualify.';if(id==='shorttitle')return `The title must contain 7 or fewer letters/numbers after punctuation and spaces are removed. ${articleRule}`;if(id==='numbertitle')return `The official game title must contain at least one numerical digit (0–9). ${articleRule}`;if(rangeLetters[id])return `The official title must begin with ${rangeLetters[id]}. Leading articles count, so “The Last of Us” begins with T.`;if(/^rating/.test(id)){const n={rating70:65,rating80:75,rating85:80,rating90:85}[id];return `The catalogue rating must be at least ${n}/100. The threshold itself is included.`}return `A valid answer must satisfy “${label}” according to the GameGrid catalogue data.`}
  const baseDescription=description;
  description=(id,label)=>generationCopy[id]||baseDescription(id,label);
  function clueIdForNode(node){const p=currentPuzzle(),grid=$('#grid');if(!p||!grid)return null;const nodes=[...grid.querySelectorAll('.clue:not(.corner)')],idx=nodes.indexOf(node);if(idx<0)return null;return idx<3?p.cols[idx]:p.rows[idx-3]}
  function showById(id){const c=clues[id],dialog=$('#infoDialog'),title=$('#infoTitle'),body=$('#infoBody');if(!c||!dialog||!title||!body)return false;title.textContent=c.label;body.innerHTML=`<div class="clue-explanation"><span class="eyebrow">CRITERION EXPLAINED</span><p>${description(id,c.label)}</p></div>`;dialog.dataset.criterionHelp='1';try{if(!dialog.open)dialog.showModal()}catch{delete dialog.dataset.criterionHelp;return false}return true}
  function showForNode(node){const id=clueIdForNode(node);return id?showById(id):false}
  window.GameGridCriterionHelp={showForNode,showById,clueIdForNode};
  function decorate(){const grid=$('#grid');if(!grid)return;grid.querySelectorAll('.clue:not(.corner)').forEach(n=>{n.classList.add('clickable-clue');n.setAttribute('role','button');n.setAttribute('tabindex','0');n.setAttribute('aria-description','Opens a short explanation of this criterion')})}
  document.addEventListener('click',e=>{const node=e.target.closest?.('#grid .clue:not(.corner)');if(!node)return;if(showForNode(node)){e.preventDefault();e.stopPropagation()}},true);
  document.addEventListener('keydown',e=>{if(!['Enter',' '].includes(e.key))return;const node=e.target.closest?.('#grid .clue:not(.corner)');if(!node)return;if(showForNode(node))e.preventDefault()});

  // Native dialog backdrops are not consistently exposed as a child event
  // target. Use viewport coordinates at capture time so a click anywhere
  // outside the visible criterion card closes it reliably.
  const infoDialog=$('#infoDialog');
  document.addEventListener('pointerdown',e=>{
    if(!infoDialog||infoDialog.dataset.criterionHelp!=='1'||!infoDialog.open)return;
    const r=infoDialog.getBoundingClientRect();
    const outside=e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom;
    if(outside){e.preventDefault();infoDialog.close()}
  },true);
  infoDialog?.addEventListener('close',()=>delete infoDialog.dataset.criterionHelp);

  function hasSeen(){if(forceOnboarding)return false;try{return localStorage.getItem(onboardingKey)==='1'}catch{return false}}
  function markSeen(){if(!forceOnboarding)try{localStorage.setItem(onboardingKey,'1')}catch{}}
  function clearHighlight(){document.querySelectorAll('.onboarding-clue-highlight').forEach(n=>n.classList.remove('onboarding-clue-highlight'))}
  function highlight(kind='clue'){clearHighlight();const target=kind==='mode'?document.querySelector('#modeTabs .mode-tab.active'):document.querySelector('#grid .clue:not(.corner)');target?.classList.add('onboarding-clue-highlight')}
  function startOnboarding(force=false){
    if((!force&&hasSeen())||document.querySelector('.gamegrid-onboarding'))return false;
    const info=$('#infoDialog');if(info?.open)info.close();
    let step=0;
    const overlay=document.createElement('div');overlay.className='gamegrid-onboarding';overlay.setAttribute('role','dialog');overlay.setAttribute('aria-modal','true');overlay.setAttribute('aria-labelledby','onboardingTitle');overlay.innerHTML='<div class="gamegrid-onboarding-card"><button class="gamegrid-onboarding-skip" type="button">Skip</button><div class="gamegrid-onboarding-progress"></div><span class="eyebrow gamegrid-onboarding-eyebrow"></span><h2 id="onboardingTitle"></h2><p class="gamegrid-onboarding-body"></p><div class="gamegrid-onboarding-actions"><button class="gamegrid-onboarding-back" type="button">Back</button><button class="gamegrid-onboarding-next" type="button">Next</button></div></div>';
    document.body.appendChild(overlay);
    const eyebrow=overlay.querySelector('.gamegrid-onboarding-eyebrow'),title=overlay.querySelector('#onboardingTitle'),body=overlay.querySelector('.gamegrid-onboarding-body'),progress=overlay.querySelector('.gamegrid-onboarding-progress'),back=overlay.querySelector('.gamegrid-onboarding-back'),next=overlay.querySelector('.gamegrid-onboarding-next');
    function finish(){clearHighlight();markSeen();overlay.remove()}
    function render(){const s=onboardingSteps[step];eyebrow.textContent=s.eyebrow;title.textContent=s.title;body.textContent=s.body;progress.innerHTML=onboardingSteps.map((_,i)=>`<span class="${i===step?'active':''}"></span>`).join('');back.hidden=step===0;next.textContent=step===onboardingSteps.length-1?'Start playing':'Next';clearHighlight();if(s.highlight)highlight(s.highlight===true?'clue':s.highlight);requestAnimationFrame(()=>next.focus())}
    back.onclick=()=>{if(step>0){step--;render()}};next.onclick=()=>{if(step<onboardingSteps.length-1){step++;render()}else finish()};overlay.querySelector('.gamegrid-onboarding-skip').onclick=finish;overlay.addEventListener('keydown',e=>{if(e.key==='Escape')finish()});render();return true;
  }
  window.GameGridOnboarding={start:()=>startOnboarding(true),version:4};

  function addReplayIntro(){
    const dialog=$('#infoDialog'),title=$('#infoTitle'),body=$('#infoBody');
    if(!dialog?.open||!title||!body||title.textContent.trim()!=='How to play'||body.querySelector('#replayIntroBtn'))return;
    const wrap=document.createElement('div');wrap.className='replay-intro-wrap';wrap.innerHTML='<button class="secondary-btn" id="replayIntroBtn" type="button">Replay introduction</button>';
    body.appendChild(wrap);wrap.querySelector('button').onclick=()=>startOnboarding(true);
  }
  document.addEventListener('click',e=>{if(e.target.closest?.('#helpBtn'))setTimeout(addReplayIntro,0)},true);
  new MutationObserver(()=>{decorate();addReplayIntro()}).observe(document.body,{subtree:true,childList:true,attributes:true,attributeFilter:['open']});

  function ready(n=0){if(document.querySelectorAll('#grid .clue:not(.corner)').length>=6||n>=20)startOnboarding(false);else setTimeout(()=>ready(n+1),100)}
  decorate();if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>ready(),{once:true});else ready();
})();
