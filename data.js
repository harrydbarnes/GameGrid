window.GAMEGRID_DATA = (() => {
const games = [
['mario64','Super Mario 64',1996,['Nintendo 64'],['Nintendo'],['Nintendo'],['Platformer','3D','Single-player'],'Mario'],
['zeldaoot','The Legend of Zelda: Ocarina of Time',1998,['Nintendo 64'],['Nintendo'],['Nintendo'],['Action-adventure','3D','Single-player'],'The Legend of Zelda'],
['goldeneye','GoldenEye 007',1997,['Nintendo 64'],['Rare'],['Nintendo'],['FPS','Multiplayer','Licensed'],'James Bond'],
['ff7','Final Fantasy VII',1997,['PlayStation','PC'],['Square'],['Square'],['RPG','Single-player'],'Final Fantasy'],
['mgs','Metal Gear Solid',1998,['PlayStation','PC'],['Konami'],['Konami'],['Action','Stealth','Single-player'],'Metal Gear'],
['re2','Resident Evil 2',1998,['PlayStation','Nintendo 64','PC','Dreamcast'],['Capcom'],['Capcom'],['Survival horror','Single-player'],'Resident Evil'],
['haloce','Halo: Combat Evolved',2001,['Xbox','PC'],['Bungie'],['Microsoft'],['FPS','Multiplayer','Sci-fi'],'Halo'],
['gtasa','Grand Theft Auto: San Andreas',2004,['PlayStation 2','Xbox','PC'],['Rockstar North'],['Rockstar'],['Action-adventure','Open world','Single-player'],'Grand Theft Auto'],
['hl2','Half-Life 2',2004,['PC','Xbox'],['Valve'],['Valve'],['FPS','Single-player','Sci-fi'],'Half-Life'],
['wow','World of Warcraft',2004,['PC'],['Blizzard'],['Blizzard'],['RPG','Online multiplayer','MMO'],'Warcraft'],
['re4','Resident Evil 4',2005,['GameCube','PlayStation 2','PC','Wii'],['Capcom'],['Capcom'],['Survival horror','Action','Single-player'],'Resident Evil'],
['shadowcol','Shadow of the Colossus',2005,['PlayStation 2'],['Team Ico'],['Sony'],['Action-adventure','Single-player'],''],
['gears','Gears of War',2006,['Xbox 360','PC'],['Epic Games'],['Microsoft'],['Third-person shooter','Multiplayer'],'Gears of War'],
['bioshock','BioShock',2007,['Xbox 360','PC','PlayStation 3'],['Irrational Games'],['2K'],['FPS','Single-player'],'BioShock'],
['masseffect','Mass Effect',2007,['Xbox 360','PC','PlayStation 3'],['BioWare'],['EA'],['RPG','Sci-fi','Single-player'],'Mass Effect'],
['portal','Portal',2007,['PC','Xbox 360','PlayStation 3'],['Valve'],['Valve'],['Puzzle','FPS','Single-player'],'Portal'],
['gta4','Grand Theft Auto IV',2008,['PlayStation 3','Xbox 360','PC'],['Rockstar North'],['Rockstar'],['Action-adventure','Open world','Multiplayer'],'Grand Theft Auto'],
['demons','Demon’s Souls',2009,['PlayStation 3'],['FromSoftware'],['Sony'],['RPG','Action','Single-player'],'Souls'],
['uncharted2','Uncharted 2: Among Thieves',2009,['PlayStation 3'],['Naughty Dog'],['Sony'],['Action-adventure','Third-person shooter','Multiplayer'],'Uncharted'],
['rdr','Red Dead Redemption',2010,['PlayStation 3','Xbox 360'],['Rockstar San Diego'],['Rockstar'],['Action-adventure','Open world','Single-player'],'Red Dead'],
['skyrim','The Elder Scrolls V: Skyrim',2011,['PC','PlayStation 3','Xbox 360','PlayStation 4','Xbox One','Switch'],['Bethesda'],['Bethesda'],['RPG','Open world','Single-player'],'The Elder Scrolls'],
['dark souls','Dark Souls',2011,['PlayStation 3','Xbox 360','PC'],['FromSoftware'],['Bandai Namco'],['RPG','Action','Single-player'],'Souls'],
['portal2','Portal 2',2011,['PC','PlayStation 3','Xbox 360'],['Valve'],['Valve'],['Puzzle','Co-op','Single-player'],'Portal'],
['tlou','The Last of Us',2013,['PlayStation 3','PlayStation 4'],['Naughty Dog'],['Sony'],['Action-adventure','Survival horror','Single-player'],'The Last of Us'],
['gta5','Grand Theft Auto V',2013,['PlayStation 3','Xbox 360','PC','PlayStation 4','Xbox One','PlayStation 5','Xbox Series'],['Rockstar North'],['Rockstar'],['Action-adventure','Open world','Online multiplayer'],'Grand Theft Auto'],
['bloodborne','Bloodborne',2015,['PlayStation 4'],['FromSoftware'],['Sony'],['RPG','Action','Single-player'],'Souls'],
['witcher3','The Witcher 3: Wild Hunt',2015,['PC','PlayStation 4','Xbox One','Switch'],['CD Projekt Red'],['CD Projekt'],['RPG','Open world','Single-player'],'The Witcher'],
['overwatch','Overwatch',2016,['PC','PlayStation 4','Xbox One','Switch'],['Blizzard'],['Blizzard'],['FPS','Online multiplayer'],'Overwatch'],
['botw','The Legend of Zelda: Breath of the Wild',2017,['Wii U','Switch'],['Nintendo'],['Nintendo'],['Action-adventure','Open world','Single-player'],'The Legend of Zelda'],
['horizon','Horizon Zero Dawn',2017,['PlayStation 4','PC'],['Guerrilla'],['Sony'],['Action-adventure','Open world','Female protagonist'],'Horizon'],
['marioodyssey','Super Mario Odyssey',2017,['Switch'],['Nintendo'],['Nintendo'],['Platformer','3D','Single-player'],'Mario'],
['gow','God of War',2018,['PlayStation 4','PC'],['Santa Monica Studio'],['Sony'],['Action-adventure','Single-player'],'God of War'],
['rdr2','Red Dead Redemption 2',2018,['PlayStation 4','Xbox One','PC'],['Rockstar Studios'],['Rockstar'],['Action-adventure','Open world','Online multiplayer'],'Red Dead'],
['smashultimate','Super Smash Bros. Ultimate',2018,['Switch'],['Bandai Namco','Sora'],['Nintendo'],['Fighting','Multiplayer'],'Super Smash Bros.'],
['sekiro','Sekiro: Shadows Die Twice',2019,['PlayStation 4','Xbox One','PC'],['FromSoftware'],['Activision'],['Action','Single-player'],''],
['control','Control',2019,['PlayStation 4','Xbox One','PC'],['Remedy'],['505 Games'],['Action-adventure','Third-person shooter','Female protagonist'],'Control'],
['deathstranding','Death Stranding',2019,['PlayStation 4','PC'],['Kojima Productions'],['Sony Interactive Entertainment'],['Action-adventure','Open world','Single-player'],'Death Stranding'],
['animalcrossing','Animal Crossing: New Horizons',2020,['Switch'],['Nintendo'],['Nintendo'],['Simulation','Multiplayer'],'Animal Crossing'],
['doom eternal','Doom Eternal',2020,['PC','PlayStation 4','Xbox One','Switch'],['id Software'],['Bethesda'],['FPS','Single-player','Multiplayer'],'Doom'],
['hades','Hades',2020,['PC','Switch','PlayStation 4','PlayStation 5','Xbox One','Xbox Series'],['Supergiant Games'],['Supergiant Games'],['Action','RPG','Single-player'],'Hades'],
['tlou2','The Last of Us Part II',2020,['PlayStation 4'],['Naughty Dog'],['Sony'],['Action-adventure','Female protagonist','Single-player'],'The Last of Us'],
['forzah5','Forza Horizon 5',2021,['Xbox One','Xbox Series','PC'],['Playground Games'],['Xbox Game Studios'],['Racing','Open world','Multiplayer'],'Forza'],
['halo infinite','Halo Infinite',2021,['Xbox One','Xbox Series','PC'],['343 Industries'],['Xbox Game Studios'],['FPS','Open world','Multiplayer'],'Halo'],
['eldenring','Elden Ring',2022,['PlayStation 4','PlayStation 5','Xbox One','Xbox Series','PC'],['FromSoftware'],['Bandai Namco'],['RPG','Action','Open world'],'Souls'],
['gowr','God of War Ragnarök',2022,['PlayStation 4','PlayStation 5','PC'],['Santa Monica Studio'],['Sony'],['Action-adventure','Single-player'],'God of War'],
['pokemonviolet','Pokémon Scarlet and Violet',2022,['Switch'],['Game Freak'],['Nintendo'],['RPG','Open world','Multiplayer'],'Pokémon'],
['bg3','Baldur’s Gate 3',2023,['PC','PlayStation 5','Xbox Series'],['Larian Studios'],['Larian Studios'],['RPG','Co-op','Single-player'],'Baldur’s Gate'],
['spiderman2','Marvel’s Spider-Man 2',2023,['PlayStation 5','PC'],['Insomniac Games'],['Sony'],['Action-adventure','Open world','Licensed'],'Spider-Man'],
['totk','The Legend of Zelda: Tears of the Kingdom',2023,['Switch'],['Nintendo'],['Nintendo'],['Action-adventure','Open world','Single-player'],'The Legend of Zelda'],
['alanwake2','Alan Wake 2',2023,['PlayStation 5','Xbox Series','PC'],['Remedy'],['Epic Games'],['Survival horror','Single-player'],'Alan Wake'],
['astrobot','Astro Bot',2024,['PlayStation 5'],['Team Asobi'],['Sony'],['Platformer','3D','Single-player'],'Astro Bot']
].map(([id,title,year,platforms,developers,publishers,tags,franchise])=>({id,title,year,platforms,developers,publishers,tags,franchise}));

const clues = {
 nintendo:{label:'Nintendo',test:g=>g.publishers.includes('Nintendo')||g.developers.includes('Nintendo')},
 sony:{label:'Published by Sony',test:g=>g.publishers.includes('Sony')},
 xbox:{label:'Xbox platform',test:g=>g.platforms.some(p=>p.startsWith('Xbox'))},
 playstation:{label:'PlayStation platform',test:g=>g.platforms.some(p=>p.startsWith('PlayStation'))},
 switch:{label:'Nintendo Switch',test:g=>g.platforms.includes('Switch')},
 pc:{label:'Released on PC',test:g=>g.platforms.includes('PC')},
 before2000:{label:'Released before 2000',test:g=>g.year<2000},
 y2000s:{label:'Released 2000–09',test:g=>g.year>=2000&&g.year<=2009},
 y2010s:{label:'Released 2010–19',test:g=>g.year>=2010&&g.year<=2019},
 y2020s:{label:'Released 2020+',test:g=>g.year>=2020},
 rpg:{label:'RPG',test:g=>g.tags.includes('RPG')},
 fps:{label:'FPS',test:g=>g.tags.includes('FPS')},
 openworld:{label:'Open world',test:g=>g.tags.includes('Open world')},
 multiplayer:{label:'Multiplayer',test:g=>g.tags.some(t=>t.includes('Multiplayer')||t==='Co-op')},
 action:{label:'Action / adventure',test:g=>g.tags.some(t=>['Action','Action-adventure'].includes(t))},
 single:{label:'Single-player',test:g=>g.tags.includes('Single-player')},
sequel:{label:'Franchise title',test:g=>Boolean(g.franchise)}
};

Object.assign(clues,{
 trial_rockstar:{label:'Made by Rockstar North',test:g=>g.developers.includes('Rockstar North')},
 trial_fromsoftware:{label:'Made by FromSoftware',test:g=>g.developers.includes('FromSoftware')},
 trial_naughtydog:{label:'Made by Naughty Dog',test:g=>g.developers.includes('Naughty Dog')},
});

const puzzles = [
{id:1,date:'2026-08-17',mode:'Classic',rows:['rpg','action','multiplayer'],cols:['playstation','y2010s','openworld']},
{id:2,date:'2026-08-18',mode:'Classic',rows:['single','rpg','action'],cols:['nintendo','pc','y2020s']},
{id:3,date:'2026-08-19',mode:'Classic',rows:['rpg','multiplayer','action'],cols:['playstation','y2020s','openworld']},
{id:4,date:'2026-08-20',mode:'Classic',rows:['single','fps','sequel'],cols:['xbox','y2000s','pc']},
{id:5,date:'2026-08-21',mode:'Classic',rows:['action','single','multiplayer'],cols:['nintendo','y2010s','switch']}
,{id:101,date:'2026-08-17',mode:'Trial',rows:['trial_rockstar','trial_fromsoftware','trial_naughtydog'],cols:['playstation','y2010s','openworld']}
,{id:102,date:'2026-08-18',mode:'Trial',rows:['trial_fromsoftware','trial_naughtydog','trial_rockstar'],cols:['pc','y2020s','single']}
,{id:103,date:'2026-08-19',mode:'Trial',rows:['trial_naughtydog','trial_rockstar','trial_fromsoftware'],cols:['playstation','y2010s','action']}
,{id:104,date:'2026-08-20',mode:'Trial',rows:['trial_rockstar','trial_fromsoftware','trial_naughtydog'],cols:['xbox','y2000s','multiplayer']}
,{id:105,date:'2026-08-21',mode:'Trial',rows:['trial_fromsoftware','trial_naughtydog','trial_rockstar'],cols:['pc','y2010s','rpg']}
,{id:199,date:'2099-01-01',mode:'Trial',rows:['trial_naughtydog','trial_rockstar','trial_fromsoftware'],cols:['playstation','y2020s','single']}
];
return {games,clues,puzzles};
})();
