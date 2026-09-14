import json
from pathlib import Path
from typing import Literal
from urllib.parse import quote, unquote

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class CapabilityQuery(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    subjectIri: str = Field(max_length=500, pattern=r"^https://w3id\.org/motorsport-hub/resource/(meeting|session)/[^/]+$")

    @field_validator("subjectIri")
    @classmethod
    def canonical_identity(cls, value: str) -> str:
        identity = value.rsplit("/", 1)[-1]
        if quote(unquote(identity, errors="strict"), safe="") != identity:
            raise ValueError("Subject must use exact canonical IRI encoding")
        return value


class CapabilityRecord(CapabilityQuery):
    text: str = Field(min_length=1, max_length=1000)


class CapabilityDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str = Field(pattern=r"^[a-z][a-z0-9-]{0,49}$")
    title: str = Field(min_length=1, max_length=100)
    records: list[CapabilityRecord] = Field(min_length=1, max_length=20)

    @model_validator(mode="after")
    def unique_subjects(self):
        if len({record.subjectIri for record in self.records}) != len(self.records):
            raise ValueError("Duplicate capability subject")
        return self


class CapabilityContribution(CapabilityRecord):
    id: str
    title: str
    kind: Literal["synthetic"] = "synthetic"


class CapabilityResponse(BaseModel):
    publicationVersion: str | None
    contributions: list[CapabilityContribution]


class CapabilityRegistry:
    def __init__(self):
        self._definitions: dict[str, CapabilityDefinition] = {}

    @property
    def available(self) -> bool:
        return bool(self._definitions)

    def register(self, definition: dict) -> None:
        parsed = CapabilityDefinition.model_validate(definition).model_copy(deep=True)
        if parsed.id in self._definitions or len(self._definitions) >= 10:
            raise ValueError("Duplicate capability or registration limit exceeded")
        self._definitions[parsed.id] = parsed

    def remove(self, identity: str) -> None:
        self._definitions.pop(identity, None)

    def read(self, subject_iri: str) -> list[CapabilityContribution]:
        CapabilityQuery(subjectIri=subject_iri)
        return [
            CapabilityContribution(id=definition.id, title=definition.title, **record.model_dump())
            for definition in self._definitions.values()
            for record in definition.records
            if record.subjectIri == subject_iri
        ]


def load_capabilities(directory: Path | None = None) -> CapabilityRegistry:
    registry = CapabilityRegistry()
    directory = directory if directory is not None else Path(__file__).with_name("optional_capabilities")
    paths = sorted(directory.glob("*.json"))
    if len(paths) > 10:
        raise ValueError("Capability module limit exceeded")
    for path in paths:
        with path.open("rb") as source:
            body = source.read(100001)
        if len(body) > 100000:
            raise ValueError("Capability module size limit exceeded")
        registry.register(json.loads(body))
    return registry


def configured_capabilities() -> CapabilityRegistry:
    return load_capabilities()


def published_contributions(registry: CapabilityRegistry, store, version: str | None, request: CapabilityQuery) -> CapabilityResponse:
    document = store.lookup_document(request.subjectIri, version) if version else None
    kind = request.subjectIri.split("/resource/", 1)[1].split("/", 1)[0].title()
    if not document or "https://w3id.org/motorsport-hub/ontology/" + kind not in document["rdfTypes"]:
        raise LookupError("Published Meeting or Session not found")
    return CapabilityResponse(publicationVersion=version, contributions=registry.read(request.subjectIri))