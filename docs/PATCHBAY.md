# KTM // Patchbay

## Direction

Replace Nightshift with a useful, playful data instrument: a modular-synth-inspired
workbench where people connect text and JSON operations and inspect each result.
The profile remains the front door, not a long application manual.

The README contains a small, script-free animated SVG. Its single link opens the
real interactive application on GitHub Pages from this same repository. The
preview is an authored demonstration, not live execution inside GitHub Markdown.
No iframe, keyboard game, or arbitrary JavaScript executes in the README.

## Research And Choice

| Direction | Strength | Why choose or reject |
| --- | --- | --- |
| Markdown first-person game | Clever use of linked states | Rejected after hands-on feedback: navigation latency and limited input make play awkward. |
| Repository city / contribution sculpture | Strong passive visual | Another activity visualization, with little practical reason to return. |
| Shared issue-driven world | Native GitHub interaction | Login, public issue noise, moderation, and workflow delay would dominate the experience. |
| Browser-local data patchbay | Visually active and actually useful | Chosen: genuine editing and useful output, static hosting, and a compact profile entry point. |

References informing the implementation:

- [CyberChef](https://github.com/gchq/CyberChef): browser-local transformations and composable operations. This is conceptual inspiration, not a claim to have invented visual pipelines or a copy of CyberChef's operation engine.
- [React Flow computing flows](https://reactflow.dev/learn/advanced-use/computing-flows): proven node/cable interaction. React Flow handles the graph editor; this repository supplies the bounded transformation engine.
- [GitHub Pages custom workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages): build static artifacts through Actions and publish with the built-in token.

## Design

- Surface: GitHub-compatible charcoal `#0d1117` and panel gray `#191e27`.
- Signal colors: coral `#ff6569` source, yellow `#ffcf58` structure, blue `#80a1ff` text, mint `#71e3ba` output.
- Type: bundled Barlow Condensed for module titles, IBM Plex Mono for data, Inter for controls.
- Layout: module library / unframed circuit canvas / editable inspector. On mobile the inspector follows the canvas; a module selector avoids precision tapping.
- Signature: hardware-style modules and patch cables carrying execution state. Motion reflects the run sequence; output remains real and deterministic.

## Implementation Phases

- [x] Research feasibility and select a direction grounded in profile feedback.
- [x] Build pure transformations, graph validation, cycle rejection, and bounded output.
- [x] Implement node editing, reconnection, presets, undo/redo, import/export, result copy/download, error display, and run trace.
- [x] Bundle fonts and dependencies; no CDN scripts or hosted operation APIs.
- [x] Verify desktop and mobile editing, result generation, and invalid-input recovery in the browser.
- [x] Add unit tests for transforms, validation, CSV escaping, Unicode, error propagation, and growth limits.
- [x] Replace the maze with responsive animated README previews.
- [ ] Verify the deployed GitHub Pages build and profile preview after publishing.

## Operating Model

```sh
cd patchbay
npm ci
npm test
npm run dev
npm run build
```

`patchbay/dist` is a static site. The `Test and publish Patchbay` workflow tests and
builds pull requests, then deploys only pushes to `main` and manual runs on `main`.
Enable repository Settings > Pages > Source > GitHub Actions for initial setup.
No separate hosting account, server, database, paid API, or personal token is
required by the application or deployment workflow.

Regenerate the repository-owned preview with:

```sh
python3 scripts/generate_patchbay_preview.py assets
```

## Privacy And Limits

- Input is processed in memory in the current tab. No analytics, external requests for operations, cookies, persistent browser storage, or user accounts.
- Hosting still involves normal GitHub Pages asset requests; this is not a claim that visiting a website produces no network traffic.
- Exported patch JSON includes its input payload. Review the file before sharing it.
- Maximum 40 modules, one incoming cable per transform, no cycles. Branching outputs are supported; joins are not.
- Source and parameter imports are capped at 200,000 characters per module; imported files at 250 KB; intermediate results at 2 million characters.
- Built-in operations only. No `eval`, arbitrary JavaScript, remote URL fetch, AI API calls, or secret collection.
- CSV export neutralizes formula-like string prefixes. It is still the user's responsibility to inspect data before importing it into another tool.
- Refreshing discards the current patch. Export it to keep work. Reduced-motion preferences disable decorative waveform animation and shorten run stepping.

## Next, Only If Useful

1. Add browser-worker execution and CSV import for larger datasets.
2. Add a schema inspector and JSON diff module, with fixtures and error tests.
3. Add a curated patch gallery of actual workflows, not activity counters or fabricated automation.
4. Consider shareable patches only with explicit payload disclosure and a strict URL size cap.

Nightshift's source and generated states remain recoverable from commit `6b0ff26`.
