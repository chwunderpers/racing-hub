from urllib.parse import quote

from rdflib import Graph, Literal, Namespace, RDF, RDFS, URIRef, XSD

from app.regulations import CompetitionRegulations


MOTORSPORT = Namespace("https://w3id.org/motorsport-hub/ontology/")
RESOURCE = "https://w3id.org/motorsport-hub/resource/"
TOPICS = ("eligibility", "format", "scoring", "tyres", "pit-stops", "sporting", "technical")


def regulation_iri(kind: str, identity: str) -> URIRef:
    return URIRef(RESOURCE + kind + "/" + quote(identity, safe=""))


def regulation_graph(bundle: CompetitionRegulations, version: str) -> Graph:
    graph = Graph()
    scope = f"{bundle.competition_identity}:{bundle.season_year}"
    profile = regulation_iri("competition-profile", scope)
    graph.add((profile, RDF.type, MOTORSPORT.CompetitionProfile))
    graph.add((profile, RDFS.label, Literal(f"Formula One {bundle.season_year} Competition Profile", lang="en")))
    graph.add((profile, MOTORSPORT.competition, regulation_iri("competition", bundle.competition_identity)))
    graph.add((profile, MOTORSPORT.season, regulation_iri("season", "competition:" + scope)))
    graph.add((profile, MOTORSPORT.year, Literal(bundle.season_year, datatype=XSD.integer)))
    graph.add((regulation_iri("publication", version), MOTORSPORT.includesProfile, profile))
    documents = {entry.identity: entry for entry in bundle.documents}
    for document in bundle.documents:
        subject = regulation_iri("regulation-document", scope + ":" + document.identity)
        graph.add((subject, RDF.type, MOTORSPORT.RegulationDocument))
        graph.add((subject, RDFS.label, Literal(document.title, lang="en")))
        for field, value in (("version", document.version), ("sourceLanguage", document.source_language), ("checksum", document.sha256)):
            graph.add((subject, MOTORSPORT[field], Literal(value)))
        graph.add((subject, MOTORSPORT.authority, Literal(document.authority, lang="en")))
        graph.add((subject, MOTORSPORT.sourceUrl, URIRef(str(document.source_url))))
        graph.add((subject, MOTORSPORT.retrievedAt, Literal(document.retrieved_at, datatype=XSD.dateTime)))
        graph.add((subject, MOTORSPORT.issuedOn, Literal(document.issued_on, datatype=XSD.date)))
        for section in document.sections:
            graph.add((subject, MOTORSPORT.sectionAnchor, Literal(f"{section.anchor}; PDF page {section.page}")))
    for passage in bundle.passages:
        subject = regulation_iri("evidence-passage", scope + ":" + passage.identity)
        document = documents[passage.document_identity]
        document_iri = regulation_iri("regulation-document", scope + ":" + document.identity)
        page = next(section.page for section in document.sections if section.anchor == passage.anchor)
        graph.add((subject, RDF.type, MOTORSPORT.EnglishEvidencePassage))
        graph.add((subject, RDFS.label, Literal(document.title + " " + passage.anchor, lang="en")))
        graph.add((subject, MOTORSPORT.document, document_iri))
        graph.add((subject, MOTORSPORT.passageText, Literal(passage.text, lang="en")))
        graph.add((subject, MOTORSPORT.evidenceKind, Literal(passage.kind)))
        graph.add((subject, MOTORSPORT.sectionAnchor, Literal(passage.anchor)))
        graph.add((subject, MOTORSPORT.sourceUrl, URIRef(str(document.source_url).split("#")[0] + f"#page={page}")))
        graph.add((subject, MOTORSPORT.retrievedAt, Literal(document.retrieved_at, datatype=XSD.dateTime)))
        if passage.translation:
            translation = passage.translation
            graph.add((subject, MOTORSPORT.sourceLanguage, Literal(translation.source_language)))
            graph.add((subject, MOTORSPORT.translationMethod, Literal(translation.method, lang="en")))
            graph.add((subject, MOTORSPORT.translationVersion, Literal(translation.version)))
            graph.add((subject, MOTORSPORT.translatedAt, Literal(translation.translated_at, datatype=XSD.dateTime)))
    for provision in bundle.provisions:
        subject = regulation_iri("provision", scope + ":" + provision.identity)
        passage = regulation_iri("evidence-passage", scope + ":" + provision.passage_identity)
        graph.add((subject, RDF.type, MOTORSPORT.Provision))
        graph.add((subject, RDFS.label, Literal(provision.summary, lang="en")))
        graph.add((subject, MOTORSPORT.provenance, passage))
        graph.add((subject, MOTORSPORT.applicability, Literal(provision.applicability, lang="en")))
        graph.add((subject, MOTORSPORT.discretion, Literal(provision.discretion, lang="en")))
        if provision.effective_from:
            graph.add((subject, MOTORSPORT.effectiveFrom, Literal(provision.effective_from, datatype=XSD.date)))
        if provision.effective_until:
            graph.add((subject, MOTORSPORT.effectiveUntil, Literal(provision.effective_until, datatype=XSD.date)))
        for exception in provision.exceptions:
            graph.add((subject, MOTORSPORT.exception, Literal(exception, lang="en")))
        for target in provision.amends:
            graph.add((subject, MOTORSPORT.amends, regulation_iri("provision", scope + ":" + target)))
    entries = {entry.topic: entry for entry in bundle.profile}
    for topic in TOPICS:
        entry = entries.get(topic)
        subject = regulation_iri("profile-value", scope + ":" + topic)
        graph.add((profile, MOTORSPORT.profileValue, subject))
        graph.add((subject, RDF.type, MOTORSPORT.ProfileValue))
        graph.add((subject, RDFS.label, Literal(f"Formula One {bundle.season_year} {topic}", lang="en")))
        graph.add((subject, MOTORSPORT.topic, Literal(topic)))
        graph.add((subject, MOTORSPORT.knowledgeState, Literal(entry.state if entry else "unknown")))
        if entry:
            if entry.value:
                graph.add((subject, MOTORSPORT.normalizedValue, Literal(entry.value, lang="en")))
            for identity in entry.provision_ids:
                provision_iri = regulation_iri("provision", scope + ":" + identity)
                graph.add((subject, MOTORSPORT.provision, provision_iri))
                for passage in graph.objects(provision_iri, MOTORSPORT.provenance):
                    graph.add((subject, MOTORSPORT.provenance, passage))
                    graph.add((profile, MOTORSPORT.provenance, passage))
    return graph


