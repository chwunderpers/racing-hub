from datetime import date
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, HttpUrl, model_validator


Topic = Literal["eligibility", "format", "scoring", "tyres", "pit-stops", "sporting", "technical"]


class RegulationModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, str_min_length=1)


class SectionAnchor(RegulationModel):
    anchor: str
    page: int = Field(ge=1)


class RegulationDocument(RegulationModel):
    identity: str
    title: str
    version: str
    season_year: int = Field(ge=2026, le=2026)
    authority: Literal["FIA", "DMSB", "VLN"]
    source_url: HttpUrl
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    retrieved_at: AwareDatetime
    issued_on: date | None
    source_language: str = Field(pattern=r"^[a-z]{2,3}$")
    sections: list[SectionAnchor] = Field(min_length=1)

    @model_validator(mode="after")
    def official_document(self) -> "RegulationDocument":
        hosts = {"FIA": ("www.fia.com", "fia.com"),
             "DMSB": ("www.dmsb.de", "dmsb.de", "www.nuerburgring-langstrecken-serie.de", "nuerburgring-langstrecken-serie.de", "teilnehmer.vln.de"),
             "VLN": ("www.nuerburgring-langstrecken-serie.de", "nuerburgring-langstrecken-serie.de", "teilnehmer.vln.de")}
        if self.source_url.scheme != "https" or self.source_url.host not in hosts[self.authority]:
            raise ValueError("Regulation documents require an official HTTPS host for their authority")
        if len({section.anchor for section in self.sections}) != len(self.sections):
            raise ValueError("Duplicate document section anchor")
        return self


class RegulationTranslation(RegulationModel):
    source_language: str = Field(pattern=r"^[a-z]{2,3}$")
    method: str
    version: str
    translated_at: AwareDatetime
    source_url: HttpUrl
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_anchor: str
    review_state: Literal["pending", "accepted"]
    reviewer: str | None = None
    reviewed_at: AwareDatetime | None = None
    authorization: str | None = None

    @model_validator(mode="after")
    def review_provenance(self) -> "RegulationTranslation":
        if self.source_language == "en":
            raise ValueError("A translation must identify its non-English source language")
        if self.review_state == "accepted" and not (self.reviewer and self.reviewed_at and self.authorization):
            raise ValueError("Accepted translation requires reviewer, time and authorization")
        return self


class EnglishEvidencePassage(RegulationModel):
    identity: str
    document_identity: str
    anchor: str
    language: Literal["en"]
    text: str = Field(max_length=2000)
    kind: Literal["quotation", "paraphrase", "translation"]
    translation: RegulationTranslation | None = None


class Provision(RegulationModel):
    identity: str
    passage_identity: str
    topic: Topic
    summary: str
    applicability: str
    exceptions: list[str]
    discretion: str
    amends: list[str]
    effective_from: date | None
    effective_until: date | None = None

    @model_validator(mode="after")
    def valid_period(self) -> "Provision":
        if self.effective_until and self.effective_from and self.effective_until < self.effective_from:
            raise ValueError("Provision applicability period is reversed")
        return self


class ProfileValue(RegulationModel):
    topic: Topic
    state: Literal["known", "unknown", "not-published", "not-applicable"]
    value: str | None = None
    provision_ids: list[str]

    @model_validator(mode="after")
    def evidence_required(self) -> "ProfileValue":
        if self.state == "known" and (not self.value or not self.provision_ids):
            raise ValueError("Known profile values require a value and governing Provisions")
        if self.state != "known" and self.value is not None:
            raise ValueError("Unknown or unavailable profile states cannot assert a value")
        if self.state in ("not-published", "not-applicable") and not self.provision_ids:
            raise ValueError("Not-published and not-applicable claims require supporting Provisions")
        return self


class CompetitionRegulations(RegulationModel):
    competition_identity: Literal["formula-one", "nls"]
    season_year: int = Field(ge=2026, le=2026)
    documents: list[RegulationDocument] = Field(min_length=1, max_length=20)
    passages: list[EnglishEvidencePassage] = Field(min_length=1, max_length=100)
    provisions: list[Provision] = Field(min_length=1, max_length=100)
    profile: list[ProfileValue] = Field(min_length=1, max_length=7)

    @model_validator(mode="after")
    def linked_evidence(self) -> "CompetitionRegulations":
        authorities = ("FIA",) if self.competition_identity == "formula-one" else ("DMSB", "VLN")
        if any(document.authority not in authorities or document.season_year != self.season_year for document in self.documents):
            raise ValueError("Regulation document authority and season must match its Competition scope")
        for entries in (self.documents, self.passages, self.provisions):
            if len({entry.identity for entry in entries}) != len(entries):
                raise ValueError("Duplicate regulation resource identity")
        documents = {entry.identity: entry for entry in self.documents}
        passages = {entry.identity: entry for entry in self.passages}
        provisions = {entry.identity: entry for entry in self.provisions}
        if len({entry.topic for entry in self.profile}) != len(self.profile):
            raise ValueError("Duplicate Competition Profile topic")
        for passage in self.passages:
            document = documents.get(passage.document_identity)
            if document is None or passage.anchor not in {section.anchor for section in document.sections}:
                raise ValueError("Evidence must reference an inventoried document section")
            translation = passage.translation
            if document.source_language != "en":
                if passage.kind != "translation" or translation is None:
                    raise ValueError("Non-English evidence requires a Translation Record")
                if (translation.source_language, translation.source_url, translation.source_sha256, translation.source_anchor) != (
                    document.source_language, document.source_url, document.sha256, passage.anchor,
                ):
                    raise ValueError("Translation provenance must match its document and section")
            elif translation is not None or passage.kind == "translation":
                raise ValueError("English source evidence must not be labelled as a translation")
        for provision in self.provisions:
            if provision.passage_identity not in passages or any(identity not in provisions or identity == provision.identity for identity in provision.amends):
                raise ValueError("Provision evidence or amendment target is unresolved")
        def visit(identity: str, path: set[str]) -> None:
            if identity in path:
                raise ValueError("Cyclic provision amendments")
            for target in provisions[identity].amends:
                visit(target, path | {identity})

        for provision in self.provisions:
            visit(provision.identity, set())
        for entry in self.profile:
            if any(identity not in provisions or provisions[identity].topic != entry.topic for identity in entry.provision_ids):
                raise ValueError("Profile value requires resolved same-topic Provisions")
        return self