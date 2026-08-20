(() => {
  const title=document.querySelector('#puzzleTitle');
  if(!title)return;
  function openArchive(){
    const archive=document.querySelector('.nav-btn[data-view="archive"]');
    archive?.click();
  }
  title.addEventListener('click',openArchive);
  title.addEventListener('keydown',e=>{
    if(e.key==='Enter'||e.key===' '){e.preventDefault();openArchive()}
  });
})();
