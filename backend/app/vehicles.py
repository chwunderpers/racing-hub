from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, HttpUrl, model_validator


VehicleField = Literal["manufacturer", "model_name", "category", "generation", "variant",
                       "engine", "drivetrain", "dimensions", "base_weight", "power"]


class VehicleEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, str_min_length=1)
    url: HttpUrl
    publisher: str = Field(max_length=200)
    kind: Literal["authoritative", "secondary"]
    retrieved_at: AwareDatetime
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    anchor: str = Field(max_length=500)
    language: Literal["en"]

    @model_validator(mode="after")
    def source_policy(self) -> "VehicleEvidence":
        if self.url.scheme != "https" or self.url.username or self.url.password:
            raise ValueError("Vehicle evidence requires HTTPS without credentials")
        host = self.url.host or ""
        if any(host == domain or host.endswith("." + domain) for domain in ("wikipedia.org", "wikidata.org")) and self.kind != "secondary":
            raise ValueError("Wikipedia and Wikidata must be marked as Secondary Evidence")
        return self


class VehicleAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, str_min_length=1)
    value: str = Field(max_length=500)
    applicability: str = Field(max_length=1000)
    source: VehicleEvidence


class BasicVehicleSpecification(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, str_min_length=1)
    identity: str = Field(max_length=120, pattern=r"^[a-z0-9][a-z0-9:._-]*$")
    language: Literal["en"]
    fields: dict[VehicleField, list[VehicleAssertion]]

    @model_validator(mode="after")
    def required_description(self) -> "BasicVehicleSpecification":
        if not {"manufacturer", "model_name", "category"}.issubset(self.fields):
            raise ValueError("Vehicle requires manufacturer, canonical English model name and category")
        if any(not assertions or len(assertions) > 10 for assertions in self.fields.values()):
            raise ValueError("Each supplied vehicle field requires one to ten evidence assertions")
        return self


class VehicleAssertionResponse(BaseModel):
    iri: str
    value: str
    applicability: str
    evidenceKind: Literal["authoritative", "secondary"]
    publisher: str
    sourceUrl: str
    retrievedAt: str
    checksum: str
    anchor: str


class VehicleFieldResponse(BaseModel):
    field: VehicleField
    value: str | None
    conflict: bool
    assertions: list[VehicleAssertionResponse]


class VehicleSpecificationResponse(BaseModel):
    iri: str
    title: str
    eligibilityEstablished: Literal[False] = False
    fields: list[VehicleFieldResponse]


class VehicleDetailsResponse(BaseModel):
    publicationVersion: str
    vehicle: VehicleSpecificationResponse


class VehicleSummaryResponse(BaseModel):
    identity: str
    iri: str
    title: str


class VehicleListResponse(BaseModel):
    publicationVersion: str | None
    vehicles: list[VehicleSummaryResponse]