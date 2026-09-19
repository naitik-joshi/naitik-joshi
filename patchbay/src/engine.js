export const MODULES = {
  source: {
    name: "Input",
    group: "Source",
    color: "#ff6569",
    code: "IN",
    format: "text",
  },
  parse: {
    name: "Parse JSON",
    group: "Structure",
    color: "#ffcf58",
    code: "{}",
    format: "JSON",
  },
  pick: {
    name: "Select fields",
    group: "Structure",
    color: "#ffcf58",
    code: "SEL",
    format: "JSON",
    default: "name, language",
  },
  filter: {
    name: "Filter records",
    group: "Structure",
    color: "#ffcf58",
    code: "FLT",
    format: "JSON",
    default: "language=Java",
  },
  sort: {
    name: "Sort records",
    group: "Structure",
    color: "#ffcf58",
    code: "SORT",
    format: "JSON",
    default: "name",
  },
  csv: {
    name: "To CSV",
    group: "Export",
    color: "#71e3ba",
    code: "CSV",
    format: "text",
  },
  stringify: {
    name: "Format JSON",
    group: "Export",
    color: "#71e3ba",
    code: "FMT",
    format: "text",
  },
  base64decode: {
    name: "Decode Base64",
    group: "Text",
    color: "#80a1ff",
    code: "B64",
    format: "text",
  },
  base64encode: {
    name: "Encode Base64",
    group: "Text",
    color: "#80a1ff",
    code: "64+",
    format: "text",
  },
  trim: {
    name: "Trim lines",
    group: "Text",
    color: "#80a1ff",
    code: "TRM",
    format: "text",
  },
  unique: {
    name: "Unique lines",
    group: "Text",
    color: "#80a1ff",
    code: "UNQ",
    format: "text",
  },
  output: {
    name: "Output",
    group: "Destination",
    color: "#71e3ba",
    code: "OUT",
    format: "any",
  },
};

