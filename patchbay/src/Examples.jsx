import React, { useEffect, useRef } from "react";
import { X, ArrowRight, Play } from "lucide-react";
import { PRESETS } from "./presets.js";

const samples = {
  manifest: [
    '[{"name":"ProdTag",\n  "language":"Go"}]',
    "name,language\nProdTag,Go",
    "JSON",
    "CSV",
  ],
  filter: [
    "Java  /  EduStand\nGo    /  ProdTag",
    "Java  /  EduStand",
    "RECORDS (EXCERPT)",
    "1 MATCH",
  ],
  decode: ["S2F0aG1hbmR1IC8gMDU6NDU=", "Kathmandu / 05:45", "BASE64", "TEXT"],
  clean: ["build\n  ship\nbuild", "build\nship", "RAW LINES", "UNIQUE LINES"],
};

export default function Examples({ onClose, onLoad }) {
  const dialog = useRef(null);
  useEffect(() => {
    const element = dialog.current;
    element.showModal();
    return () => element.close();
  }, []);
  return (
    <dialog
      ref={dialog}
      className="examples-dialog"
      aria-labelledby="examples-title"
      onCancel={onClose}
      onClick={(e) => {
        if (e.target === dialog.current) onClose();
      }}
    >
      <header>
        <div>
          <span className="dialog-kicker">KTM // PATCHBAY</span>
          <h2 id="examples-title">Example library</h2>
        </div>
        <button
          className="icon-button"
          aria-label="Close examples"
          title="Close examples"
          onClick={onClose}
        >
          <X size={20} />
        </button>
      </header>
      <div className="example-list">
        {Object.entries(PRESETS).map(([key, p]) => {
          const s = samples[key];
          return (
            <section className="example-item" key={key}>
              <h3>{p.name}</h3>
              <div className="example-comparison">
                <div>
                  <span>{s[2]}</span>
                  <pre>{s[0]}</pre>
                </div>
                <ArrowRight size={18} />
                <div>
                  <span>{s[3]}</span>
                  <pre>{s[1]}</pre>
                </div>
              </div>
              <button className="example-load" onClick={() => onLoad(key)}>
                <Play size={14} />
                Open example
              </button>
            </section>
          );
        })}
      </div>
    </dialog>
  );
}
