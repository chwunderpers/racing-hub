import { useEffect, useState } from "react";
import { RotateCcw } from "lucide-react";
import { getCapabilities } from "./api/client";
import type { components } from "./api/schema";

type Contribution = components["schemas"]["CapabilityContribution"];

export function CapabilityEntries({ contributions }: { contributions: Contribution[] }) {
  if (!contributions.length) return null;
  return <section className="capability-list" aria-label="Synthetic contributions">
    {contributions.map(entry => <article className="capability-entry" key={`${entry.id}:${entry.subjectIri}`}>
      <h3>{entry.title}</h3>
      <p className="capability-kind">Synthetic data / Not sporting evidence</p>
      <p>{entry.text}</p>
      <details><summary>Canonical identity</summary><p className="publication-version">{entry.subjectIri}</p></details>
    </article>)}
  </section>;
}

export function MeetingCapabilities({ identity, publicationVersion }: { identity: string; publicationVersion: string }) {
  const [contributions, setContributions] = useState<Contribution[]>([]);
  const [error, setError] = useState(false);
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let active = true;
    setContributions([]);
    setError(false);
    const subjectIri = `https://w3id.org/motorsport-hub/resource/meeting/${encodeURIComponent(identity.replace(/^meeting:/, ""))}`;
    getCapabilities(subjectIri).then(result => {
      if (!active) return;
      if (result.publicationVersion !== publicationVersion) throw new Error("Publication changed");
      setContributions(result.contributions || []);
    }).catch(() => { if (active) setError(true); });
    return () => { active = false; };
  }, [identity, publicationVersion, retry]);
  if (error) return <div className="capability-error" role="status">Optional data unavailable
    <button className="assistant-icon" type="button" aria-label="Retry optional data" title="Retry optional data" onClick={() => setRetry(value => value + 1)}><RotateCcw size={18} /></button>
  </div>;
  return <CapabilityEntries contributions={contributions} />;
}