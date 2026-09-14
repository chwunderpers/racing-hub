import csv
import io
from pathlib import Path
from typing import Literal as FormatLiteral

from pydantic import BaseModel
from rdflib import Graph, Literal, URIRef

from app.graph_queries import PUBLIC_PREDICATES
from app.stores import GraphDbProjection


ExportFormat = FormatLiteral["json", "csv", "turtle"]
EXPORT_PREDICATES = PUBLIC_PREDICATES | {
    URIRef("https://w3id.org/motorsport-hub/ontology/" + name)
    for name in (
        "includesVehicle", "vehicleField", "includesSeason", "fieldAssertion",
        "activity", "coverageReason", "durationMinutes", "locator", "responseSha256",
        "startLocal", "endLocal", "startOffset", "endOffset", "startZone", "endZone",
        "startInstant", "endInstant",
    )
}
EXPORT_TYPES = {"json": ("application/ld+json", "json"), "csv": ("text/csv", "csv"), "turtle": ("text/turtle", "ttl")}


class ExportSelection(BaseModel):
    publicationVersion: str | None


def ontology_bytes() -> bytes:
    base = Path(__file__).resolve()
    packaged = base.parents[1] / "ontology/motorsport.ttl"
    source = packaged if packaged.is_file() else base.parents[2] / "ontology/motorsport.ttl"
    return source.read_bytes()


def publication_graph(store, version: str) -> Graph:
    if store.current_publication_version() != version:
        raise LookupError("Requested publication is not current")
    snapshot = store.publication_envelope(version)
    graph = Graph()
    for subject, predicate, value in GraphDbProjection.build_graph(version, snapshot):
        if predicate in EXPORT_PREDICATES:
            if isinstance(value, Literal) and value.language not in (None, "en"):
                raise ValueError("Non-English export literal")
            graph.add((subject, predicate, value))
    if store.current_publication_version() != version:
        raise LookupError("Publication changed; refresh the export selection")
    return graph


def serialize_publication(graph: Graph, version: str, format: ExportFormat) -> str:
    if format != "csv":
        return graph.serialize(format="json-ld" if format == "json" else "turtle", auto_compact=False)
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["publicationVersion", "subject", "predicate", "object", "objectKind", "datatype", "language"])
    for subject, predicate, value in sorted(graph, key=lambda triple: tuple(term.n3() for term in triple)):
        writer.writerow([
            version, subject.n3(), predicate.n3(), value.n3(),
            "literal" if isinstance(value, Literal) else "iri",
            str(value.datatype or "") if isinstance(value, Literal) else "",
            (value.language or "") if isinstance(value, Literal) else "",
        ])
    return output.getvalue()