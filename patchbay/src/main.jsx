import React, { useState, useRef, useCallback } from "react";
import { createRoot } from "react-dom/client";
import {
  ReactFlow,
  Background,
  BackgroundVariant,
  Controls,
  Handle,
  Position,
  applyNodeChanges,
  applyEdgeChanges,
} from "@xyflow/react";
import {
  Play,
  Plus,
  Trash2,
  Copy,
  Download,
  Upload,
  Undo2,
  Redo2,
  Cable,
  Check,
  CircleAlert,
  ArrowUpRight,
  Braces,
  FileInput,
  FileOutput,
  Scissors,
  SlidersHorizontal,
  X,
  PanelLeft,
  Expand,
  Github,
  Zap,
} from "lucide-react";
import {
  MODULES,
  asText,
  evaluate,
  canConnect,
  exportPatch,
  validatePatch,
} from "./engine.js";
import { PRESETS, getPreset } from "./presets.js";
import "@xyflow/react/dist/style.css";
import "@fontsource/barlow-condensed/latin-700.css";
import "@fontsource/barlow-condensed/latin-800.css";
import "@fontsource/ibm-plex-mono/latin-400.css";
import "@fontsource/ibm-plex-mono/latin-500.css";
import "@fontsource/inter/latin-400.css";
import "@fontsource/inter/latin-500.css";
import "@fontsource/inter/latin-600.css";
import "./style.css";

