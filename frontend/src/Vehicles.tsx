import { useEffect, useState } from "react";
import { ArrowLeft, ArrowRight, ExternalLink, RefreshCw } from "lucide-react";
import { getVehicle, getVehicles } from "./api/client";
import type { components } from "./api/schema";

type Details = components["schemas"]["VehicleDetailsResponse"];
type Listing = components["schemas"]["VehicleListResponse"];
const labels: Record<string, string> = { manufacturer: "Manufacturer", model_name: "Model", category: "Category", generation: "Generation", variant: "Variant", engine: "Engine", drivetrain: "Drivetrain", dimensions: "Dimensions", base_weight: "Base weight", power: "Power" };

export function Vehicles({ identity, href, navigate }: { identity: string; href: (identity: string) => string; navigate: (identity: string) => void }) {
  const [result, setResult] = useState<{ identity: string; list?: Listing; details?: Details | null } | null>(null);
  const [failed, setFailed] = useState(false);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let active = true;
    setResult(null);
    setFailed(false);
    const request = identity ? getVehicle(identity).then(details => ({ identity, details })) : getVehicles().then(list => ({ identity, list }));
    request.then(value => { if (active) setResult(value); }).catch(() => { if (active) setFailed(true); });
    return () => { active = false; };
  }, [identity, attempt]);
  const current = result?.identity === identity ? result : null;
  const vehicle = current?.details?.vehicle;
  return <section className="vehicles-view" aria-labelledby="vehicles-title">
    <div className="schedule-heading"><div><h1 id="vehicles-title">{vehicle?.title || "Vehicles"}</h1></div></div>
    {identity && <a className="vehicle-back" href={href("")} onClick={event => { event.preventDefault(); navigate(""); }}><ArrowLeft size={18} aria-hidden="true" />All vehicles</a>}
    {failed ? <div className="failure-state" role="alert"><h2>Vehicle service unavailable</h2><button type="button" onClick={() => setAttempt(value => value + 1)}><RefreshCw size={18} aria-hidden="true" />Retry</button></div>
      : !current ? <p role="status">Loading vehicles</p>
      : identity && !vehicle ? <h2>Vehicle not found</h2>
      : current.list ? current.list.vehicles.length ? <ul className="vehicle-list">{current.list.vehicles.map(entry => <li key={entry.identity}><a href={href(entry.identity)} onClick={event => { event.preventDefault(); navigate(entry.identity); }}><span>{entry.title}</span><ArrowRight size={20} aria-hidden="true" /></a></li>)}</ul> : <h2>No vehicles published yet</h2>
      : vehicle && <>
        <p className="stale-notice">Competition Eligibility is not established by these descriptive specifications.</p>
        <dl className="vehicle-fields">{vehicle.fields.map(entry => <div className="vehicle-field" key={entry.field}>
          <dt>{labels[entry.field] || entry.field}</dt><dd><strong>{entry.value ?? "Unresolved"}</strong>
            {entry.conflict && <span className="vehicle-conflict">Conflicting source values</span>}
            <details><summary>Evidence ({entry.assertions.length})</summary>{entry.assertions.map(assertion => <div className="vehicle-evidence" key={assertion.iri}>
              <p><strong>{assertion.value}</strong> <span className="evidence-kind">{assertion.evidenceKind === "secondary" ? "Secondary Evidence" : "Authoritative source"}</span></p>
              <p>{assertion.applicability}</p>
              <a href={assertion.sourceUrl} target="_blank" rel="noreferrer">{assertion.publisher}<ExternalLink size={14} aria-hidden="true" /></a>
              <p>{assertion.anchor}</p><p>Retrieved <time dateTime={assertion.retrievedAt}>{new Date(assertion.retrievedAt).toISOString()}</time></p>
              <p className="vehicle-checksum">SHA-256: {assertion.checksum}</p>
            </div>)}</details>
          </dd>
        </div>)}</dl>
      </>}
  </section>;
}