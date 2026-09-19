import React, { useState } from "react";
import { Table2, Code2 } from "lucide-react";
import { asText } from "./engine.js";
import { tableData } from "./presentation.js";

export default function ResultPreview({ value, format }) {
  const [raw, setRaw] = useState(false);
  const data = tableData(value, format);
  const text = asText(value);
  return (
    <>
      {data && (
        <div
          className="result-view-toggle"
          role="group"
          aria-label="Result view"
        >
          <button
            aria-label="Table view"
            title="Table view"
            aria-pressed={!raw}
            onClick={() => setRaw(false)}
          >
            <Table2 size={14} />
          </button>
          <button
            aria-label="Raw data"
            title="Raw data"
            aria-pressed={raw}
            onClick={() => setRaw(true)}
          >
            <Code2 size={14} />
          </button>
        </div>
      )}
      {data && !raw ? (
        <div className="data-table-scroll">
          <table aria-label="Result data">
            <thead>
              <tr>
                {data.fields.map((f) => (
                  <th key={f}>{f}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.rows.map((r, i) => (
                <tr key={i}>
                  {data.fields.map((f) => (
                    <td key={f}>
                      {r[f] == null
                        ? ""
                        : typeof r[f] === "object"
                          ? JSON.stringify(r[f])
                          : String(r[f])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          {data.truncated && (
            <p className="clipped-note">Preview: first 20 rows / 8 columns</p>
          )}
        </div>
      ) : (
        <pre data-testid="result">{text.slice(0, 80000)}</pre>
      )}
      {text.length > 80000 && (
        <p className="clipped-note">
          Preview truncated. Full result available as a download.
        </p>
      )}
    </>
  );
}
