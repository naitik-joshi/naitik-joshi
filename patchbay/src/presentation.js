import Papa from "papaparse";
import { asText } from "./engine.js";

export function summarize(value) {
  if (Array.isArray(value))
    return `${value.length} records\n${JSON.stringify(value[0] ?? {})}`;
  return asText(value).replace(/\s+/g, " ").slice(0, 130);
}

export function tableData(value, format) {
  let rows = value;
  if (format === "csv" && typeof value === "string") {
    const parsed = Papa.parse(value, {
      header: true,
      skipEmptyLines: true,
      preview: 21,
    });
    if (parsed.errors.length) return null;
    rows = parsed.data;
  }
  if (
    !Array.isArray(rows) ||
    !rows.length ||
    rows.some((r) => !r || typeof r !== "object" || Array.isArray(r))
  )
    return null;
  const fields = [...new Set(rows.slice(0, 20).flatMap(Object.keys))];
  if (!fields.length) return null;
  return {
    fields: fields.slice(0, 8),
    rows: rows.slice(0, 20),
    truncated: rows.length > 20 || fields.length > 8,
  };
}

export function advanceTour(tour, direction = 1) {
  const index = Math.max(
    0,
    Math.min(tour.order.length - 1, tour.index + direction),
  );
  return {
    ...tour,
    index,
    playing:
      direction === 1 && tour.index < tour.order.length - 1
        ? tour.playing
        : false,
  };
}
