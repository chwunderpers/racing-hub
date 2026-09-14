# Vehicle Source Inventory

Issue 13 source research and collection record, 2026-09-14. Sample scope: Porsche 911 GT3 R (992), BMW M4 GT3 EVO, Mercedes-AMG GT3. **The minimal inventory is now accepted and published for the local PoC under the operator's explicit delegation.** See [delegated closeout](vehicles.md#delegated-closeout). The initial research observations below are historical: their pending-review wording and no-publication statements describe the research stage, not the completed closeout. Optional technical notes were not ingested.

## Closeout Capture

The fresh official captures returned HTTP 200 with no redirects or compression.
Porsche's PDF hash was unchanged. BMW and AMG HTML hashes changed while the
inspected model passages remained supportive of the same sparse assertions.
The final [inventory](../examples/vehicle-inventory.json) and
[collection record](../reviews/requests/issue-13-collection.json) contain these
updated hashes and actual capture times:

- Porsche: `e73140237efcf3a470233fe6315eadd560c75ef3a88536789483e0d82a0d2df3` (130154 bytes).
- BMW: `c4dfd9e1bbfaf8f21587331ffe8d6268c547508e9e8583e595e1f6cc99e21b43` (134841 bytes).
- AMG: `9691e49c175273e6c3c815da0eead5d4fc98cc115dbc7255bae810043dfb9d2e` (259254 bytes).

Repeated live collection still detected raw-byte drift. Rather than disable that
gate, the PoC execution replayed the retained official responses through the
unchanged collector validation and preserved their original observation times.
The raw captures are retained privately, unlike the initial research stage.
This demonstrates a captured-source handoff, not stable repeated live collection.
Source classification and wording were accepted by GitHub Copilot acting under
Chris's scoped delegation; no claim that Chris inspected each field is made.

GT3 below is a manufacturer's vehicle-category description only. No competition eligibility, homologation, class mapping, season applicability, or Balance of Performance inference is made. Omitted fields mean not established for this sample, not that the vehicle lacks the feature.

## Three Source Targets

| Sample | Exact official URL | Publisher | Research result |
| --- | --- | --- | --- |
| Porsche 911 GT3 R (992) | https://newsroom.porsche.com/dam/jcr:3b5e8287-01fb-481f-9d5c-2add88364f30/250808e_Technical%20Data%20911%20GT3%20R26.pdf | Dr. Ing. h.c. F. Porsche Aktiengesellschaft | HTTP 200; five-page English PDF parsed in memory; title, generation, category and Model Year 2026 scope verified. |
| BMW M4 GT3 EVO | https://www.bmw-m.com/en/fastlane/motorsport/race-cars/bmw-m4-gt3-evo.html | BMW M GmbH / BMW M Motorsport | HTTP 200; English EVO identity, revision context and GT3 category verified in actual downloaded HTML. |
| Mercedes-AMG GT3 | https://www.mercedes-amg.com/en/mercedes-amg-gt3 | Mercedes-AMG GmbH | HTTP 200; English identity, racing context and 2019-successor scope verified in actual downloaded HTML. |

For all three: final response URL exactly equalled the requested URL, no `Location` header, zero redirects followed, and identity content encoding. The probe reports an absent `Content-Encoding` header as `identity`; it does not distinguish absence from an explicit identity value. Requests used `Accept-Encoding: identity`, redirects disabled, a 20-second HTTP timeout and a 10,000,000-byte body cap. HTTPS certificate verification was enabled. Only these three exact official hosts were allowed. No credentials or browser session were supplied.

| Source | Actual Content-Type | Raw bytes | Retrieval completed (UTC) | SHA-256 of exact raw uncompressed response body |
| --- | --- | ---: | --- | --- |
| Porsche | `application/pdf;charset=UTF-8` | 130154 | `2026-09-14T11:57:09.423165+00:00` | `e73140237efcf3a470233fe6315eadd560c75ef3a88536789483e0d82a0d2df3` |
| BMW | `text/html;charset=utf-8` | 134840 | `2026-09-14T11:57:09.913083+00:00` | `39a0ff41c8fadebdcb5236ba590df3821e28e65ff983a96a5c21689216ad13c2` |
| AMG | `text/html; charset=utf-8` | 259254 | `2026-09-14T11:57:10.371387+00:00` | `0229d321aa41c76a267449e2ac11dabb9618a78c02931948ff292e7e3e1c3037` |

Hashes cover concatenated `httpx.Response.iter_raw()` chunks before UTF-8 decoding, HTML parsing or PDF extraction, with no newline normalization. The timestamp was captured with `datetime.now(UTC)` after each complete body read. PDF parsing used `pypdf.PdfReader(io.BytesIO(body))`; HTML parsing excluded script/style/noscript data and normalized whitespace only for passage inspection. These are verified research downloads, not an ingestion CLI run. Raw bodies were held in memory only; the repository retains the metadata and short evidence passages, not source snapshots. Later retrieval may differ, especially for dynamic HTML.

