# KTM // Patchbay

An experimental, browser-local JSON and text pipeline workbench by Naitik Joshi.

[Open the workbench](https://naitik-joshi.github.io/naitik-joshi/) · [Design and implementation notes](../docs/PATCHBAY.md)

Select a preset, edit the Input payload, and run the patch. Choose a module to
inspect its output. Use ports to connect nodes or the inspector's Input cable
selector to change a connection. Add transformations from the module library.

New here? Open **Examples** to compare inputs and outputs, then choose **Play
walkthrough**. The walkthrough follows your current data through each module;
pause, go backward, or select any numbered step. It does not replace your patch.
On phones the inspector moves above the circuit during a walkthrough.

CSV and arrays of records have a table view. The code icon switches to raw data.
The table previews at most 20 rows and 8 columns; downloads retain the full output.

Export patch saves the graph **and its input** as JSON; Import patch restores it.
Download result exports the selected module's result. Refreshing clears the tab.

## Development

Requires Node 22 or later.

```sh
npm ci
npm test
npm run dev
npm run build
```

React Flow provides the graph editor. React, Vite, and Lucide provide the UI
toolchain and icons. Barlow Condensed, IBM Plex Mono, and Inter are bundled through
Fontsource (SIL Open Font License); their licenses ship in their npm packages.
Dependencies retain their respective licenses. The transform engine is local to
this repository, uses built-in browser APIs, and never executes user code.
