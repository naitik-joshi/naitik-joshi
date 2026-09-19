const example = JSON.stringify(
  [
    {
      name: "ProdTag",
      language: "Go",
      kind: "Developer tool",
      status: "In development",
    },
    {
      name: "EduStand",
      language: "Java",
      kind: "Learning platform",
      status: "Academic project",
    },
    {
      name: "API Escape",
      language: "Python",
      kind: "API learning",
      status: "Team project",
    },
    {
      name: "Tab Unloader",
      language: "JavaScript",
      kind: "Browser extension",
      status: "Released",
    },
  ],
  null,
  2,
);
function patch(name, ops) {
  return {
    name,
    nodes: ops.map(([op, param = ""], i) => ({
      id: `m${i}`,
      type: "module",
      position: { x: (i % 3) * 290, y: Math.floor(i / 3) * 285 },
      data: { op, param },
    })),
    edges: ops
      .slice(1)
      .map((_, i) => ({ id: `e${i}`, source: `m${i}`, target: `m${i + 1}` })),
  };
}
export const PRESETS = {
  manifest: patch("JSON to spreadsheet", [
    ["source", example],
    ["parse"],
    ["pick", "name, language, status"],
    ["csv"],
    ["output"],
  ]),
  filter: patch("Filter JSON records", [
    ["source", example],
    ["parse"],
    ["filter", "language=Java"],
    ["stringify"],
    ["output"],
  ]),
  decode: patch("Base64 to readable text", [
    [
      "source",
      "S2F0aG1hbmR1IC8gMDU6NDUKTWFrZSBpdCB3b3JrLiBNYWtlIGl0IHdlaXJkLg==",
    ],
    ["base64decode"],
    ["trim"],
    ["output"],
  ]),
  clean: patch("Remove duplicate lines", [
    ["source", "  build\nship\n  learn\nbuild\nlearn\n  repeat  "],
    ["trim"],
    ["unique"],
    ["output"],
  ]),
};
export function getPreset(key) {
  return structuredClone(PRESETS[key]);
}