## Porsche: Gap Resolved

The direct PDF above supplies the evidence; the previously consent-blocked launch article is not used. Actual page 1, printed `1 of 5`, carries `Press Release 8 August 2025`, `Technical Data`, and the title:

> Porsche 911 GT3 R (Generation 992) Model Year 2026

Under `Concept`, the actual English passage is:

> Single-seater customer race car; homologated for the FIA GT3 category; homologation basis: Porsche 911 GT3 (992 series)

The publisher is named in the page footer. The extracted heading splits `Technical` as `T echnical`; the anchor normalizes this extraction artifact. `pypdf` emitted incorrect object-offset warnings but recovered all five pages and readable page-1 title/Concept text. No OCR, translation, filename inference or search-snippet evidence was used.

| Field | Pending English value | Verified anchor | Applicability |
| --- | --- | --- | --- |
| manufacturer | Porsche | Page 1 title and publisher footer | Manufacturer brand of this Model Year 2026 car. |
| model_name | 911 GT3 R | Page 1 title | Racing model, not the road-going homologation-basis car or GT3 R rennsport. |
| category | GT3 racing car | Page 1, `Concept` | Descriptive normalization only; no homologation-validity or eligibility finding is persisted. |
| generation | 992 | Page 1 title, `(Generation 992)` | Explicit generation of the Model Year 2026 subject; not inferred from the road-car basis. |

Every Porsche assertion is scoped to Model Year 2026. Revision-specific specifications are not applied to the original 2023 car or all 992 cars. Variant, engine, drivetrain, dimensions, base weight and power remain absent from the pending inventory even though the PDF includes technical details.

## BMW M4 GT3 EVO

