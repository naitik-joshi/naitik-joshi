import test from "node:test";
import assert from "node:assert/strict";
import {
  transform,
  evaluate,
  canConnect,
  validatePatch,
  exportPatch,
} from "../src/engine.js";
import { PRESETS, getPreset } from "../src/presets.js";

test("expanding pipelines stop at the output size limit", () => {
  const nodes = Array.from({length: 20}, (_, i) => ({id: `n${i}`, data: {op: i ? 'base64encode' : 'source', param: i ? '' : 'x'.repeat(200000)}}));
  const edges = nodes.slice(1).map((n,i) => ({source:`n${i}`,target:n.id}));
  assert.match(evaluate(nodes,edges).results.n19.error, /exceeds 2 million/);
});

test("all presets execute and produce an output", () => {
  for (const key of Object.keys(PRESETS)) {
    const p = getPreset(key),
      run = evaluate(p.nodes, p.edges);
    assert.equal(
      Object.values(run.results).filter((r) => r.error).length,
      0,
      key,
    );
    assert.ok(run.results[p.nodes.at(-1).id].value);
  }
});
test("manifest produces genuine CSV", () => {
  const p = getPreset("manifest");
  const value = evaluate(p.nodes, p.edges).results.m4.value;
  assert.match(value, /name,language,status\r\nProdTag,Go,In development/);
  assert.equal(value.split("\r\n").length, 5);
});
test("filter, sort and select do not mutate the input", () => {
  const rows = [
    { n: 10, name: "B" },
    { n: 2, name: "A" },
  ];
  assert.deepEqual(
    transform("sort", rows, "n").map((r) => r.n),
    [2, 10],
  );
  assert.equal(rows[0].n, 10);
  assert.deepEqual(transform("filter", rows, "name=A"), [rows[1]]);
  assert.deepEqual(transform("pick", rows, "name"), [
    { name: "B" },
    { name: "A" },
  ]);
});
test("CSV escapes and neutralizes spreadsheet formulas", () => {
  assert.equal(
    transform("csv", [{ a: 'x,"y"', b: "=1+2" }]),
    'a,b\r\n"x,""y""",\'=1+2',
  );
});
test("Base64 supports Unicode and rejects malformed input", () => {
  const value = "Kathmandu / \u0928\u0947\u092a\u093e\u0932";
  assert.equal(
    transform("base64decode", transform("base64encode", value)),
    value,
  );
  assert.throws(() => transform("base64decode", "!invalid!"));
});
test("missing input, bad JSON and downstream failures are explicit", () => {
  const p = getPreset("manifest");
  p.nodes[0].data.param = "not JSON";
  const run = evaluate(p.nodes, p.edges);
  assert.ok(run.results.m1.error);
  assert.match(run.results.m4.error, /Upstream/);
  assert.match(evaluate(p.nodes, []).results.m1.error, /Connect an input/);
});
test("connections reject cycles, multiple inputs and invalid ports", () => {
  const p = getPreset("manifest");
  assert.equal(canConnect(p.nodes, p.edges, "m0", "m2"), false);
  assert.equal(canConnect(p.nodes, [], "m4", "m1"), false);
  assert.equal(canConnect(p.nodes, [], "m1", "m0"), false);
  assert.equal(
    canConnect(p.nodes, [{ source: "m1", target: "m2" }], "m2", "m1"),
    false,
  );
  assert.equal(canConnect(p.nodes, [], "m0", "m1"), true);
});
test("patch serialization excludes runtime state and round-trips", () => {
  const p = getPreset("manifest");
  p.nodes[0].data.result = { value: "secret" };
  const clean = validatePatch(exportPatch(p.nodes, p.edges));
  assert.equal(clean.nodes[0].data.result, undefined);
  assert.equal(evaluate(clean.nodes, clean.edges).results.m4.error, undefined);
});
test("untrusted patch imports reject malformed and inherited operations", () => {
  for (const op of ["toString", "constructor", "invalid"]) {
    const p = exportPatch(getPreset("manifest").nodes, []);
    p.nodes[0].data.op = op;
    assert.throws(() => validatePatch(p));
  }
  assert.throws(() => validatePatch({ version: 1, nodes: [null], edges: [] }));
  const p = exportPatch(getPreset("manifest").nodes, []);
  p.nodes[0].data.param = "x".repeat(200001);
  assert.throws(() => validatePatch(p));
});
test("prototype-like node IDs do not alias cached results", () => {
  const p = getPreset("clean");
  p.nodes[0].id = "__proto__";
  p.edges[0].source = "__proto__";
  assert.equal(
    evaluate(p.nodes, p.edges).results.m3.value,
    "build\nship\nlearn\nrepeat",
  );
});
