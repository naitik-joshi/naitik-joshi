import test from "node:test";
import assert from "node:assert/strict";
import { tableData, summarize, advanceTour } from "../src/presentation.js";

test("CSV preview supports quoted commas and multiline fields", () => {
  const data = tableData(
    'name,note\r\n"Joshi, Naitik","line one\nline two"',
    "csv",
  );
  assert.equal(data.rows[0].name, "Joshi, Naitik");
  assert.equal(data.rows[0].note, "line one\nline two");
});
test("tables are bounded and primitive arrays stay raw", () => {
  const data = tableData(
    Array.from({ length: 30 }, (_, i) => ({ id: i })),
    "parse",
  );
  assert.equal(data.rows.length, 20);
  assert.equal(data.truncated, true);
  assert.equal(tableData([1, 2, 3], "parse"), null);
  assert.equal(tableData("not a table", "text"), null);
});
test("invalid CSV does not fabricate a table", () => {
  assert.equal(tableData('a,b\n"unclosed', "csv"), null);
});
test("module summaries use real values", () => {
  assert.match(summarize([{ name: "Test" }]), /^1 records\n/);
  assert.equal(summarize("  one\n two"), " one two");
});
test("walkthrough advances, stops at end and clamps back", () => {
  const tour = { order: ["a", "b"], index: 0, playing: true };
  assert.equal(advanceTour(tour).index, 1);
  assert.deepEqual(advanceTour(advanceTour(tour)), {
    order: ["a", "b"],
    index: 1,
    playing: false,
  });
  assert.equal(advanceTour(tour, -1).index, 0);
  assert.equal(advanceTour(tour, -1).playing, false);
});
