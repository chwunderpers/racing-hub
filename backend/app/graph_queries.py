import re
from dataclasses import dataclass

from rdflib import RDF, RDFS, URIRef
from rdflib.plugins.sparql import prepareQuery
from rdflib.plugins.sparql.parserutils import CompValue


ONTOLOGY = "https://w3id.org/motorsport-hub/ontology/"
RESOURCE = "https://w3id.org/motorsport-hub/resource/"
PUBLIC_PREDICATES = {RDF.type, RDFS.label} | {
    URIRef(ONTOLOGY + name) for name in (
        "circuit", "competition", "season", "meeting", "round", "session", "venue", "layout",
        "startDate", "endDate", "status", "year", "number", "kind", "lengthKm", "timeZone",
        "sourceUrl", "retrievedAt", "provenance", "includesMeeting", "version",
        "subject", "field", "value", "preferred", "effectiveLocal", "coverageState",
        "includesProfile", "profileValue", "topic", "knowledgeState", "normalizedValue", "provision",
        "amends", "effectiveFrom", "effectiveUntil", "passageText", "document", "evidenceKind",
        "sectionAnchor", "sourceLanguage", "authority", "checksum", "issuedOn", "translationMethod",
        "translationVersion", "translatedAt", "applicability", "discretion", "exception",
    )
}


@dataclass(frozen=True)
class ValidatedGraphQuery:
    query: str
    form: str
    limit: int


class GraphQueryPolicy:
    def __init__(self, version: str):
        if not re.fullmatch(r"[0-9a-f]{64}", version):
            raise ValueError("A published version is required")
        self.graph = URIRef("https://w3id.org/motorsport-hub/graph/publication/" + version)

    def validate(self, query: str) -> ValidatedGraphQuery:
        if not query or len(query.encode("utf-8")) > 12000:
            raise ValueError("Graph query exceeds input bounds")
        try:
            algebra = prepareQuery(query).algebra
        except Exception:
            raise ValueError("Invalid read-only SPARQL query") from None
        forms = {"SelectQuery": "SELECT", "AskQuery": "ASK", "ConstructQuery": "CONSTRUCT", "DescribeQuery": "DESCRIBE"}
        if algebra.name not in forms:
            raise ValueError("Unsupported query form")
        dataset = algebra["datasetClause"]
        if not dataset or len(dataset) != 1 or dict(dataset[0]).get("default") != self.graph:
            raise ValueError("Query must use only the current publication FROM graph")
        form = forms[algebra.name]
        root = algebra["p"]
        limit = int(root["length"]) if root.name == "Slice" and "length" in root else 0
        if form != "ASK" and not 1 <= limit <= 100:
            raise ValueError("Query requires LIMIT between 1 and 100")
        nodes = 0
        triples = 0
        matched_triples = set()
        allowed = set(forms) | {"Slice", "Project", "BGP", "Join", "LeftJoin", "Union", "Filter", "Distinct", "OrderBy", "OrderCondition", "RelationalExpression", "ConditionalAndExpression", "ConditionalOrExpression", "UnaryNot", "Builtin_BOUND", "Builtin_LANG", "Builtin_LANGMATCHES", "Builtin_STR", "TrueFilter", "DatasetClause"}

        def visit(value):
            nonlocal nodes, triples
            if isinstance(value, CompValue):
                nodes += 1
                if nodes > 100 or value.name not in allowed:
                    raise ValueError("Query operation is not permitted")
                if form == "CONSTRUCT" and value.name in {"Union", "LeftJoin"}:
                    raise ValueError("Construct requires a conjunctive matched graph pattern")
                if value.name == "Slice" and int(dict(value).get("start", 0)) > 1000:
                    raise ValueError("Query offset exceeds bounds")
                for key, child in value.items():
                    if key in {"triples", "template"}:
                        if key == "triples":
                            matched_triples.update(child)
                        triples += len(child)
                        if triples > 30:
                            raise ValueError("Query complexity exceeds bounds")
                        for subject, predicate, target in child:
                            if predicate not in PUBLIC_PREDICATES:
                                raise ValueError("Only fixed public predicates are permitted")
                    if key != "_vars":
                        visit(child)
            elif isinstance(value, (list, tuple)):
                for child in value:
                    visit(child)

        visit(algebra)
        if form == "CONSTRUCT":
            if len(algebra["template"]) * limit > 300:
                raise ValueError("Construct exceeds triple budget")
            if not set(algebra["template"]).issubset(matched_triples):
                raise ValueError("Construct may only project matched triples")
        if form == "DESCRIBE" and any(not isinstance(term, URIRef) or not str(term).startswith(RESOURCE) for term in algebra["PV"]):
            raise ValueError("Describe requires explicit canonical resource IRIs")
        return ValidatedGraphQuery(query, form, limit or 1)


def shared_circuits_query(version: str) -> str:
        graph = GraphQueryPolicy(version).graph
        return f"""PREFIX msh: <{ONTOLOGY}>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT DISTINCT ?circuit ?circuitName ?competitionA ?nameA ?competitionB ?nameB ?sourceA ?retrievedA ?sourceB ?retrievedB
FROM <{graph}>
WHERE {{
    ?meetingA a msh:Meeting; msh:circuit ?circuit; msh:competition ?competitionA; msh:provenance ?provenanceA .
    ?meetingB a msh:Meeting; msh:circuit ?circuit; msh:competition ?competitionB; msh:provenance ?provenanceB .
    ?circuit rdfs:label ?circuitName .
    ?competitionA rdfs:label ?nameA . ?competitionB rdfs:label ?nameB .
    ?provenanceA msh:sourceUrl ?sourceA; msh:retrievedAt ?retrievedA .
    ?provenanceB msh:sourceUrl ?sourceB; msh:retrievedAt ?retrievedB .
    FILTER (STR(?competitionA) < STR(?competitionB))
}}
ORDER BY ?circuit ?competitionA ?competitionB
LIMIT 100"""