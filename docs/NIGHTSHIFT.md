# KTM//NIGHTSHIFT

## Thesis

`KTM//NIGHTSHIFT` is a first-person maze that runs entirely in GitHub's Markdown viewer. It uses no JavaScript, iframe, WebAssembly, external server, GitHub Pages site, or per-move workflow execution.

The game is a finite state graph:

1. A Python raycaster renders one SVG viewport for every walkable map cell and cardinal direction.
2. A Markdown file represents each `(x, y, heading)` state.
3. Movement controls are ordinary relative links to neighboring state files.
4. Clicking a control loads another pre-rendered state, creating the experience of movement.

GitHub does not execute a game engine. The repository contains the complete possibility space.

## Experience

- Setting: a fictional relay bunker beneath Kathmandu.
- Objective: cross the level and reach the `05:45` uplink terminal.
- Visual language: GitHub-dark architecture, signal red, transit blue, utility yellow, and mint telemetry.
- Controls: turn left, step forward, turn right, and step backward.
- End state: reaching the uplink cell reveals a completion transmission and a restart link.

## Build Phases

### 1. Profile Cleanup

- Remove the visitor guestbook and redundant project catalogue.
- Add a compact operating-principle quote after the biography.
- Repair project artwork, clipping, contrast, and copy in the profile poster.

### 2. Raycaster

- Define an original grid map with multiple wall materials.
- Validate that spawn and uplink cells are connected.
- Render deterministic first-person SVG frames with distance shading and a compact HUD.

### 3. Stateless Engine

- Enumerate all walkable positions and four headings.
- Generate relative navigation links for every state.
- Keep blocked movement in place instead of producing broken links.
- Generate a manifest containing counts, spawn, exit, and map metadata.

### 4. GitHub Integration

- Embed the starting viewport in the profile README.
- Link the viewport and controls into the generated state graph.
- Explain the trick in one sentence without interrupting the experience.

### 5. Verification

- Parse every SVG as XML.
- Confirm every generated navigation target exists.
- Confirm the exit is reachable from spawn.
- Render-check representative spawn, corridor, corner, and exit states.
- Test the published flow on GitHub itself.

## Scope Guardrails

- This is an original Doom-like raycaster, not a copy of Doom or its art assets.
- The level is exploration-based; it does not pretend to support realtime combat.
- Generated state files are deterministic and reproducible from the checked-in map and script.
- The profile remains useful even when a visitor does not enter the game.
