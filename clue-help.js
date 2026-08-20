(() => {
  const DATA=window.GAMEGRID_DATA;if(!DATA)return;
  const {clues,puzzles}=DATA;
  const $=s=>document.querySelector(s);
  const articleRule='Articles are treated as part of the official title unless this clue explicitly says otherwise.';
  const rangeLetters={lettera:'A, B, C, D, E or F',letterg:'G, H, I, J, K or L',letterm:'M, N, O, P, Q or R',letters:'S, T, U, V, W, X, Y or Z'};
  const platformCopy={pc:'The game must have an official PC release.',playstation:'The game must have appeared on a PlayStation-family platform.',xbox:'The game must have appeared on an Xbox-family platform.',nintendo:'The game must have appeared on a Nintendo platform.',switch:'The game must have an official Nintendo Switch release.',switch2:'The game must have an official Nintendo Switch 2 release.',ps5:'The game must have an official PlayStation 5 release.',ps4:'The game must have an official PlayStation 4 release.',ps3:'The game must have an official PlayStation 3 release.',ps2:'The game must have an official PlayStation 2 release.',ps1:'The game must have an official original PlayStation release.',xseries:'The game must have an official Xbox Series X|S release.',xone:'The game must have an official Xbox One release.',x360:'The game must have an official Xbox 360 release.',xboxoriginal:'The game must have an official original Xbox release.',wiiu:'The game must have an official Wii U release.',wii:'The game must have an official Wii release.',gamecube:'The game must have an official GameCube release.',n64:'The game must have an official Nintendo 64 release.',snes:'The game must have an official SNES release.',nes:'The game must have an official NES release.',gba:'The game must have an official Game Boy Advance release.',gbc:'The game must have an official Game Boy Color release.',gb:'The game must have an official Game Boy release.',ds:'The game must have an official Nintendo DS release.',3ds:'The game must have an official Nintendo 3DS release.',dreamcast:'The game must have an official Dreamcast release.',megadrive:'The game must have an official Mega Drive / Genesis release.'};
  const genreCopy={rpg:'The game must be classified as a role-playing game (RPG).',shooter:'The game must be classified as a shooter.',strategy:'The game must be classified as strategy.',racing:'The game must be classified as racing.',sport:'The game must be classified as sports.',fighting:'The game must be classified as fighting.',platformer:'The game must be classified as a platformer.',puzzle:'The game must be classified as puzzle.',adventure:'The game must be classified as adventure.',simulation:'The game must be classified as simulation.',indie:'The game must be classified as indie.',arcade:'The game must be classified as arcade.'};
  const onboardingKey='gamegrid-onboarding-v2';
  const forceOnboarding=new URLSearchParams(location.search).get('onboarding')==='1';
  const onboardingSteps=[
    {eyebrow:'WELCOME TO GAMEGRID',title:'Fill the grid. Find the rare gems.',body:'Pick a game that matches both the row and column criteria. Every square has an answer, but the less obvious picks are where the fun is.'},
    {eyebrow:'QUICK TIP',title:'Need help with the criteria?',body:'Tap or click any row or column criterion to see exactly what it means, including title rules, year ranges and other clarifications.',highlight:true},
    {eyebrow:'YOU’RE READY',title:'Go for the rarest grid you can.',body:'Complete the grid, compare your answers with the best and most obvious picks, then share your score. Have fun!'}
  ];

  function currentPuzzle(){const mode=document.querySelector('.mode-tab.active')?.dataset.mode||'Classic';const id=Number((($('#puzzleTitle')?.textContent||'').match(/#(\d+)/)||[])[1]);return puzzles.find(p=>p.id===id&&p.mode===mode)||puzzles.find(p=>p.id===id)||null}
  function yearsText(a,b){const arr=[];for(let y=a;y<=b;y++)arr.push(y);return arr.length<=11?arr.join(', '):`${a} through ${b}`}
  function description(id,label){
    if(platformCopy[id])return platformCopy[id];
    if(genreCopy[id])return genreCopy[id]+' Genre classification follows the GameGrid catalogue metadata.';
    if(id==='pre1990')return 'The game must have first released before 1990. 1989 qualifies; 1990 does not.';
    if(id==='pre2000')return 'The game must have first released before 2000. 1999 qualifies; 2000 does not.';
    if(id==='post2015')return 'The game must have first released in 2015 or later. 2015 is included.';
    if(id==='y1990s')return `The first release year must be within the 1990s, inclusive: ${yearsText(1990,1999)}.`;
    if(id==='y2000s')return `The first release year must be within the 2000s, inclusive: ${yearsText(2000,2009)}.`;
    if(id==='y2010s')return `The first release year must be within the 2010s, inclusive: ${yearsText(2010,2019)}.`;
    if(id==='y2020s')return `The first release year must be within the 2020s, inclusive: ${yearsText(2020,2029)}.`;
    if(id==='oneword')return 'The official title must contain exactly one word. Leading articles such as “The”, “A” and “An” currently count as words, so “The Sims” does not qualify.';
    if(id==='shorttitle')return `The title must contain 7 or fewer letters/numbers after punctuation and spaces are removed. ${articleRule}`;
    if(id==='numbertitle')return `The official game title must contain at least one numerical digit (0–9). ${articleRule}`;
    if(rangeLetters[id])return `The official title must begin with ${rangeLetters[id]}. Leading articles count, so “The Last of Us” begins with T.`;
    if(/^rating/.test(id)){const n=id.replace('rating','');return `The catalogue rating must be at least ${n}/100. The threshold itself is included.`}
    return `A valid answer must satisfy “${label}” according to the GameGrid catalogue data.`;
  }
  function clueIdForNode(node){const p=currentPuzzle(),grid=$('#grid');if(!p||!grid)return null;const nodes=[...grid.querySelectorAll('.clue:not(.corner)')];const idx=nodes.indexOf(node);if(idx<0)return null;return idx<3?p.cols[idx]:p.rows[idx-3]}
  function show(id){const c=clues[id],dialog=$('#infoDialog'),title=$('#infoTitle'),body=$('#infoBody');if(!c||!dialog||!title||!body)return;title.textContent=c.label;body.innerHTML=`<div class="clue-explanation"><span class="eyebrow">CLUE EXPLAINED</span><p>${description(id,c.label)}</p></div>`;if(!dialog.open)dialog.showModal()}
  function decorate(){const grid=$('#grid');if(!grid)return;grid.querySelectorAll('.clue:not(.corner)').forEach(n=>{n.classList.add('clickable-clue');n.setAttribute('role','button');n.setAttribute('tabindex','0');n.title='Tap for explanation'})}

  function hasSeenOnboarding(){if(forceOnboarding)return false;try{return localStorage.getItem(onboardingKey)==='1'}catch{return false}}
  function markOnboardingSeen(){if(forceOnboarding)return;try{localStorage.setItem(onboardingKey,'1')}catch{}}
  function clearOnboardingHighlight(){document.querySelectorAll('.onboarding-clue-highlight').forEach(n=>n.classList.remove('onboarding-clue-highlight'))}
  function highlightCriterion(){clearOnboardingHighlight();const clue=document.querySelector('#grid .clue:not(.corner)');if(clue)clue.classList.add('onboarding-clue-highlight')}
  function startOnboarding(){
    if(hasSeenOnboarding()||document.querySelector('.gamegrid-onboarding'))return;
    let step=0;
    const overlay=document.createElement('div');
    overlay.className='gamegrid-onboarding';
    overlay.setAttribute('role','dialog');
    overlay.setAttribute('aria-modal','true');
    overlay.setAttribute('aria-labelledby','onboardingTitle');
    overlay.innerHTML=`<div class="gamegrid-onboarding-card"><button class="gamegrid-onboarding-skip" type="button">Skip</button><div class="gamegrid-onboarding-progress" aria-hidden="true"></div><span class="eyebrow gamegrid-onboarding-eyebrow"></span><h2 id="onboardingTitle"></h2><p class="gamegrid-onboarding-body"></p><div class="gamegrid-onboarding-actions"><button class="gamegrid-onboarding-back" type="button">Back</button><button class="gamegrid-onboarding-next" type="button">Next</button></div></div>`;
    document.body.appendChild(overlay);
    const eyebrow=overlay.querySelector('.gamegrid-onboarding-eyebrow');
    const title=overlay.querySelector('#onboardingTitle');
    const body=overlay.querySelector('.gamegrid-onboarding-body');
    const progress=overlay.querySelector('.gamegrid-onboarding-progress');
    const back=overlay.querySelector('.gamegrid-onboarding-back');
    const next=overlay.querySelector('.gamegrid-onboarding-next');
    const skip=overlay.querySelector('.gamegrid-onboarding-skip');
    function finish(){clearOnboardingHighlight();markOnboardingSeen();overlay.remove()}
    function render(){
      const s=onboardingSteps[step];
      eyebrow.textContent=s.eyebrow;title.textContent=s.title;body.textContent=s.body;
      progress.innerHTML=onboardingSteps.map((_,i)=>`<span class="${i===step?'active':''}"></span>`).join('');
      back.hidden=step===0;
      next.textContent=step===onboardingSteps.length-1?'Start playing':'Next';
      clearOnboardingHighlight();if(s.highlight)highlightCriterion();
      requestAnimationFrame(()=>next.focus());
    }
    back.addEventListener('click',()=>{if(step>0){step--;render()}});
    next.addEventListener('click',()=>{if(step<onboardingSteps.length-1){step++;render()}else finish()});
    skip.addEventListener('click',finish);
    overlay.addEventListener('keydown',e=>{if(e.key==='Escape')finish()});
    render();
  }
  function startWhenReady(attempt=0){
    const gridReady=document.querySelectorAll('#grid .clue:not(.corner)').length>=6;
    if(gridReady||attempt>=20){startOnboarding();return}
    setTimeout(()=>startWhenReady(attempt+1),100);
  }

  document.addEventListener('click',e=>{const node=e.target.closest&&e.target.closest('#grid .clue:not(.corner)');if(!node)return;const id=clueIdForNode(node);if(!id)return;e.preventDefault();e.stopPropagation();show(id)},true);
  document.addEventListener('keydown',e=>{if(e.key!=='Enter'&&e.key!==' ')return;const node=e.target.closest&&e.target.closest('#grid .clue:not(.corner)');if(!node)return;const id=clueIdForNode(node);if(!id)return;e.preventDefault();show(id)});
  new MutationObserver(()=>decorate()).observe(document.body,{subtree:true,childList:true});decorate();
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>startWhenReady(),{once:true});else startWhenReady();
})();