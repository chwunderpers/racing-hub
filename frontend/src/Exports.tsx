import { useEffect, useState } from "react";
import { Download, RefreshCw } from "lucide-react";
import { downloadExport, getExportSelection } from "./api/client";

export function Exports() {
  const [selection, setSelection] = useState<{ publicationVersion: string | null } | null>(null);
  const [attempt, setAttempt] = useState(0);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [format, setFormat] = useState<"json" | "csv" | "turtle">("json");
  useEffect(() => {
    let active = true;
    setSelection(null);
    setError("");
    getExportSelection().then(result => { if (active) setSelection(result); })
      .catch(() => { if (active) setError("Publication service unavailable. Refresh to retry."); });
    return () => { active = false; };
  }, [attempt]);

  async function download(ontology: boolean) {
    if (!ontology && !selection?.publicationVersion) return;
    setBusy(true);
    setError("");
    try {
      await downloadExport(ontology ? null : selection!.publicationVersion, format);
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : "Download unavailable. Retry the download.");
    } finally {
      setBusy(false);
    }
  }

  return <section className="exports-view" aria-labelledby="exports-title">
    <div className="schedule-heading"><div><h1 id="exports-title">Exports</h1></div></div>
    {error && <p className="stale-notice" role="alert">{error}</p>}
    <div className="export-section">
      <h2>Accepted publication</h2>
      {!selection && !error && <p role="status">Loading publication</p>}
      {selection && (selection.publicationVersion ? <p className="export-version">{selection.publicationVersion}</p> : <p>No accepted publication yet</p>)}
      <div className="export-controls">
        <label>Format<select value={format} disabled={busy} onChange={event => setFormat(event.target.value as typeof format)}>
          <option value="json">JSON-LD</option><option value="csv">CSV</option><option value="turtle">RDF (Turtle)</option>
        </select></label>
        <button type="button" disabled={busy || !selection?.publicationVersion} onClick={() => void download(false)}><Download size={18} aria-hidden="true" />Download publication</button>
        <button type="button" title="Refresh publication" aria-label="Refresh publication" disabled={busy} onClick={() => setAttempt(value => value + 1)}><RefreshCw size={18} aria-hidden="true" /></button>
      </div>
    </div>
    <div className="export-section">
      <h2>OWL ontology</h2>
      <button type="button" disabled={busy} onClick={() => void download(true)}><Download size={18} aria-hidden="true" />Download ontology</button>
    </div>
    {busy && <p role="status">Preparing download</p>}
  </section>;
}