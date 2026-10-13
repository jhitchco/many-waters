# Many Waters

A reverse-horror Metroidvania in the spirit of Carrion, set in the Swift River Valley,
Massachusetts, from 1938 to 1946, while four towns were cleared and drowned to make the
Quabbin Reservoir. You are the thing under the valley.

Built with Godot 4.7 (GL Compatibility renderer). The world renders at 480x270 and is
scaled 3x for a 16-bit look; the interface renders at full resolution.

## Run it

Play in a browser at https://jhitchco.github.io/many-waters/ , or double-click
`Play Many Waters.bat` (it uses the Godot that `winget install GodotEngine.GodotEngine`
installs). You can also open the folder in Godot 4.7 and press F5, or from a terminal:

```
godot --path .
```

## How it plays

- **Move** with WASD, the arrow keys or the left stick. You cling to any rough surface:
  rock, earth, timber, granite. Concrete and sheer cliff faces give you nothing to hold.
- **Fling** (Shift, right-click, or LB/RT) throws a tentacle at the first rough surface in
  that direction and yanks you to it, keeping your speed. Right-click aims at the cursor.
  With nothing in reach it whips the air and bursts you forward. Bigger bodies reach further.
  Chain flings to cross the Under-Valley's hanging rock and the spillway cut at the Works.
- **Take** (Space, left-click or A) pulls in the nearest person, animal or grave in reach.
  People and animals add mass. Mass is your size and your health.
- **Each kind of person teaches you something.** Take three of a kind to learn it:

  | Town | Who | Memory | Opens |
  |---|---|---|---|
  | I. Enfield | Woodcutters (red flannel) | The Axe | Timber jams, the sawmill, the Enfield ridge |
  | II. Greenwich | Grave diggers (brown) | The Shovel | Soft earth, which also hides you |
  | III. Dana | Surveyors (khaki) | The Level (F) | False stone |
  | IV. The Works | Engineers (blue) | The Charge (E) | Granite |

- **Go where you like.** The Under-Valley runs beneath Enfield, Greenwich and Dana, so the
  first three memories can be earned in any order. The Works opens either through the false
  wall on Dana's east ridge (the Level) or up the diversion tunnel (the Axe and the Shovel).
  Only the basin needs the Charge.
- **Size is a key in both directions.** Rotten boards give way under 10 mass or more.
  Crawlways fit 6 or less. Hold Q at a spring to give mass back.
- **Memories.** Some graves and some people carry a memory you play as them, in sepia, before
  the valley was cleared: Thankful Rich at the spring in 1794, Eli Stone in the Greenwich
  burying ground in 1841, Marion Haskell at the Farewell Ball in 1938, and C. R. Ballou running
  the 530-foot line in 1939.
- **The valley changes.** Once the woodpeckers have taught you the axe, Enfield's maples are
  stumps and their brush fires burn. Fire hurts.
- **Enemies.** Woodcutters swing axes. Engineers throw dynamite. Wardens shoot. **Burners** carry
  kerosene flamethrowers: their fire hurts, catches in timber and rotten boards and spreads,
  so a burner can open a timber jam for you. Take a burner and his tank bursts, taking anyone
  close with it. **Tracker dogs** smell you even under the earth, bay to bring the crews, and bite.
- **Bosses.** *The Foreman* in the Enfield sawmill is a wall of fire from the front: get behind
  him and tear at his tanks while he slowly turns. *The Steam Shovel* in the spillway cut sweeps
  and slams its bucket: tear out its three cables, then take the operator from the wreck.
  *The Last Train* runs the Rabbit Run trestle high over Dana: tear down the three supports
  under its weak span and let it come. *The Houndmaster* in the Dana kennels whistles up his
  pack; his dogs drag you off him, so take them first. *The Diver* walks drowned Prescott after
  the flood: tear his air hose at its brass couplings. Each leaves a Root Heart.
- **New places.** The Rabbit Run, an old railroad trestle above Dana with a rail tunnel into the
  Works; the kennels; and the Hollow, a cave of living roots at the very bottom of the valley,
  under the deep road, reached through a false floor or by digging. Something is beating there.
