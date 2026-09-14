import json
from urllib.parse import urlsplit

import yaml
from markdown_it import MarkdownIt
from pydantic import BaseModel, ConfigDict, Field
from rdflib import Graph, Literal, Namespace, RDF, RDFS, URIRef


RESOURCE = "https://w3id.org/motorsport-hub/resource/"
ONTOLOGY = Namespace("https://w3id.org/motorsport-hub/ontology/")


class DocumentMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")
    iri: str
    rdfTypes: list[str] = Field(min_length=1)
    title: str = Field(min_length=1)
    language: str
    publicationVersion: str = Field(pattern=r"^[0-9a-f]{64}$")


def project_markdown(documents: list[str], graph: Graph, version: str) -> list[dict]:
    records = []
    seen = set()
    for markdown in documents:
        parts = markdown.split("---\n", 2)
        if len(parts) != 3 or parts[0]:
            raise ValueError("English Markdown requires YAML front matter")
        metadata = DocumentMetadata.model_validate(yaml.safe_load(parts[1]))
        subject = URIRef(metadata.iri)
        if metadata.iri in seen:
            raise ValueError("Duplicate documentation IRI")
        seen.add(metadata.iri)
        if not metadata.iri.startswith(RESOURCE) or not list(graph.predicate_objects(subject)):
            raise ValueError("Broken documentation IRI")
        if metadata.language != "en" or metadata.publicationVersion != version:
            raise ValueError("Documentation language or publication mismatch")
        if sorted(metadata.rdfTypes) != sorted(str(value) for value in graph.objects(subject, RDF.type)):
            raise ValueError("Documentation RDF type mismatch")
        labels = list(graph.objects(subject, RDFS.label))
        if labels and metadata.title not in [str(label) for label in labels if label.language == "en"]:
            raise ValueError("Documentation English label mismatch")
        for token in MarkdownIt().parse(parts[2]):
            for child in token.children or []:
                reference = child.attrGet("href")
                if reference and reference.startswith(RESOURCE) and not list(graph.predicate_objects(URIRef(reference))):
                    raise ValueError("Broken Markdown resource reference")
        records.append({**metadata.model_dump(), "markdown": markdown})
    return sorted(records, key=lambda record: record["iri"])


def canonical_documents(graph: Graph, version: str) -> list[dict]:
    documents = []
    sources_by_iri = {}
    for subject in sorted(set(graph.subjects(RDF.type, None)), key=str):
        types = sorted(str(value) for value in graph.objects(subject, RDF.type))
        labels = sorted(str(value) for value in graph.objects(subject, RDFS.label) if value.language == "en")
        kind = types[0].rsplit("/", 1)[-1]
        title = labels[0] if labels else kind + " " + str(subject).rsplit("/", 1)[-1]
        metadata = DocumentMetadata(iri=str(subject), rdfTypes=types, title=title, language="en", publicationVersion=version)
        lines = ["# " + title, "", "RDF type: " + ", ".join(types), ""]
        sources = set()
        provenance = set(graph.objects(subject, ONTOLOGY.provenance)) | {subject}
        if kind in {"Competition", "Season", "Circuit", "Venue", "Layout", "Round"}:
            related = set(graph.subjects(None, subject)) | set(graph.objects(subject, ONTOLOGY.meeting))
            for resource in related:
                provenance.update(graph.objects(resource, ONTOLOGY.provenance))
        for assertion in provenance:
            for url in graph.objects(assertion, ONTOLOGY.sourceUrl):
                if urlsplit(str(url)).scheme in {"https", "http"}:
                    retrieved = next(graph.objects(assertion, ONTOLOGY.retrievedAt), None)
                    sources.add((str(url), str(retrieved) if retrieved else None))
        excluded = {"evidence", "translationReviewer", "translationAuthorization", "rule", "responseSha256", "sourceIdentity"}
        for predicate, value in sorted(graph.predicate_objects(subject), key=lambda pair: (str(pair[0]), str(pair[1]))):
            field = str(predicate).rsplit("/", 1)[-1].rsplit("#", 1)[-1]
            if predicate in {RDF.type, RDFS.label} or field in excluded:
                continue
            if isinstance(value, Literal) and value.language not in {None, "en"}:
                raise ValueError("Non-English canonical documentation literal")
            if isinstance(value, URIRef) and str(value).startswith(RESOURCE) and not list(graph.predicate_objects(value)):
                raise ValueError("Broken canonical resource reference")
            lines.append("- " + field + ": " + json.dumps(str(value), ensure_ascii=True))
        sources_by_iri[str(subject)] = [{"url": url, "retrievedAt": retrieved} for url, retrieved in sorted(sources, key=lambda item: (item[0], item[1] or ""))]
        documents.append("---\n" + yaml.safe_dump(metadata.model_dump(), sort_keys=True, allow_unicode=False) + "---\n" + "\n".join(lines) + "\n")
    records = [{**record, "sources": sources_by_iri[record["iri"]]} for record in project_markdown(documents, graph, version)]
    from app.regulation_projection import profile_projection
    from app.vehicle_projection import vehicle_projection
    for record in records:
        if str(ONTOLOGY.CompetitionProfile) in record["rdfTypes"]:
            record["regulationProfile"] = profile_projection(graph, URIRef(record["iri"]))
        if str(ONTOLOGY.VehicleModel) in record["rdfTypes"]:
            record["vehicleSpecification"] = vehicle_projection(graph, URIRef(record["iri"]))
    return records