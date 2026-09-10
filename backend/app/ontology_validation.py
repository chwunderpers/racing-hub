from pathlib import Path

from pyshacl import validate
from rdflib import BNode, Graph, Literal, Namespace, OWL, RDF, RDFS, URIRef, XSD
from rdflib.term import Node


ONTOLOGY = Namespace("https://w3id.org/motorsport-hub/ontology/")
RESOURCE = "https://w3id.org/motorsport-hub/resource/"
SH = Namespace("http://www.w3.org/ns/shacl#")
SHAPES = Path(__file__).resolve().parents[2] / "ontology/shapes.ttl"
NEUTRAL_FIELDS = """
    identity version year status sourceIdentity sourceLanguage retrievedAt startDate endDate
    field locator rule preferred responseSha256 effectiveLocal translationVersion translatedAt
    translationReviewState number coverageState activity kind timeZone durationMinutes startLocal
    endLocal startOffset endOffset startZone endZone startInstant endInstant lengthKm
""".split()
HUMAN_FIELDS = [RDFS.label, RDFS.comment] + [ONTOLOGY[name] for name in (
    "evidence", "coverageReason", "translationMethod", "translationReviewer", "translationAuthorization",
)]


def rename_term(term: Node, renames: dict[URIRef, URIRef]) -> Node:
    return renames.get(term, term) if isinstance(term, URIRef) else term


def validate_graph(data: Graph, *, vocabulary: bool = False, renames: dict[URIRef, URIRef] | None = None) -> tuple[bool, Graph, str]:
    replacements = renames or {}
    shapes = Graph().parse(SHAPES, format="turtle") if not vocabulary else Graph()
    if replacements:
        migrated_shapes = Graph()
        for subject, predicate, value in shapes:
            if predicate == SH.select and isinstance(value, Literal):
                query = str(value)
                for old, new in replacements.items():
                    query = query.replace(old.n3(), new.n3())
                value = Literal(query)
            migrated_shapes.add((rename_term(subject, replacements), rename_term(predicate, replacements), rename_term(value, replacements)))
        shapes = migrated_shapes
    generic = BNode()
    shapes.add((generic, RDF.type, SH.NodeShape))
    for subject in set(data.subjects()):
        shapes.add((generic, SH.targetNode, subject))
        if isinstance(subject, URIRef):
            identity = BNode()
            shapes.add((identity, RDF.type, SH.NodeShape))
            shapes.add((identity, SH.targetNode, subject))
            shapes.add((identity, SH.pattern, Literal(
                "^https://w3id\\.org/motorsport-hub/" + ("ontology/" if vocabulary else "resource/")
            )))
    neutral = ", ".join(replacements.get(ONTOLOGY[name], ONTOLOGY[name]).n3() for name in NEUTRAL_FIELDS)
    human = ", ".join(replacements.get(predicate, predicate).n3() for predicate in HUMAN_FIELDS)
    constraints = [
        ("Human-readable literals require English tags; machine values must remain neutral.", f'''
            SELECT $this ?path ?value WHERE {{
                $this ?path ?value . FILTER(isLiteral(?value))
                FILTER (
                    (?path IN ({neutral}) && LANG(?value) != "") ||
                    (?path IN ({human}) && LCASE(LANG(?value)) != "en") ||
                    (?path NOT IN ({neutral}) &&
                        (DATATYPE(?value) IN (<{XSD.string}>, <{RDF.langString}>) || LANG(?value) != "") &&
                        LCASE(LANG(?value)) != "en")
                )
            }}'''),
        ("Canonical vocabulary and resource links must use the approved persistent authority.", f'''
            SELECT $this ?path ?value WHERE {{
                $this ?path ?value .
                FILTER (
                    !(STRSTARTS(STR(?path), "{ONTOLOGY}") ||
                      STRSTARTS(STR(?path), "{RDF}") || STRSTARTS(STR(?path), "{RDFS}") ||
                      STRSTARTS(STR(?path), "{OWL}")) ||
                    (isIRI(?value) && ?path != <{ONTOLOGY.sourceUrl}> &&
                      !(STRSTARTS(STR(?value), "{ONTOLOGY}") || STRSTARTS(STR(?value), "{RESOURCE}") ||
                        STRSTARTS(STR(?value), "{RDF}") || STRSTARTS(STR(?value), "{RDFS}") ||
                        STRSTARTS(STR(?value), "{OWL}") || STRSTARTS(STR(?value), "{XSD}"))) ||
                    ?path = <{OWL.imports}>
                )
            }}'''),
    ]
    for message, query in constraints:
        constraint = BNode()
        shapes.add((generic, SH.sparql, constraint))
        shapes.add((constraint, RDF.type, SH.SPARQLConstraint))
        shapes.add((constraint, SH.message, Literal(message, lang="en")))
        shapes.add((constraint, SH.select, Literal(query)))
    conforms, report, text = validate(data, shacl_graph=shapes, inference="none", do_owl_imports=False)
    if not isinstance(report, Graph):
        raise ValueError("SHACL did not produce a validation graph")
    return bool(conforms), report, str(text)