Source: [BMW M4 GT3 EVO official page](https://www.bmw-m.com/en/fastlane/motorsport/race-cars/bmw-m4-gt3-evo.html). All anchors below are observed heading/text locators, not invented HTML fragment IDs.

The raw HTML body verified `THE GT FLAGSHIP.` followed by `BMW M4 GT3 EVO` and the English description `the latest evolutionary stage of BMW M Motorsport GT race car`, explicitly competing since the 2025 season. The following paragraph distinguishes the earlier `BMW M4 GT3 model from 2022 to 2024`. Under `5 POWERFUL FACTS:`, the first item reads `GT3 racing car with the new BMW M design`. These passages support all four supplied fields. Optional technical fields below are earlier research notes and are not included in the minimal inventory.

| Field | Proposed English value | Source anchor | Applicability / uncertainty |
| --- | --- | --- | --- |
| manufacturer | BMW | `THE GT FLAGSHIP.`; introductory `BMW M4 GT3 EVO` description | Manufacturer brand, not an assertion about a separate legal manufacturing entity. |
| model_name | BMW M4 GT3 EVO | `THE GT FLAGSHIP.`; introductory model description | Explicit EVO identity; do not shorten to the earlier BMW M4 GT3. |
| category | GT3 racing car | `5 POWERFUL FACTS:`; first item | Explicit vehicle category, not series eligibility. |
| variant | EVO | Introductory description of the evolutionary stage and first season in 2025 | EVO is explicit in the model name. The date distinguishes the revision; it is not a competition-validity interval. |
| engine (optional) | P58 3.0-litre straight-six, M TwinPower Turbo; 2,993 cm3 | `TECHNICAL DATA OF THE BMW M4 GT3 EVO.` > `Engine.`; Type, Technology, Capacity | Explicitly EVO-labelled technical table. Retain both marketed displacement and stated capacity. |
| dimensions (optional) | Length 5,020 mm; width 2,040 mm; height 1,308 mm (variable); wheelbase 2,917 mm | `TECHNICAL DATA OF THE BMW M4 GT3 EVO.` > `Dimensions.` | Keep the variable-height qualifier. Width measurement basis is not specified in the extracted table. |

Recommended minimal fields: manufacturer, model_name, category, variant. Engine and dimensions are supported optional additions, not necessary for the sparse sample. Leave generation, drivetrain and base_weight absent. Omit power: the table says up to 590 hp and nearby prose states output varies with regulations; no event-specific or fixed output is established.

Content limitations: the page also discusses the older M4 GT3, M4 GT4 EVO, M4 CS and a LEGO model. Restrict extraction to the introductory EVO identity, category item and EVO technical table. Some embedded media require consent, but the cited English text was readable without interacting with that media. The index-linked `/en_PM/fastlane/motorsport/race-cars/bmw-m4-gt3-evo.html` path also produced readable content; the `/en/` target above was independently fetched successfully.

## Mercedes-AMG GT3

Source: [Mercedes-AMG GT3 official page](https://www.mercedes-amg.com/en/mercedes-amg-gt3). Anchors are observed heading/text locators.

The raw HTML verified `The Mercedes-AMG GT3` and the introduction: `The 2015 introduced Mercedes-AMG GT3 immediately set new benchmarks. Its successor, unveiled in 2019, defines a new level of user-friendliness and economic efficiency.` The opening bullet states `Sequential AMG 6-gear race car transmission`; `Highlights` names the Mercedes-AMG GT3 and its customer sports series context. The pending category `GT3 racing car` is an explicitly disclosed descriptive normalization of this model name plus racing context, not a verbatim category phrase or a regulatory conclusion. Human wording review remains required. Optional engine/gearbox notes below are excluded from the minimal inventory.

| Field | Proposed English value | Source anchor | Applicability / uncertainty |
| --- | --- | --- | --- |
| manufacturer | Mercedes-AMG | `THE MERCEDES-AMG GT3`; introductory model description | Manufacturer brand; publisher is Mercedes-AMG GmbH. |
| model_name | Mercedes-AMG GT3 | `THE MERCEDES-AMG GT3` | Retain the published name; do not append EVO or a chassis code. |
| category | GT3 racing car | `THE MERCEDES-AMG GT3`; opening race-transmission bullet; `HIGHLIGHTS` model paragraph | Descriptive normalization of the GT3 model and racing context only, not a regulatory finding. |
| engine (optional) | AMG 6.3-litre naturally aspirated V8 | Opening engine bullet; `PERFORMANCE` > `Engine and electronics` | Applies to the vehicle described on this page. Omit exact cubic-centimetre capacity: the English page renders it as `6.208 cm3` with ambiguous punctuation. |
| drivetrain (optional) | Sequential six-speed racing gearbox; rear-axle transaxle configuration | `PERFORMANCE` > `AMG 6-speed racing gearbox` | Gearbox layout is explicit. Do not turn this into an unsupported standalone driven-wheel classification. |

Recommended minimal fields: manufacturer, model_name, category. The introduction distinguishes the GT3 introduced in 2015 from its successor unveiled in 2019. Scope the page's descriptive specifications to that successor; it does not establish a formal generation code, a model-year validity range or a named EVO variant. Leave generation and variant absent, and do not transfer these assertions to the separately linked GT3 Edition 130Y Motorsport.

Engine and gearbox are optional additions with that applicability statement. Omit dimensions and base_weight, which were not established in the cited text. Omit power: the opening 404 kW figure has insufficient configuration context for this sparse inventory. English model passages coexist with German legal/footer material and consent-gated videos; do not ingest the whole page as uniformly English evidence.

## Collection And Review

The evidence contract in [vehicles.py](../backend/app/vehicles.py) requires `url`, `publisher`, `kind`, `retrieved_at`, `sha256`, `anchor` and `language` on every field assertion.

- The pending [inventory](../examples/vehicle-inventory.json) contains three vehicles and eleven field assertions: Porsche manufacturer/model/category/generation, BMW manufacturer/model/category/variant, AMG manufacturer/model/category. All optional mechanical specifications are absent.
- Offline validation passed against the actual `VehicleInventory` and `BasicVehicleSpecification` models with `strict=True`: three unique vehicles, eleven assertions, exact intended field sets, three allowlisted HTTPS sources, and every URL/checksum/retrieval timestamp matching the captured HTTP record. The note's checksums/timestamps also matched. Network connections were blocked during validation; the ingestion and review functions were not invoked.
- Each assertion uses `kind: authoritative`, an official publisher, `language: en`, its verified passage locator and the actual raw-body digest/retrieval time above. This is source classification, not approval of wording, identities or applicability. No unsupported `status` or approval property is added to the strict schema; pending status is recorded in this companion note.
- The three official hosts are already in `vehicle_ingestion.APPROVED_HOSTS`; ports are HTTPS defaults. Actual status/content type/encoding/size checks match the collector's acquisition requirements. Search snippets, filenames, consent text and unrelated redirects are not assertion evidence.
- Remaining gates: human review of sources, proposed identities, English wording (especially AMG's normalized category), model/revision applicability, and any necessary ontology decision. This research cannot approve any of them. No Competition Eligibility is established.
- A later collector must refetch these URLs. A changed checksum blocks collection and requires fresh evidence review, not replacement of the digest without inspection. Because raw snapshots are not retained, exact historical source bodies cannot be reconstructed from this inventory alone. No stability across repeated requests is claimed.
- No `prepare_candidate`, ingestion CLI, review preview, live database/queue write, evidence acceptance or publication was run. The Porsche readability and BMW/AMG byte-download blockers are resolved for this observation only; review and publication gates remain.

Notable rejected paths: `https://motorsports.porsche.com/en/category/cars/911-gt3-r-992` redirected to `https://racing.porsche.com/`; the latter exposed only consent text. `https://www.bmw-m-motorsport.com/en/race-cars/bmw-m4-gt3-evo.html` yielded no meaningful extraction. `https://www.mercedes-amg.com/en/racing/gt3.html` returned 404; the old customer-racing homepage redirected to `https://www.mercedes-amg.com/en/motorsport`. Do not use these as vehicle evidence or assume other legacy paths share the same redirect.