export function asText(value) {
  return typeof value === "string" ? value : JSON.stringify(value, null, 2);
}
function textOnly(value) {
  if (typeof value !== "string")
    throw new Error("Expected text. Add Format JSON before this module.");
  return value;
}
function records(value) {
  if (
    !Array.isArray(value) ||
    value.some((v) => !v || typeof v !== "object" || Array.isArray(v))
  )
    throw new Error("Expected an array of objects.");
  return value;
}
function own(object, key) {
  return Object.hasOwn(object, key) ? object[key] : undefined;
}
function csvCell(value) {
  let text =
    value == null
      ? ""
      : typeof value === "object"
        ? JSON.stringify(value)
        : String(value);
  // Neutralize spreadsheet formula prefixes in exported untrusted strings.
  if (typeof value === "string" && /^[\s]*[=+@-]/.test(text)) text = "'" + text;
  return /[",\r\n]/.test(text) ? '"' + text.replaceAll('"', '""') + '"' : text;
}
export function transform(op, value, parameter = "") {
  switch (op) {
    case "source":
      return parameter;
    case "output":
      return value;
    case "parse":
      return JSON.parse(textOnly(value));
    case "stringify":
      return JSON.stringify(value, null, 2);
    case "trim":
      return textOnly(value)
        .split(/\r?\n/)
        .map((line) => line.trim())
        .join("\n")
        .trim();
    case "unique":
      return [...new Set(textOnly(value).split(/\r?\n/))].join("\n");
    case "base64encode":
      return btoa(
        Array.from(new TextEncoder().encode(textOnly(value)), (byte) =>
          String.fromCharCode(byte),
        ).join(""),
      );
    case "base64decode":
      return new TextDecoder("utf-8", { fatal: true }).decode(
        Uint8Array.from(atob(textOnly(value).replace(/\s/g, "")), (c) =>
          c.charCodeAt(0),
        ),
      );
    case "pick": {
      const fields = parameter
        .split(",")
        .map((field) => field.trim())
        .filter(Boolean);
      if (!fields.length) throw new Error("Enter at least one field name.");
      const select = (row) => {
        if (!row || typeof row !== "object" || Array.isArray(row))
          throw new Error("Expected an object or array of objects.");
        return Object.fromEntries(
          fields
            .filter((key) => Object.hasOwn(row, key))
            .map((key) => [key, own(row, key)]),
        );
      };
      return Array.isArray(value) ? value.map(select) : select(value);
    }
    case "filter": {
      const split = parameter.indexOf("=");
      if (split < 1)
        throw new Error("Use field=value, for example language=Java.");
      const key = parameter.slice(0, split).trim(),
        expected = parameter.slice(split + 1).trim();
      return records(value).filter((row) => String(own(row, key)) === expected);
    }
    case "sort": {
      const field = parameter.trim();
      if (!field) throw new Error("Enter a field to sort.");
      return [...records(value)].sort((a, b) => {
        const x = own(a, field),
          y = own(b, field);
        return typeof x === "number" && typeof y === "number"
          ? x - y
          : String(x ?? "").localeCompare(String(y ?? ""), "en", {
              numeric: true,
            });
      });
    }
    case "csv": {
      const rows = records(value);
      const keys = [...new Set(rows.flatMap(Object.keys))];
      return [
        keys.map(csvCell).join(","),
        ...rows.map((row) =>
          keys.map((key) => csvCell(own(row, key))).join(","),
        ),
      ].join("\r\n");
    }
    default:
      throw new Error("Unknown module.");
  }
}

export function canConnect(nodes, edges, source, target) {
  if (
    source === target ||
    !nodes.some((n) => n.id === source) ||
    !nodes.some((n) => n.id === target)
  )
    return false;
  if (
    nodes.find((n) => n.id === target).data.op === "source" ||
    nodes.find((n) => n.id === source).data.op === "output"
  )
    return false;
  if (edges.some((e) => e.target === target)) return false;
  const seen = new Set();
  const stack = [target];
  while (stack.length) {
    const id = stack.pop();
    if (id === source) return false;
    if (seen.has(id)) continue;
    seen.add(id);
    edges.filter((e) => e.source === id).forEach((e) => stack.push(e.target));
  }
  return true;
}

export function evaluate(nodes, edges) {
  const results = Object.create(null),
    visiting = new Set(),
    order = [];
  const byId = new Map(nodes.map((node) => [node.id, node]));
  function visit(id) {
    if (results[id]) return results[id];
    if (visiting.has(id)) throw new Error("A patch cannot contain a loop.");
    visiting.add(id);
    const node = byId.get(id);
    try {
      if (!node) throw new Error("Missing module.");
      let input;
      if (node.data.op !== "source") {
        const connections = edges.filter((edge) => edge.target === id);
        if (connections.length !== 1)
          throw new Error(
            connections.length
              ? "Only one input cable is supported."
              : "Connect an input cable.",
          );
        const upstream = visit(connections[0].source);
        if (upstream.error) throw new Error("Upstream: " + upstream.error);
        input = upstream.value;
      }
      const value = transform(node.data.op, input, node.data.param);
      if (asText(value).length > 2000000)
        throw new Error("Module output exceeds 2 million characters. Reduce the input or patch length.");
      results[id] = {
        value,
        count: Array.isArray(value) ? value.length : null,
        type:
          typeof value === "string"
            ? "TEXT"
            : Array.isArray(value)
              ? "ARRAY"
              : "JSON",
      };
    } catch (error) {
      results[id] = { error: error.message };
    }
    visiting.delete(id);
    order.push(id);
    return results[id];
  }
  nodes.forEach((node) => visit(node.id));
  return { results, order };
}

export function exportPatch(nodes, edges) {
  return {
    version: 1,
    nodes: nodes.map(({ id, position, data }) => ({
      id,
      position,
      data: { op: data.op, param: data.param ?? "" },
    })),
    edges: edges.map(({ id, source, target }) => ({ id, source, target })),
  };
}
export function validatePatch(patch) {
  if (
    patch?.version !== 1 ||
    !Array.isArray(patch.nodes) ||
    !Array.isArray(patch.edges) ||
    patch.nodes.length > 40 ||
    patch.edges.length > 80
  )
    throw new Error("Invalid patch. Maximum 40 modules and 80 cables.");
  const ids = new Set();
  for (const n of patch.nodes) {
    if (
      !n ||
      typeof n.id !== "string" ||
      !/^[\w-]{1,100}$/.test(n.id) ||
      ids.has(n.id) ||
      !Object.hasOwn(MODULES, n.data?.op) ||
      typeof n.data.param !== "string" ||
      n.data.param.length > 200000 ||
      !Number.isFinite(n.position?.x) ||
      !Number.isFinite(n.position?.y)
    )
      throw new Error("Invalid module data.");
    ids.add(n.id);
  }
  const accepted = [];
  for (const e of patch.edges) {
    if (
      !e ||
      typeof e.id !== "string" ||
      accepted.some((a) => a.id === e.id) ||
      !canConnect(patch.nodes, accepted, e.source, e.target)
    )
      throw new Error("Invalid cable or loop in patch.");
    accepted.push(e);
  }
  return exportPatch(patch.nodes, accepted);
}
