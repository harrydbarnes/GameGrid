(() => {
  const DATA=window.GAMEGRID_DATA;if(!DATA)return;
  const {clues,puzzles}=DATA;
  const $=s=>document.querySelector(s);

  function currentMode(){return document.querySelector('.mode-tab.active')?.dataset.mode||'Classic'}
  function currentPuzzle(){const id=Number((($('#puzzleTitle')?.textContent||'').match(/#(\d+)/)||[])[1]);const mode=currentMode();return puzzles.find(p=>p.id===id&&p.mode===mode)||puzzles.find(p=>p.id===id)||null}
  const articleRule='Articles are treated as part of the official title unless this clue explicitly says otherwise.';
  const noArticleStart='For letter-based clues, leading articles such as “The”, “A” and “An” are ignored when deciding the first letter.';
  const oneWordRule='For this clue, leading articles such as “The”, “A” and “An” are ignored. So “The Sims” counts as a one-word title because the meaningful title word is “Sims”. Other words, subtitles and descriptors still count.';
  const rangeLetters={lettera:'A, B, C, D, E or F',letterg:'G, H, I, J, K or L',letterm:'M, N, O, P, Q or R',letters:'S, T, U, V, W, X, Y or Z'};
  const platformCopy={
    pc:'The game must have an official PC release.',playstation:'The game must have appeared on a PlayStation-family platform.',xbox:'The game must have appeared on an Xbox-family platform.',nintendo:'The game must have appeared on a Nintendo platform.',switch:'The game must have an official Nintendo Switch release.',switch2:'The game must have an official Nintendo Switch 2 release.',ps5:'The game must have an official PlayStation 5 release.',ps4:'The game must have an official PlayStation 4 release.',ps3:'The game must have an official PlayStation 3 release.',ps2:'The game must have an official PlayStation 2 release.',ps1:'The game must have an official original PlayStation release.',xseries:'The game must have an official Xbox Series X|S release.',xone:'The game must have an official Xbox One release.',x360:'The game must have an official Xbox 360 release.',xboxoriginal:'The game must have an official original Xbox release.',wiiu:'The game must have an official Wii U release.',wii:'The game must have an official Wii release.',gamecube:'The game must have an official GameCube release.',n64:'The game must have an official Nintendo 64 release.',snes:'The game must have an official SNES release.',nes:'The game must have an official NES release.',gba:'The game must have an official Game Boy Advance release.',gbc:'The game must have an official Game Boy Color release.',gb:'The game must have an official Game Boy release.',ds:'The game must have an official Nintendo DS release.',3ds:'The game must have an official Nintendo 3DS release.',dreamcast:'The game must have an official Dreamcast release.',megadrive:'The game must have an official Mega Drive / Genesis release.'
  };
  const genreCopy={rpg:'The game must be classified as a role-playing game (RPG).',shooter:'The game must be classified as a shooter.',strategy:'The game must be classified as strategy.',racing:'The game must be classified as racing.',sport:'The game must be classified as sports.',fighting:'The game must be classified as fighting.',platformer:'The game must be classified as a platformer.',puzzle:'The game must be classified as puzzle.',adventure:'The game must be classified as adventure.',simulation:'The game must be classified as simulation.',indie:'The game must be classified as indie.',arcade:'The game must be classified as arcade.'};

  function yearsText(a,b){const years=[];for(let y=a;y<=b;y++)years.push(y);return years.length<=11?years.join(', '):`${a} through ${b}`}
  function description(id,label){
    if(platformCopy[id])return platformCopy[id];
    if(genreCopy[id])return genreCopy[id]+' Genre classification follows the GameGrid catalogue metadata.';
    if(id==='pre1990')return 'The game must have first released before 1990. 1989 qualifies; 1990 does not.';
    if(id==='pre2000')return 'The game must have first released before 2000. 1999 qualifies; 2000 does not.';
    if(id==='post2015')return 'The game must have first released in 2015 or later. 2015 is included.';
    if(id==='y1990s')return `The game's first release year must be within the 1990s, inclusive: ${yearsText(1990,1999)}.`;
    if(id==='y2000s')return `The game's first release year must be within the 2000s, inclusive: ${yearsText(2000,2009)}.`;
    if(id==='y2010s')return `The game's first release year must be within the 2010s, inclusive: ${yearsText(2010,2019)}.`;
    if(id==='y2020s')return `The game's first release year must be within the 2020s, inclusive: ${yearsText(2020,2029)}.`;
    if(id==='oneword')return oneWordRule;
    if(id==='shorttitle')return `The title must contain 7 or fewer letters/numbers after punctuation and spaces are removed. ${articleRule}`;
    if(id==='numbertitle')return `The official game title must contain at least one numerical digit (0–9). ${articleRule}`;
    if(rangeLetters[id])return `The first meaningful word of the title must begin with ${rangeLetters[id]}. ${noArticleStart}`;
    if(id==='rating70')return 'The game must have a catalogue rating of at least 70/100 (or 7/10). The threshold is inclusive.';
    if(id==='rating80')return 'The game must have a catalogue rating of at least 80/100 (or 8/10). The threshold is inclusive.';
    if(id==='rating85')return 'The game must have a catalogue rating of at least 85/100 (or 8.5/10). The threshold is inclusive.';
    if(id==='rating90')return 'The game must have a catalogue rating of at least 90/100 (or 9/10). The threshold is inclusive.';
    return `A valid answer must satisfy “${label}” according to the GameGrid catalogue data.`;
  }

  function ensureDialog(){if($('#clueHelpDialog'))return $('#clueHelpDialog');const d=document.createElement('dialog');d.id='clueHelpDialog';d.className='clue-help-dialog';d.innerHTML='<div class="clue-help-card"><button class="icon-btn clue-help-close" aria-label="Close">×</button><span class="eyebrow">CLUE EXPLAINED</span><h2 id="clueHelpTitle"></h2><p id="clueHelpText"></p></div>';document.body.appendChild(d);d.querySelector('.clue-help-close').onclick=()=>d.close();d.addEventListener('click',e=>{if(e.target===d)d.close()});return d}
  function show(id){const d=ensureDialog(),c=clues[id];if(!c)return;$('#clueHelpTitle').textContent=c.label;$('#clueHelpText').textContent=description(id,c.label);d.showModal()}
  function enhance(){const grid=$('#grid'),p=currentPuzzle();if(!grid||!p)return;const nodes=[...grid.querySelectorAll('.clue')].filter(n=>!n.classList.contains('corner'));if(nodes.length!==6)return;const ids=[...p.cols,...p.rows];nodes.forEach((n,i)=>{const id=ids[i];n.classList.add('clickable-clue');n.setAttribute('role','button');n.setAttribute('tabindex','0');n.setAttribute('aria-label',`${clues[id]?.label||n.textContent}. Tap for explanation.`);n.dataset.clueId=id;n.onclick=()=>show(id);n.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();show(id)}}})}
  const obs=new MutationObserver(enhance);obs.observe(document.body,{subtree:true,childList:true});document.addEventListener('click',()=>setTimeout(enhance,0));enhance();
})();