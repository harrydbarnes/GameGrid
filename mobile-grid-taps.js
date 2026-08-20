(() => {
  const grid=document.querySelector('#grid');if(!grid)return;
  const setVisualHeight=()=>document.documentElement.style.setProperty('--gamegrid-visual-height',`${Math.round(window.visualViewport?.height||window.innerHeight)}px`);
  setVisualHeight();
  window.visualViewport?.addEventListener('resize',setVisualHeight);
  window.addEventListener('resize',setVisualHeight);
  let down=null,x=0,y=0;
  grid.addEventListener('pointerdown',e=>{if(!['touch','pen'].includes(e.pointerType))return;down=e.target;x=e.clientX;y=e.clientY},{passive:true});
  grid.addEventListener('pointerup',e=>{if(!['touch','pen'].includes(e.pointerType)||!down)return;const moved=Math.hypot(e.clientX-x,e.clientY-y);down=null;if(moved>12)return;
    const clue=e.target.closest?.('.clue:not(.corner)');
    if(clue){e.preventDefault();e.stopPropagation();if(window.GameGridCriterionHelp?.showForNode){window.GameGridCriterionHelp.showForNode(clue)}return}
    const cell=e.target.closest?.('button.cell');if(cell&&!cell.disabled){e.preventDefault();cell.click()}
  },{passive:false});
})();
