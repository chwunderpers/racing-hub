import hashlib
import json
from urllib.parse import quote

from rdflib import Graph, Literal, Namespace, RDF, RDFS, URIRef, XSD

from app.vehicles import BasicVehicleSpecification


MOTORSPORT = Namespace("https://w3id.org/motorsport-hub/ontology/")
RESOURCE = "https://w3id.org/motorsport-hub/resource/"


def vehicle_iri(identity: str) -> URIRef:
    return URIRef(RESOURCE + "vehicle-model/" + quote(identity, safe=""))


def preferred_value(assertions: list[dict]) -> str | None:
    strongest = [assertion for assertion in assertions if assertion["evidenceKind"] == "authoritative"] or assertions
    values = {assertion["value"] for assertion in strongest}
    return next(iter(values)) if len(values) == 1 else None


def vehicle_graph(vehicle: BasicVehicleSpecification, version: str) -> Graph:
    graph = Graph()
    subject = vehicle_iri(vehicle.identity)
    graph.add((subject, RDF.type, MOTORSPORT.VehicleModel))
    names = [{"value": assertion.value, "evidenceKind": assertion.source.kind} for assertion in vehicle.fields["model_name"]]
    title = preferred_value(names) or "Vehicle Model " + vehicle.identity
    graph.add((subject, RDFS.label, Literal(title, lang="en")))
    graph.add((URIRef(RESOURCE + "publication/" + version), MOTORSPORT.includesVehicle, subject))
    for field, assertions in vehicle.fields.items():
        for assertion in assertions:
            digest = hashlib.sha256(json.dumps(assertion.model_dump(mode="json"), sort_keys=True).encode()).hexdigest()
            node = URIRef(str(subject) + "/assertion/" + field + "/" + digest)
            graph.add((subject, MOTORSPORT.provenance, node))
            graph.add((node, RDF.type, MOTORSPORT.VehicleSpecificationAssertion))
            graph.add((node, RDFS.label, Literal(title + " " + field + ": " + assertion.value, lang="en")))
            for predicate, value in (("vehicleField", field), ("evidenceKind", assertion.source.kind),
                                     ("checksum", assertion.source.sha256), ("sectionAnchor", assertion.source.anchor)):
                graph.add((node, MOTORSPORT[predicate], Literal(value)))
            for predicate, value in (("value", assertion.value), ("applicability", assertion.applicability),
                                     ("authority", assertion.source.publisher)):
                graph.add((node, MOTORSPORT[predicate], Literal(value, lang="en")))
            graph.add((node, MOTORSPORT.sourceUrl, URIRef(str(assertion.source.url))))
            graph.add((node, MOTORSPORT.retrievedAt, Literal(assertion.source.retrieved_at, datatype=XSD.dateTime)))
    return graph


def vehicle_projection(graph: Graph, subject: URIRef) -> dict:
    fields = {}
    for node in sorted(graph.objects(subject, MOTORSPORT.provenance), key=str):
        def scalar(predicate):
            value = graph.value(node, MOTORSPORT[predicate])
            return str(value) if value is not None else None
        field = scalar("vehicleField")
        fields.setdefault(field, []).append({
            "iri": str(node), "value": scalar("value"), "applicability": scalar("applicability"),
            "evidenceKind": scalar("evidenceKind"), "publisher": scalar("authority"),
            "sourceUrl": scalar("sourceUrl"), "retrievedAt": scalar("retrievedAt"),
            "checksum": scalar("checksum"), "anchor": scalar("sectionAnchor"),
        })
    return {"iri": str(subject), "title": str(graph.value(subject, RDFS.label)),
            "eligibilityEstablished": False,
            "fields": [{"field": field, "value": preferred_value(assertions),
                        "conflict": len({assertion["value"] for assertion in assertions}) > 1,
                        "assertions": assertions} for field, assertions in sorted(fields.items())]}