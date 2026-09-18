# Kathmandu Network Node Profile

## Objective

Replace the conventional profile README with a repository-owned, generated SVG experience that presents Naitik Joshi as a Kathmandu-based builder through an animated project broadcast. The profile must remain truthful, readable, self-hosted, and operational without an external deployment.

## Operating Model

1. `profile.json` stores authored identity, project, and status information.
2. `scripts/generate_profile.py` optionally reads public GitHub data and renders light and dark SVG assets.
3. GitHub Actions regenerates the assets on configuration changes, manual dispatch, and a weekly schedule.
4. Generated assets are committed into this repository and embedded by `README.md`.
5. If GitHub data cannot be reached, generation succeeds using the last configured fallback values.

No server, database, Vercel project, VPS, or external statistics service is required.

## Phases

### Phase 1 - Visual Foundation

- Define the Kathmandu Network Node visual language.
- Build a deterministic Python SVG renderer with no third-party runtime dependencies.
- Render dark and light assets from one configuration file.
- Add the network topology, skyline, mountain contour, status panels, and terminal prompt.
- Add restrained motion with a usable static first frame.
- Validate generated SVG as XML and test escaping.
- Integrate generated assets into a minimal README.

Exit condition: both themes render locally, tests pass, and the README has no third-party analytics dependency.

### Phase 2 - Honest GitHub Telemetry

- [x] Fetch public repository count, followers, stars, latest pushed repository, and selected repository metadata.
- [x] Show selected-repository language, stars, forks, and last-push date.
- [x] Mark dynamic values with a `PUBLIC SIGNAL` label.
- [x] Retain manually authored lifecycle states such as `ACTIVE DEVELOPMENT` and `HACKATHON PROTOTYPE`.
- [x] Add offline, certificate, and API-rate-limit fallbacks.
- [x] Remove generation timestamps so unchanged public data produces unchanged assets.
- [x] Commit generated assets only when their content changes.

Exit condition met locally: live public data refreshes without a personal access token, while the scheduled workflow uses only GitHub's built-in token.

### Phase 3 - Visual Refinement

- [x] Improve skyline silhouettes, city details, node spacing, and signal hierarchy.
- [x] Generate dedicated 720 x 960 mobile artwork instead of scaling the desktop composition.
- [x] Select mobile and desktop sources responsively in the profile README.
- [x] Tune packet animation duration and reduced-motion behavior.
- [x] Add deterministic generation comparisons to the test suite.
- [x] Review both themes at desktop and 430 px browser widths.
- [x] Replace the passive preview with the responsive neobrutalist KTM Node Build Desk.

Exit condition met: both layouts remain readable at their target widths with no clipped project labels or overlapping telemetry.

### Phase 4 - Reusable Engine

- [x] Extract telemetry, validation, theme tokens, and rendering into reusable modules.
- [x] Formalize the configuration with `profile.schema.json`.
- [x] Add a one-command local preview and starter configuration.
- [x] Package the renderer as a composite GitHub Action.
- [x] Keep KTM Project Broadcast as the reference implementation.

Exit condition: another user can generate a profile by changing configuration rather than renderer code.

### Phase 5 - Optional Interaction

- [x] Add a GitHub Issue Form for short visitor signals.
- [x] Publish only issue numbers explicitly listed in `signals-approved.json`.
- [x] Escape content, limit message length, deduplicate authors, and cap the display.
- [x] Render the channel independently from the core profile artwork.

The profile remains complete when the channel is empty or disabled.

## Non-Goals

- A live production-monitoring dashboard.
- Fabricated CI, deployment, uptime, or AI-agent activity.
- Per-second clocks or per-visitor rendering.
- A hosted editor in the initial version.
- Private-repository data in generated public assets.

## Release Safety

- Work locally before any push.
- Never write API tokens or environment values into generated SVG files.
- Preserve manually authored status labels as the source of truth.
- Use GitHub's built-in workflow token only for public data and repository writes.
- Do not push generated changes until the rendered result has been reviewed.