- **Root Hearts.** Ten of them, hidden or guarded. Each is a permanent upgrade: Long Reach,
  Wet Bark (fire resistance), Quick Tendons (faster flings), Iron Gut (more mass per person),
  Regrowth, Old Blood (fast through earth and water), Thick Hide (resist bullets, blades and
  teeth), Steam Lungs (bigger air bursts), Keen Nose (graves, papers and hearts on the map),
  and Deep Lungs (regrow underwater).
- **Nine memories** to live through and **eight papers** to read: an eviction notice,
  Marion's diary, the last sermon, the grave-removal ledger, Ballou's field book, a telegram
  from Boston, a child's letter, and a last letter from Prescott.
- **Frenzy.** Take people in quick succession for a combo; from the third, each one gives extra mass.
- **Achievements** (21) are kept across playthroughs and listed on the pause screen. The ending
  screen shows your time, deaths and how much of the valley you found.
- **The flood.** Drop into the basin and the gates close. The whole valley fills to
  530 feet, and three sheer hilltops become islands you can finally reach.
- **Taken and kept.** Taking a person counts as taken. Opening a grave counts as kept.
  Animals count for neither. When you reach the intake, the larger number decides how the
  story ends.
- **Cellar holes** are checkpoints and save the game. **Tab** opens the map of everywhere
  you have been. **C** lists every voice you carry. Places announce their names as you enter.

Gamepads work: A take, B shed, X read, Y charge, LB or RT fling, Start pause, Back map, RB chorus.

## Project layout

```
scenes/main.tscn        the only scene; main.gd builds everything in code
scripts/main.gd         rules, checkpoints and saving, flood, ending, --autotest, --shots
scripts/creature.gd     movement, collision, tentacles, abilities
scripts/actors.gd       people, animals, graves, springs, decor, projectiles
scripts/world.gd        tile map loading, queries, drawing
scripts/hud.gd          interface and screens; map_view.gd draws the map
scripts/bg.gd           parallax backdrops per town
scripts/data.gd         story text: towns, memories, every voice, the playable memories
scripts/flashback.gd    plays a memory as a person from the valley's past
scripts/boss.gd         the Foreman and the Steam Shovel
scripts/boss2.gd        the Last Train, the Houndmaster and the Diver
scripts/view.gdshader   sepia, lantern light and cave darkness over the game view
data/world.txt          the map, one character per 16px tile (generated)
data/entities.json      people, graves, springs, cellar holes (generated)
data/decor.json         trees, buildings, props (generated)
tools/build_level.py    builds the map and checks that progression works
tools/gen_art.py        draws every sprite, tile and backdrop
tools/gen_audio.py      synthesizes the core sound effects
tools/gen_music.py      composes and renders the score, ambient beds and extra effects
tools/publish_web.sh    builds the Web export and publishes it to GitHub Pages
```

## Sound and music

Everything is synthesized by `tools/gen_music.py`, with no samples. Each town has its own
original piece on period instruments: fiddle and reed organ in Enfield, a meetinghouse
hymn with choir and bell in Greenwich, plucked strings in Dana, an industrial pulse at the
Works, slow bells over the basin, and a low choir in the caves. Ambient beds (birds, dusk,
night crickets, machinery, cave drips, water) crossfade with the music. The creature
slithers as it moves and digs in soft earth, people scream when taken, opened graves
whisper, sound muffles underwater, and a heartbeat starts when you are down to 3 mass.

## Changing the world

Edit `tools/build_level.py`, then run:

```
python tools/build_level.py
```

It rewrites `data/`, renders `data/_world_preview.png`, and simulates the creature (crawling,
falling and flinging) to check the design. It fails if any grave or the intake can't be
reached, if any place traps you with no way back, if any of the first three memories can't be
earned first, or if either way into the Works is closed.

## Automated checks

```
godot --headless --path . -- --autotest
```

This plays scripted checks against the real physics: climbing, taking, opening graves,
every ability gate, heavy and light boards, springs, the flood, saving and the ending.

```
godot --path . -- --shots=<folder>
```

This saves screenshots of each area to a folder (it needs a window, not `--headless`).

## Web build

`export_presets.cfg` has a Web preset (single-threaded, so it runs on GitHub Pages
without special server headers). With Godot's web export templates installed:

```
tools/publish_web.sh path/to/godot
```

builds `export/web/` and force-pushes it to the `gh-pages` branch. The web build uses
the browser's default font instead of Georgia and Courier.
