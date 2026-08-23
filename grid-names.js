(() => {
  const names={
    Classic:'GameGrid',Retro:'RetroGrid',Modern:'ModernGrid',Nintendo:'NintendoGrid',
    PlayStation:'PlayStationGrid',Xbox:'XboxGrid','Deep Cut':'DeepCutGrid',Trial:'TrialGrid'
  };
  window.GameGridName=mode=>names[mode]||`${mode}Grid`;

  const currentMode=()=>document.querySelector('.mode-tab.active')?.dataset.mode||'Classic';
  const label=(mode,id)=>`${window.GameGridName(mode)} #${id}`;
  function replaceTitle(node,mode=currentMode()){
    if(!node)return;
    const match=node.textContent.match(/(?:[A-Za-z]+(?:\s+[A-Za-z]+)?Grid|[A-Za-z]+) #(\d+)/);
    if(match){const value=label(mode,match[1]);if(node.textContent!==value)node.textContent=value}
  }
  function refresh(){
    replaceTitle(document.querySelector('#puzzleTitle'));
    const result=document.querySelector('#infoTitle');
    if(result?.textContent.endsWith(' results')){
      const id=(result.textContent.match(/#(\d+)/)||[])[1];
      if(id){const value=`${label(currentMode(),id)} results`;if(result.textContent!==value)result.textContent=value}
    }
    document.querySelectorAll('#resultHistory .history-row strong').forEach(node=>{
      const match=node.textContent.match(/^(.+?) #(\d+)$/);
      if(match){const value=label(match[1],match[2]);if(node.textContent!==value)node.textContent=value}
    });
  }
  new MutationObserver(refresh).observe(document.documentElement,{childList:true,subtree:true,characterData:true});
  document.addEventListener('DOMContentLoaded',refresh);
  refresh();
})();
