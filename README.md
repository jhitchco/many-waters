# Many Waters

A reverse-horror Metroidvania in the spirit of Carrion, set in the Swift River Valley,
Massachusetts, from 1938 to 1946, while four towns were cleared and drowned to make the
Quabbin Reservoir. You are the thing under the valley.

Built with Godot 4.7 (GL Compatibility renderer). The world renders at 480x270 and is
scaled 3x for a 16-bit look; the interface renders at full resolution.

## Run it

Open the folder in Godot 4.7 and press F5, or from a terminal:

```
godot --path .
```

## How it plays

- **Move** with WASD, the arrow keys or the left stick. You cling to any rough surface:
  rock, earth, timber, granite. Concrete and sheer cliff faces give you nothing to hold.
- **Take** (Space / A) pulls in the nearest person, animal or grave in reach.
  People and animals add mass. Mass is your size and your health.
- **Each kind of person teaches you something.** Take three of a kind to learn it:

  | Town | Who | Memory | Opens |
  |---|---|---|---|
  | I. Enfield | Woodcutters (red flannel) | The Axe | Timber jams |
  | II. Greenwich | Grave diggers (brown) | The Shovel | Soft earth, which also hides you |
  | III. Dana | Surveyors (khaki) | The Level (F) | False stone |
  | IV. The Works | Engineers (blue) | The Charge (E) | Granite |

- **Size is a key in both directions.** Rotten boards give way under 10 mass or more.
  Crawlways fit 6 or less. Hold Q at a spring to give mass back.
- **Everything you learn opens places you have already been.** The cave you woke in,
  the Shaw family crypt, the town hall cellar and the Swift River caves all hold graves
  that need a later memory.
- **The flood.** Drop into the basin and the gates close. The whole valley fills to
  530 feet. Sheer hilltops you could never climb are now within a swim of the surface.
- **Taken and kept.** Taking a person counts as taken. Opening a grave counts as kept.
  Animals count for neither. When you reach the intake, the larger number decides how the
  story ends.
- **Cellar holes** are checkpoints and save the game. **Tab** opens the map of everywhere
  you have been. **C** lists every voice you carry.

Gamepads work: A take, B shed, X read, Y charge, Start pause, Back map, RB chorus.

## Project layout

```
scenes/main.tscn        the only scene; main.gd builds everything in code
scripts/main.gd         rules, checkpoints and saving, flood, ending, --autotest, --shots
scripts/creature.gd     movement, collision, tentacles, abilities
scripts/actors.gd       people, animals, graves, springs, decor, projectiles
scripts/world.gd        tile map loading, queries, drawing
scripts/hud.gd          interface and screens; map_view.gd draws the map
scripts/bg.gd           parallax backdrops per town
scripts/data.gd         story text: towns, memories, every voice
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

It rewrites `data/`, renders `data/_world_preview.png`, and simulates a playthrough:
starting with no abilities, it unlocks each memory as soon as three of that kind of person
are reachable, and lists which graves each new ability opens. It exits with an error if
any grave or the intake cannot be reached.

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