function ModuleNode({ data, selected }) {
  const meta = MODULES[data.op],
    result = data.result;
  const status = data.active
    ? "PROCESSING"
    : result?.error
      ? "CHECK INPUT"
      : result
        ? "PROCESSED"
        : "READY";
  return (
    <div
      className={`module ${selected ? "chosen" : ""} ${data.active ? "executing" : ""}`}
      style={{ "--accent": meta.color }}
    >
      {data.op !== "source" && (
        <Handle
          type="target"
          position={Position.Left}
          aria-label="Input port"
        />
      )}
      <div className="module-head">
        <span className="module-code">{meta.code}</span>
        <span>{meta.group.toUpperCase()}</span>
        <i className={result?.error ? "error-dot" : ""} />
      </div>
      <div className="module-body">
        <h3>{meta.name}</h3>
        <div className="module-parameter">
          {data.op === "source"
            ? "LOCAL PAYLOAD"
            : data.param || meta.format.toUpperCase()}
        </div>
        <div className="waveform" aria-hidden="true">
          {[18, 29, 16, 39, 25, 48, 36, 20, 42, 31, 18, 26, 44, 34, 16, 24].map(
            (h, i) => (
              <b
                key={i}
                style={{ height: h / 2, animationDelay: `${i * 35}ms` }}
              />
            ),
          )}
        </div>
      </div>
      <div className="module-foot">
        <span>{status}</span>
        <span>
          {result?.error ? (
            <CircleAlert size={13} />
          ) : result ? (
            <Check size={13} />
          ) : (
            <span className="empty-led" />
          )}
        </span>
      </div>
      {data.op !== "output" && (
        <Handle
          type="source"
          position={Position.Right}
          aria-label="Output port"
        />
      )}
    </div>
  );
}
const nodeTypes = { module: ModuleNode };
const initial = getPreset("manifest");
function IconButton({ label, children, ...props }) {
  return (
    <button
      type="button"
      className="icon-button"
      aria-label={label}
      title={label}
      {...props}
    >
      {children}
    </button>
  );
}
function download(name, text, type = "text/plain") {
  const url = URL.createObjectURL(new Blob([text], { type }));
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function App() {
  const [graph, setGraph] = useState(initial),
    [preset, setPreset] = useState("manifest"),
    [selected, setSelected] = useState("m4");
  const [execution, setExecution] = useState(() =>
      evaluate(initial.nodes, initial.edges),
    ),
    [active, setActive] = useState(null),
    [running, setRunning] = useState(false),
    [elapsed, setElapsed] = useState(null);
  const [notice, setNotice] = useState(""),
    [shelf, setShelf] = useState(false),
    [tab, setTab] = useState("result"),
    [history, setHistory] = useState({ past: [], future: [] });
  const flow = useRef(null),
    epoch = useRef(0),
    noticeTimer = useRef(null),
    importInput = useRef(null),
    dragStart = useRef(null);
  const chosen = graph.nodes.find((n) => n.id === selected),
    result = execution.results[selected],
    meta = chosen ? MODULES[chosen.data.op] : null;
  function notify(message) {
    setNotice(message);
    clearTimeout(noticeTimer.current);
    noticeTimer.current = setTimeout(() => setNotice(""), 4500);
  }
  function invalidate() {
    epoch.current++;
    setRunning(false);
    setActive(null);
    setExecution({ results: {}, order: [] });
    setElapsed(null);
  }
  function change(next, record = true) {
    if (record)
      setHistory((h) => ({
        past: [...h.past, exportPatch(graph.nodes, graph.edges)].slice(-30),
        future: [],
      }));
    setGraph(next);
    setPreset("custom");
    invalidate();
  }
  function restore(value) {
    setGraph({
      ...value,
      nodes: value.nodes.map((n) => ({ ...n, type: "module" })),
    });
    setSelected(value.nodes.at(-1)?.id ?? null);
    setPreset("custom");
    invalidate();
  }
  function undo() {
    if (!history.past.length) return;
    const previous = history.past.at(-1);
    setHistory({
      past: history.past.slice(0, -1),
      future: [exportPatch(graph.nodes, graph.edges), ...history.future],
    });
    restore(previous);
  }
  function redo() {
    if (!history.future.length) return;
    const next = history.future[0];
    setHistory({
      past: [...history.past, exportPatch(graph.nodes, graph.edges)],
      future: history.future.slice(1),
    });
    restore(next);
  }
  function addModule(op) {
    if (graph.nodes.length >= 40) {
      notify("This patch has reached 40 modules.");
      return;
    }
    const id = crypto.randomUUID();
    const last = graph.nodes.at(-1);
    const position = flow.current?.screenToFlowPosition({
      x: window.innerWidth * 0.46,
      y: window.innerHeight * 0.45,
    }) ?? { x: 200, y: 100 };
    change({
      ...graph,
      nodes: [
        ...graph.nodes,
        {
          id,
          type: "module",
          position: {
            x: position.x + (graph.nodes.length % 3) * 22,
            y: position.y,
          },
          data: {
            op,
            param: op === "source" ? "" : (MODULES[op].default ?? ""),
          },
        },
      ],
    });
    setSelected(id);
    setShelf(false);
  }
  function removeNode() {
    if (!chosen) return;
    change({
      ...graph,
      nodes: graph.nodes.filter((n) => n.id !== selected),
      edges: graph.edges.filter(
        (e) => e.source !== selected && e.target !== selected,
      ),
    });
    setSelected(null);
  }
  function setParameter(param) {
    change({
      ...graph,
      nodes: graph.nodes.map((n) =>
        n.id === selected ? { ...n, data: { ...n.data, param } } : n,
      ),
    });
  }
  function setInput(source) {
    const edges = graph.edges.filter((e) => e.target !== selected);
    if (source && !canConnect(graph.nodes, edges, source, selected)) {
      notify("That connection would create a loop.");
      return;
    }
    change({
      ...graph,
      edges: source
        ? [...edges, { id: crypto.randomUUID(), source, target: selected }]
        : edges,
    });
  }
  function connect(connection) {
    if (
      !canConnect(
        graph.nodes,
        graph.edges,
        connection.source,
        connection.target,
      )
    ) {
      notify("One input per module; loops are not allowed.");
      return;
    }
    change({
      ...graph,
      edges: [...graph.edges, { ...connection, id: crypto.randomUUID() }],
    });
  }
  const onNodesChange = useCallback((changes) => {
    setGraph((g) => ({ ...g, nodes: applyNodeChanges(changes, g.nodes) }));
  }, []);
  function onEdgesChange(changes) {
    if (changes.some((c) => c.type === "remove"))
      change({ ...graph, edges: applyEdgeChanges(changes, graph.edges) });
    else setGraph((g) => ({ ...g, edges: applyEdgeChanges(changes, g.edges) }));
  }
  function loadPreset(key) {
    const next = getPreset(key);
    change(next);
    setPreset(key);
    setSelected(next.nodes.at(-1).id);
    setTab("result");
    setShelf(false);
    setTimeout(
      () => flow.current?.fitView({ padding: 0.18, duration: 300 }),
      60,
    );
  }
  function run() {
    if (!graph.nodes.length) {
      notify("Add an Input module to begin.");
      return;
    }
    const current = ++epoch.current;
    const start = performance.now();
    const calculated = evaluate(graph.nodes, graph.edges);
    const duration = performance.now() - start;
    setRunning(true);
    setExecution({ results: {}, order: calculated.order });
    setElapsed(null);
    const reduced = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    let i = 0;
    function step() {
      if (epoch.current !== current) return;
      const id = calculated.order[i];
      if (!id) {
        setActive(null);
        setRunning(false);
        setElapsed(duration);
        return;
      }
      setActive(id);
      setExecution((e) => ({
        ...e,
        results: { ...e.results, [id]: calculated.results[id] },
      }));
      i++;
      setTimeout(step, reduced ? 0 : 180);
    }
    step();
  }
  async function copyResult() {
    if (!result || result.error) return;
    try {
      await navigator.clipboard.writeText(asText(result.value));
      notify("Result copied.");
    } catch {
      notify("Clipboard unavailable. Use Download result.");
    }
  }
  function downloadResult() {
    if (!result || result.error) return;
    const incoming = graph.edges.find((e) => e.target === selected);
    const upstream = graph.nodes.find((n) => n.id === incoming?.source);
    const op = chosen.data.op === "output" ? upstream?.data.op : chosen.data.op;
    download(
      `patchbay-result.${op === "csv" ? "csv" : op === "stringify" || typeof result.value === "object" ? "json" : "txt"}`,
      asText(result.value),
    );
  }
  async function importPatch(event) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    try {
      if (file.size > 250000)
        throw new Error("Patch files must be smaller than 250 KB.");
      const patch = validatePatch(JSON.parse(await file.text()));
      change({
        ...patch,
        nodes: patch.nodes.map((n) => ({ ...n, type: "module" })),
      });
      setSelected(patch.nodes.at(-1)?.id);
      setTimeout(() => flow.current?.fitView({ padding: 0.18 }), 80);
      notify("Patch loaded.");
    } catch (error) {
      notify(error.message);
    }
  }
  const nodes = graph.nodes.map((n) => ({
    ...n,
    selected: n.id === selected,
    data: {
      ...n.data,
      result: execution.results[n.id],
      active: n.id === active,
    },
  }));
  const edges = graph.edges.map((e) => ({
    ...e,
    type: "smoothstep",
    animated:
      running &&
      Boolean(execution.results[e.source]) &&
      !execution.results[e.source]?.error,
    style: {
      stroke:
        MODULES[graph.nodes.find((n) => n.id === e.source)?.data.op]?.color ??
        "#777",
      strokeWidth: 2.5,
    },
  }));
  const successful = Object.values(execution.results).filter(
      (r) => !r.error,
    ).length,
    errors = Object.values(execution.results).filter((r) => r.error).length;
  return (
    <div className="app">
      <header className="topbar">
        <a className="brand" href="https://github.com/naitik-joshi">
          <span className="brand-mark">
            <Cable size={22} />
          </span>
          <span>
            KTM <em>//</em> PATCHBAY<small>NAITIK JOSHI / EXPERIMENT 02</small>
          </span>
        </a>
        <div className="top-actions">
          <span className="local-status">
            <i />
            LOCAL PROCESSING
          </span>
          <a
            className="icon-button"
            href="https://github.com/naitik-joshi/naitik-joshi/tree/main/patchbay"
            title="View source"
            aria-label="View source"
          >
            <Github size={19} />
          </a>
        </div>
      </header>
      <nav className="toolbar" aria-label="Patch controls">
        <IconButton
          label="Toggle module library"
          onClick={() => setShelf(!shelf)}
        >
          <PanelLeft size={18} />
        </IconButton>
        <label className="preset-label">
          <span>PATCH</span>
          <select
            aria-label="Choose a patch"
            value={preset}
            onChange={(e) => loadPreset(e.target.value)}
          >
            <option value="custom" disabled>Custom patch</option>
            {Object.entries(PRESETS).map(([key, p]) => (
              <option key={key} value={key}>
                {p.name}
              </option>
            ))}
          </select>
        </label>
        <div className="toolbar-spacer" />
        <IconButton label="Undo" onClick={undo} disabled={!history.past.length}>
          <Undo2 size={18} />
        </IconButton>
        <IconButton
          label="Redo"
          onClick={redo}
          disabled={!history.future.length}
        >
          <Redo2 size={18} />
        </IconButton>
        <span className="separator" />
        <IconButton
          label="Import patch"
          onClick={() => importInput.current.click()}
        >
          <Upload size={18} />
        </IconButton>
        <input
          type="file"
          accept=".json,application/json"
          ref={importInput}
          onChange={importPatch}
          hidden
        />
        <IconButton
          label="Export patch"
          onClick={() =>
            download(
              "ktm-patch.json",
              JSON.stringify(exportPatch(graph.nodes, graph.edges), null, 2),
              "application/json",
            )
          }
        >
          <Download size={18} />
        </IconButton>
        <button className="run-button" onClick={run} disabled={running}>
          <Play size={15} fill="currentColor" />
          {running ? "RUNNING" : "RUN PATCH"}
        </button>
      </nav>
      <main className={`workbench ${shelf ? "shelf-open" : ""}`}>
        <aside className="library" aria-label="Module library">
          <div className="section-heading">
            <span>MODULE LIBRARY</span>
            <span className="count">{Object.keys(MODULES).length}</span>
          </div>
          {["Source", "Structure", "Text", "Export", "Destination"].map(
            (group) => (
              <section key={group}>
                <h2>{group}</h2>
                {Object.entries(MODULES)
                  .filter(([, m]) => m.group === group)
                  .map(([op, m]) => (
                    <button
                      className="library-item"
                      key={op}
                      onClick={() => addModule(op)}
                    >
                      <span className="library-code" style={{ color: m.color }}>
                        {m.code}
                      </span>
                      <span>{m.name}</span>
                      <Plus size={13} />
                    </button>
                  ))}
              </section>
            ),
          )}
          <div className="library-bottom">
            <span className="stamp">05:45</span>
            <span>
              KATHMANDU
              <br />
              OPEN CIRCUIT LAB
            </span>
          </div>
        </aside>
        <section className="canvas-region" aria-label="Patch canvas">
          <div className="canvas-title">
            <span>
              <i />
              PATCH CIRCUIT
            </span>
            <span>
              {graph.nodes.length} MODULES / {graph.edges.length} CABLES
            </span>
          </div>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            nodeTypes={nodeTypes}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={connect}
            isValidConnection={(c) =>
              canConnect(graph.nodes, graph.edges, c.source, c.target)
            }
            onNodeClick={(_, node) => setSelected(node.id)}
            onPaneClick={() => setSelected(null)}
            onInit={(instance) => (flow.current = instance)}
            onNodeDragStart={() =>
              (dragStart.current = exportPatch(graph.nodes, graph.edges))
            }
            onNodeDragStop={() => {
              const previous = dragStart.current;
              if (previous)
                setHistory((h) => ({
                  past: [...h.past, previous].slice(-30),
                  future: [],
                }));
            }}
            fitView
            fitViewOptions={{ padding: 0.18 }}
            minZoom={0.3}
            maxZoom={1.6}
            colorMode="dark"
            deleteKeyCode={null}
            nodesConnectable={!running}
            defaultEdgeOptions={{ type: "smoothstep" }}
          >
            <Background
              variant={BackgroundVariant.Dots}
              gap={22}
              size={1}
              color="#353b46"
            />
            <Controls showInteractive={false} />
          </ReactFlow>
          <div className="circuit-caption">
            <span className="crosshair">+</span>
            <span>DATA IN. POSSIBILITIES OUT.</span>
            <span className="crosshair">+</span>
          </div>
        </section>
        <aside className="inspector" aria-label="Module inspector">
          <div className="section-heading">
            <span>INSPECTOR</span>
            <select aria-label="Inspect module" value={selected ?? ""} onChange={e=>setSelected(e.target.value || null)}>
              <option value="">Select module</option>
              {graph.nodes.map((n,i)=><option key={n.id} value={n.id}>{i+1}. {MODULES[n.data.op].name}</option>)}
            </select>
          </div>
          {chosen ? (
            <>
              <div className="inspector-identity">
                <span className="inspector-code" style={{ color: meta.color }}>
                  {meta.code}
                </span>
                <div>
                  <h2>{meta.name}</h2>
                  <span>{meta.group} module</span>
                </div>
                <IconButton label="Delete selected module" onClick={removeNode}>
                  <Trash2 size={16} />
                </IconButton>
              </div>
              {chosen.data.op !== "source" && (
                <label className="field">
                  <span>INPUT CABLE</span>
                  <select
                    aria-label="Input cable"
                    value={
                      graph.edges.find((e) => e.target === selected)?.source ??
                      ""
                    }
                    onChange={(e) => setInput(e.target.value)}
                  >
                    <option value="">Disconnected</option>
                    {graph.nodes
                      .filter(
                        (n) => n.id !== selected && n.data.op !== "output",
                      )
                      .map((n, i) => (
                        <option value={n.id} key={n.id}>
                          {MODULES[n.data.op].name} [
                          {graph.nodes.indexOf(n) + 1}]
                        </option>
                      ))}
                  </select>
                </label>
              )}
              {chosen.data.op === "source" ? (
                <label className="field">
                  <span>
                    PAYLOAD <small>MAX 200,000 CHARACTERS</small>
                  </span>
                  <textarea
                    className="source-editor"
                    aria-label="Input payload"
                    maxLength={200000}
                    spellCheck="false"
                    value={chosen.data.param}
                    onChange={(e) => setParameter(e.target.value)}
                  />
                </label>
              ) : MODULES[chosen.data.op].default !== undefined ? (
                <label className="field">
                  <span>
                    {chosen.data.op === "pick"
                      ? "FIELDS (COMMA SEPARATED)"
                      : chosen.data.op === "sort"
                        ? "SORT FIELD"
                        : "MATCH (FIELD=VALUE)"}
                  </span>
                  <input
                    aria-label="Module parameter"
                    value={chosen.data.param}
                    onChange={(e) => setParameter(e.target.value)}
                  />
                </label>
              ) : null}
              <div className="result-tabs">
                <button
                  className={tab === "result" ? "active" : ""}
                  onClick={() => setTab("result")}
                >
                  RESULT
                </button>
                <button
                  className={tab === "trace" ? "active" : ""}
                  onClick={() => setTab("trace")}
                >
                  RUN TRACE
                </button>
                <div className="toolbar-spacer" />
                <IconButton
                  label="Copy result"
                  onClick={copyResult}
                  disabled={!result || Boolean(result.error)}
                >
                  <Copy size={14} />
                </IconButton>
                <IconButton
                  label="Download result"
                  onClick={downloadResult}
                  disabled={!result || Boolean(result.error)}
                >
                  <Download size={14} />
                </IconButton>
              </div>
              {tab === "result" ? (
                <div className="result-area">
                  {!result ? (
                    <div className="empty-state">
                      <Zap size={25} />
                      <strong>Ready for a signal</strong>
                      <span>Run patch</span>
                    </div>
                  ) : result.error ? (
                    <div className="error-state" role="alert">
                      <CircleAlert size={23} />
                      <strong>{result.error}</strong>
                    </div>
                  ) : (
                    <>
                      <div className="result-meta">
                        <span>{result.type}</span>
                        <span>
                          {result.count !== null
                            ? `${result.count} RECORDS`
                            : `${new TextEncoder().encode(asText(result.value)).length} BYTES`}
                        </span>
                      </div>
                      <pre data-testid="result">
                        {asText(result.value).slice(0, 80000)}
                      </pre>
                      {asText(result.value).length > 80000 && (
                        <p className="clipped-note">
                          Preview truncated. Download for the full result.
                        </p>
                      )}
                    </>
                  )}
                </div>
              ) : (
                <ol className="trace">
                  {execution.order.map((id) => {
                    const n = graph.nodes.find((n) => n.id === id),
                      r = execution.results[id];
                    return (
                      <li key={id} className={r?.error ? "trace-error" : ""}>
                        {r?.error ? (
                          <CircleAlert size={14} />
                        ) : r ? (
                          <Check size={14} />
                        ) : (
                          <span className="empty-led" />
                        )}
                        <span>{MODULES[n.data.op].name}</span>
                        <small>
                          {r?.error ? "ERROR" : (r?.type ?? "WAIT")}
                        </small>
                      </li>
                    );
                  })}
                </ol>
              )}
            </>
          ) : (
            <div className="empty-state">
              <Cable size={30} />
              <strong>No module selected</strong>
              <span>
                {graph.nodes.length
                  ? "Select a module"
                  : "Add a module from the library"}
              </span>
            </div>
          )}
          <div className="privacy-note">
            <i />
            Your input stays in this browser tab.
          </div>
        </aside>
      </main>
      <footer className="statusbar">
        <span>
          <i className={errors ? "warning" : ""} />
          {running
            ? "SIGNAL IN TRANSIT"
            : errors
              ? `${errors} MODULE${errors === 1 ? "" : "S"} NEED ATTENTION`
              : successful
                ? `${successful} MODULES PROCESSED`
                : "READY"}
        </span>
        <span>
          {elapsed !== null ? `${elapsed.toFixed(2)} ms` : "LOCAL SESSION"}
          <b> / </b>NO ACCOUNT REQUIRED
        </span>
        <a href="https://github.com/naitik-joshi">
          BUILT BY NAITIK <ArrowUpRight size={12} />
        </a>
      </footer>
      {notice && (
        <div className="toast" role="status">
          {notice}
          <IconButton
            label="Dismiss notification"
            onClick={() => setNotice("")}
          >
            <X size={14} />
          </IconButton>
        </div>
      )}
    </div>
  );
}
createRoot(document.getElementById("root")).render(<App />);