def profile_projection(graph: Graph, subject: URIRef) -> list[dict]:
    def scalar(resource, predicate):
        value = graph.value(resource, predicate)
        return str(value) if value is not None else None

    profile = []
    for entry in sorted(graph.objects(subject, MOTORSPORT.profileValue), key=str):
        provisions = []
        for provision in sorted(graph.objects(entry, MOTORSPORT.provision), key=str):
            passage = graph.value(provision, MOTORSPORT.provenance)
            document = graph.value(passage, MOTORSPORT.document)
            provisions.append({
                "iri": str(provision), "summary": scalar(provision, RDFS.label),
                "applicability": scalar(provision, MOTORSPORT.applicability),
                "exceptions": sorted(str(value) for value in graph.objects(provision, MOTORSPORT.exception)),
                "discretion": scalar(provision, MOTORSPORT.discretion),
                "amends": sorted(str(value) for value in graph.objects(provision, MOTORSPORT.amends)),
                "effectiveFrom": scalar(provision, MOTORSPORT.effectiveFrom),
                "effectiveUntil": scalar(provision, MOTORSPORT.effectiveUntil),
                "evidence": {"iri": str(passage), "text": scalar(passage, MOTORSPORT.passageText),
                    "kind": scalar(passage, MOTORSPORT.evidenceKind), "anchor": scalar(passage, MOTORSPORT.sectionAnchor),
                    "sourceUrl": scalar(passage, MOTORSPORT.sourceUrl), "retrievedAt": scalar(passage, MOTORSPORT.retrievedAt),
                    "documentVersion": scalar(document, MOTORSPORT.version), "checksum": scalar(document, MOTORSPORT.checksum),
                    "issuedOn": scalar(document, MOTORSPORT.issuedOn),
                    "sourceLanguage": scalar(document, MOTORSPORT.sourceLanguage),
                    "translationMethod": scalar(passage, MOTORSPORT.translationMethod),
                    "translationVersion": scalar(passage, MOTORSPORT.translationVersion)},
            })
        profile.append({"iri": str(entry), "topic": scalar(entry, MOTORSPORT.topic),
            "state": scalar(entry, MOTORSPORT.knowledgeState), "value": scalar(entry, MOTORSPORT.normalizedValue), "provisions": provisions})
    return profile