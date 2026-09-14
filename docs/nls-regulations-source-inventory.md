# NLS 2026 Regulations: Source Inventory

Research date: **2026-09-11**. Scope: [Issue 12][issue], official NLS 2026 race-points evidence for comparison with the existing conditional Formula One sole-winner 25-point example. This is **private research, incomplete and pending human review**, not translation acceptance, ingestion, a Competition Profile, approval or publication.

## Result And Remaining Gaps

**Extraction resolved; evidence pending human review.** A1 and Bulletins 1-8 were reacquired and parsed in memory with `pypdf 6.16.2`. All nine hashes match the earlier ledger. A1's internal version is **as at 12 June 2026**, not merely the filename's after-Bulletin-5 label. Its 2026 allocation is a **class-starter/rank lookup table**, not a continuous points formula. [NLS index][rules] [Bulletin index][bulletins]

For annual championship classifications A-F, including the annual overall championship, a full-points **class winner** receives **2, 3, 4, 6, 8, 11, 15** points in a 4-hour race for respectively **1, 2, 3, 4, 5, 6, 7-or-more actual class starters**. The corresponding 6-hour awards are **3, 4, 5, 8, 10, 14, 19**. Nonregistered starters are not removed to promote registered participants. The separate **NLS Speed Trophy H** awards **35 race points for overall first place** to an eligible registered competitor/team; this is not the A-F driver/class-based award. See E04-E07 and E12 below, especially the exceptions and scope.

The existing [F1 inventory](f1-regulations-source-inventory.md) supports a conditional sole winner receiving 25 points: final first-place classification, no dead heat, at least 75% of scheduled distance, and the specified two consecutive leader laps without SC/VSC procedures. That FIA evidence was **not reacquired or independently revalidated in this continuation**. NLS instead states the duration bands and **70% class-winner / 50% overall-winner distance classification tests** below. No NLS 75% scoring threshold was found in these provisions. A defensible comparison must name the NLS award, race format, class field and eligibility; none establishes a real race's points. Translation acceptance, exact event applicability, DMSB edition/amendment resolution and the A1 approval-date conflict remain open.

## Authority And Discovery

- The [official NLS English homepage][home] links `https://teilnehmer.vln.de`, establishing the organizer's public participant/document portal. The portal is used as an explicitly linked first-party distribution surface, not an independent secondary source.
- A1 p. 1 names **VLN Sport GmbH & Co. KG** as series organizer, supported by VLN VV GmbH & Co. KG. The document authority is **VLN**, with **DMSB approval/visa 970/26**, not DMSB authorship substituted for the organizer. Bulletin signature blocks name VLN and DMSB separately. Signatures are printed attributions, not independently authenticated signatures. E01 and the internal-identity ledger distinguish dates and roles.
- The portal's [DMSB regulations index][portal-dmsb] links German and English 2026 circuit regulations and appendices, plus two bulletin links. Independently, the [official DMSB circuit-sport page][dmsb-index] supplies the exact DMSB-hosted English-labelled downloads below. A1 Art. 3, pp. 7-8 expressly incorporates the currently valid DMSB circuit regulations, Appendices 1 and 2, NLS regulations and DMSB-approved bulletins, among other instruments. This establishes incorporation by reference, **not which exact downloaded edition or amendment governed a particular event**.
- A1 Art. 3.1, p. 8 makes **only the DMSB-approved German text binding**. Parallel organizer-supplied English is a useful cross-check, not a replacement authority. All German-derived evidence below remains a pending translation.
- The [NLS website legal notice][legal] and its rights discussion were recorded in the earlier NLS research, not re-reviewed here. Public availability and private research authorization do not establish translation, reproduction or redistribution rights. No open licence or rights clearance is asserted.

## NLS PDF Ledger

Each row is a complete HTTP response-body SHA-256, computed before parsing. Every row returned **HTTP 200**, MIME **application/pdf**, and a **%PDF- signature**. Final URL equals the linked URL after ordinary percent-encoding of spaces; no redirect was received. No PDF body or German regulatory prose was saved. Times are retrieval completion times on **2026-09-11 UTC**.

The original acquisition ledger is retained unchanged. Internal identities and provision/page anchors are now verified to the extent stated in the next sections. All documents concern **2026**. German source text was inspected, with parallel English present in A1 and bulletin passages; this does not assert complete bilingual coverage of every appendix or image. All provision `effective_from` values remain `null`.

| Ref / exact download | Published version clue | Bytes | Retrieval UTC | SHA-256 |
| --- | --- | ---: | --- | --- |
| [A1: sporting regulations][a1] | A1, after Bulletin 5; approval indicated in filename | 1809857 | 06:22:25.522425Z | `462f1172233f5591ef681b38c99563a2ab989c15a7280ab4ac64ae67b2683897` |
| [B1][b1] | Bulletin 1; approval indicated in filename | 1442876 | 06:22:25.834566Z | `e678be8a9b1523c6414b4f4cf36112c0685d3f57a2afb889040e8270f5560775` |
| [B2][b2] | Bulletin 2; approval indicated in filename | 355235 | 06:22:26.008682Z | `f74c7f2f22fafce7f14eb7f82ce2f9cdb73dfe408f2480e056861cc4fa5cb3cb` |
| [B3][b3] | Bulletin 3; approval indicated in filename | 371008 | 06:22:26.196565Z | `347c028ecdd056de22b188b13079bec6b42062e65cad6f19ea2be4a0b26f3159` |
| [B4][b4] | Bulletin 4; approval indicated in filename | 491717 | 06:22:26.382087Z | `366e236cc96da3396a800091497262c46220300c82b6d33cb7c75f52f511697d` |
| [B5][b5] | Bulletin 5; approval indicated in filename | 346005 | 06:22:26.540138Z | `c6f0493d0822486f9c6bc2a1dd2b947d258d87ec72399772629c0cceba015509` |
| [B6][b6] | Bulletin 6; approval indicated in filename | 484783 | 06:22:26.706630Z | `ed6407d918d39f0585823ba5b18076283de3af5b9231fac59020d515a3e0f465` |
| [B7][b7] | Bulletin 7; approval indicated in filename | 427672 | 06:22:26.889355Z | `4ea6a979c28ca0cc5333ee96c3d0c1f843efed0026acd0832338dfc6b0736e98` |
| [B8][b8] | Bulletin 8; approval indicated in filename | 375258 | 06:22:27.084011Z | `6049de8d14b4a0518aa662c94322d6c4a59860fc55373c3933f8685435394fce` |

No Last-Modified or ETag header was present on these nine responses. HTTP Date was 2026-09-11T06:22:22Z for A1/B1/B2 and 06:22:23Z for B3-B8. These server-response dates are not document dates or effective dates.

### Internal Identity And Reacquisition

All rows below were HTTP 200 and were parsed with `PdfReader(BytesIO(...))`; hashes and URLs resolve to the same Ref in the original ledger. Times are on **2026-09-11 UTC**, recorded after response acquisition/parser initialization. Physical pages are one-based PDF positions. Printed page numbers agree with the physical pages cited here.

| Ref | Internal identity / version | Pages | Reacquisition UTC | Printed approval evidence and locator |
| --- | --- | ---: | --- | --- |
| A1 | ADAC Ravenol Nurburgring Langstrecken-Serie 2026, Part 1 Sporting Regulations; as at **2026-06-12**, p. 1 | 63 | 06:47:29.997768Z | Visa 970/26, p. 1; Art. 2.3 p. 6: German **2025-02-16**, English **2026-02-16**. Conflict unresolved. |
| B1 | Bulletin **01 / 2026**, to the Standard Regulations, p. 1 | 8 | 06:47:36.988722Z | p. 8: VLN approval **2026-03-02 15:00**; DMSB approval **2026-03-02** |
| B2 | Bulletin **02 / 2026**, same series/visa, p. 1 | 2 | 06:47:37.323830Z | p. 2: VLN approval **2026-03-11 15:00**; DMSB approval label/name present, **no date in the extracted approval field** |
| B3 | Bulletin **03 / 2026**, same series/visa, p. 1 | 2 | 06:47:37.607849Z | p. 2: VLN approval **2026-04-01 11:00**; DMSB approval **2026-04-01** |
| B4 | Bulletin **04 / 2026**, same series/visa, p. 1 | 3 | 06:47:37.922808Z | p. 3: DMSB approval **2026-04-09**; separate VLN approval time not verified in this pass |
| B5 | Bulletin **05 / 2026**, same series/visa, p. 1 | 1 | 06:47:38.254998Z | p. 1: VLN approval **2026-05-07 15:00**; DMSB approval **2026-05-07** |
| B6 | Bulletin **06 / 2026**, same series/visa, p. 1 | 4 | 06:47:38.635302Z | p. 4: VLN approval **2026-07-14 15:00**; DMSB approval **2026-07-14** |
| B7 | Bulletin **07 / 2026**, same series/visa, p. 1 | 2 | 06:47:39.003372Z | p. 2: VLN approval **2026-07-30 15:00**; DMSB approval **2026-07-30** |
| B8 | Bulletin **08 / 2026**, same series/visa, p. 1 | 1 | 06:47:39.390885Z | p. 1: VLN approval **2026-09-09 12:00**; DMSB approval **2026-09-09** |

The bulletin headers all identify base regulations visa **970/26 approved 2026-02-16**. This corroborates the English A1 date but does not silently correct the binding German clause. **An approval date is not a verified issue/publication date.** No separately labelled `issued_on` was established: it remains unknown (`null` in this research note), including for A1's consolidated June version. The approval dates above are exact observed dates, not invented issue dates. A1's **as-at** date is a version date, not evidence of first issuance or commencement. Bulletin approval times have **no verified timezone**; they must not be converted to UTC by assumption. Retrieval/translation timestamps, in contrast, are explicitly UTC.

## DMSB Supporting Downloads

The following exact links were discovered on the DMSB circuit-sport page, not synthesized from filenames. All returned HTTP 200 directly, application/pdf and a %PDF- signature. Titles are the English title portions of the index labels, normalized to ASCII. **English-labelled is not verified PDF language or definitive-language precedence.** Internal issue, document/approval date, applicability and section/page anchors remain unknown. These are supporting candidates, not proof that DMSB supplies the NLS championship points formula.

| Ref / index title | Bytes | Retrieval on 2026-09-11 UTC | SHA-256 |
| --- | ---: | --- | --- |
| [D1: Circuit Racing - Sporting Regulations 2026][d1] | 570526 | 06:24:16.112008Z | `4734d451f4b69e15ef374a9db0c319bf5196af171df5fdde9d9fc2eee736379a` |
| [D2: Circuit Racing - Sporting Regulations 2026 / Appendix 2 - Nurburgring Nordschleife][d2] | 393663 | 06:24:16.395538Z | `3d872c860addc5a9bfc334cee78111aec1e6b4ca158b9654f3dbdf3d318e5829` |
| [D3: Circuit Racing - Sporting Regulations 2026 / Appendix 1 - Code 60][d3] | 164586 | 06:24:16.641479Z | `ffa310d456a0291d8ce63d666fcd0d30ea421ed6daa30ff66b3ee0ca975be5bf` |

Last-Modified: D1 2026-02-06T10:05:33Z; D2 2026-02-06T10:07:09Z; D3 2025-12-09T09:44:52Z. No ETag was present. HTTP Date: D1 2026-09-11T06:24:12Z; D2/D3 06:24:13Z. These headers do not establish issue or effective dates; D3's 2025 header does not negate its 2026 index label.

The portal also exposes [Circuit Regulations 2026][portal-circuit], [Appendix 1][portal-app1] and [Appendix 2][portal-app2]. Those mirror bytes were **not** acquired or compared with D1-D3; titles alone do not prove byte equality. Two additional portal links are [Bulletin 1 for circuit-regulation Appendix 2][dmsb-b2] and [Bulletin 1 for Appendix 3][dmsb-b3]. Their bytes, dates, language, changes and applicability were not assessed. They remain explicit amendment candidates rather than an empty amendment list.

A DMSB permit overview and an entry form were incidentally fetched while resolving English download labels; neither is used as scoring evidence. The entry form returned DOCX, not PDF. This inventory does not expand into licence eligibility, entry procedures, technical regulations or a whole-rulebook audit.

## English Provision Evidence

These are short, factual **translations/paraphrases of German provisions**, not authoritative quotations or accepted evidence. Each E identifier is both a passage identifier and its proposed same-topic Provision identifier within this note; it is not a persisted application resource. Common Translation Record fields and precise source locators are given below. Every proposed Provision has `effective_from: null` and `effective_until: null`. Applicability is **NLS 2026, this A1 version and the award expressly identified**, not retrospective proof for every 2026 race.

| ID | Topic / source anchor (physical = printed page) | Short English evidence and limits |
| --- | --- | --- |
| E01 | sporting; A1 p. 1 title/organizer/version and Art. 2.3 p. 6 | VLN Sport GmbH & Co. KG organizes the series, supported by VLN VV GmbH & Co. KG. Part 1 is as at 12 June 2026, visa 970/26. The German approval clause prints 16 February 2025; parallel English prints 16 February 2026. Do not resolve this discrepancy without review. |
| E02 | sporting; A1 Art. 3 pp. 7-8; Arts. 3.1-3.2 p. 8 | The currently valid listed FIA/DMSB instruments, DMSB circuit Appendices 1 and 2, NLS Parts 1-3, approved bulletins and event regulations apply. Only DMSB-approved German text is binding. Interpretation involves the clerk/race director with stewards and organizer; final interpretation rests with DMSB sporting jurisdiction. No universal precedence ladder or exact DMSB edition is inferred. |
| E03 | scoring; B3 Part 1 Art. 4 p. 1; matching A1 Art. 4 p. 9 | The two ADAC 24h Nurburgring Qualifiers races run under their event regulations; points for all events listed in the NLS series calendar are awarded under these series regulations. This scoring-scope sentence is present in A1. It does not prove an individual Qualifiers race was completed or eligible for an award. |
| E04 | scoring; A1 Art. 25 p. 51 | Registered drivers and competitors/teams are eligible for championship classifications A-I only after registration and its fee have been received. Earlier results are not counted. Nonregistered participants receive no championship points and appear only in event classifications. Additional Cup/Trophy conditions also apply. No automatic crew-wide duplication or division of an award is established here. |
| E05 | scoring; A1 Art. 25.1 pp. 51-52 | For classifications A-F, excluding G/H/I, awards use the actual class placing in official final race results and the Arts. 25.1.1-25.1.2 tables. Nonregistered participants are not deleted and registered participants do not move up, except for classification/sporting penalties. The number of class starters counts vehicles actually starting: crossing the start line after the start signal or starting subsequently from the pit lane. This is not a count of registered entrants, qualifiers or finishers. |
| E06 | scoring; A1 Arts. 25.1.1-25.1.2 p. 53 | The 4-hour and 6-hour allocation matrices below depend on class starters and finishing rank. The tables explicitly allow a one-starter class to score 2 or 3 full points respectively; no seven-starter minimum is imposed by these tables. Seven-or-more is a field-size band, not an eligibility threshold. No continuous formula or general points-rounding instruction was found in these allocation paragraphs. |
| E07 | scoring; A1 Art. 25.1 p. 52, shortened/stopped-race allocation | If scheduled distance is shortened, or a stopped race is not resumed: 4-hour race duration up to 80 minutes gives no classification; over 80 through 160 gives half points; over 160 gives full points. For 6-hour races: up to 120 gives no classification; over 120 through 250 gives half points; over 250 gives full points. The rule says 250, not 240. These are duration conditions, not a 75% distance test. Scope follows the A-F allocation article; application to separate G/H/I awards is not established here. |
| E08 | scoring; A1 Art. 24 pp. 49-50 | The winner completes the most laps; equal distances are ordered by shorter elapsed time, including imposed time penalties. Classification requires at least 70% of the class winner's distance and 50% of the overall winner's distance, each commercially rounded, and crossing the finish/timing line no later than 20 minutes after the overall winner is flagged. Finish and counted laps must be under the vehicle's own engine power. The final lap must combine the GP course and Nordschleife. Vehicles entering the pit lane while being flagged can cross its extended timing line; vehicles already in the pit lane when the leader is flagged are not classified. Results become final after technical checks and any protest/appeal proceedings. No rule for an exact equal-distance/equal-time dead heat is established. |
| E09 | scoring; A1 Art. 18.5 pp. 41-42, especially p. 42 | Stoppage classification refers to DMSB circuit Arts. 16.4 and/or 16.5, and requires the last counted lap to end over the timing line under own engine power. The extracted restart clauses distinguish a leader below two laps from above two laps. Exactly two laps and the incorporated DMSB details are not resolved here; this is not a complete restart algorithm. |
| E10 | scoring; A1 Art. 25.2 pp. 53-54 | For A-F, ten or nine completed races use the best eight results. Drivers/competitors/teams completing eight or fewer count those results without a discard. A completed counting race is a classified race in which that vehicle crossed the start line. A disqualification cannot be discarded. These are season-total rules, not individual race award amounts or proof of the actual season race count. |
| E11 | scoring; A1 Art. 25.3 p. 54 | A driver starting two cars nominates the car for driver-championship points on the signed double-starter list by Saturday 08:00; without nomination the lower start number is used. Class classifications separately count the placing in each of two different classes, or the better placing when both cars are in one class. This is a double-start exception, not a rule for dividing points among co-drivers. |
| E12 | scoring; A1 Art. 25.6.2 p. 60 | NLS Speed Trophy H is separate: registered competitors/teams identified by car start number score for top-20 overall race positions. Overall first is 35 race points. Qualifying also awards 3/2/1 to the three fastest registered competitors/teams. Thus 35 race points is not a driver's A-F award or necessarily the event total. Shortened-race treatment for H remains unverified. |
| E13 | scoring; A1 Art. 25.1 pp. 52-53 | Written objections to race or championship points must reach the organizer within 14 days of publication. The organizer may correct obvious errors after publication; complaints are directed to it and this clause states no appeal against its points decision. Read together with Art. 3.2, not as an unlimited power to change the regulations. |

### Allocation Matrices

E06, A1 p. 53, cross-checked using plain extraction and `extraction_mode='layout'`. Columns are **actual starters in the class**; rows are **official final class rank**. A dash preserves a blank source cell (rank exceeds that starter count), not a Competition Profile state. The last row applies only where that rank exists. Registration, classification, penalties and E07 remain prerequisites.

**4-hour race, Art. 25.1.1:**

| Class rank | 1 starter | 2 | 3 | 4 | 5 | 6 | 7 or more |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 2 | 3 | 4 | 6 | 8 | 11 | 15 |
| 2 | - | 2 | 3 | 4 | 6 | 8 | 11 |
| 3 | - | - | 2 | 3 | 4 | 6 | 8 |
| 4 | - | - | - | 2 | 3 | 4 | 6 |
| 5 | - | - | - | - | 2 | 3 | 4 |
| 6 | - | - | - | - | - | 2 | 3 |
| 7 | - | - | - | - | - | - | 2 |
| 8 or lower | - | - | - | - | - | - | 1 |

**6-hour race, Art. 25.1.2:**

| Class rank | 1 starter | 2 | 3 | 4 | 5 | 6 | 7 or more |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 3 | 4 | 5 | 8 | 10 | 14 | 19 |
| 2 | - | 3 | 4 | 5 | 8 | 10 | 14 |
| 3 | - | - | 3 | 4 | 5 | 8 | 10 |
| 4 | - | - | - | 3 | 4 | 5 | 8 |
| 5 | - | - | - | - | 3 | 4 | 5 |
| 6 | - | - | - | - | - | 3 | 4 |
| 7 | - | - | - | - | - | - | 3 |
| 8 or lower | - | - | - | - | - | - | 1 |

A faithful operational representation is **table lookup by race format, actual class starters and final class rank**, then the applicable half/full multiplier from E07. No fractional-award rounding rule is inferred. For illustration only, a classified, registered sole class winner in a full-points 4-hour race with at least seven class starters has a 15-point A-F table award; with six starters it is 11. These are conditional derivations, not sourced results from a real race or an F1-equivalent overall-winner claim.

### Bounded Profile Mapping

This is research, not an ingested or accepted Competition Profile. The seven possible topics are retained without invented unavailable states:

| Topic | Research state | Evidence/value scope |
| --- | --- | --- |
| scoring | known, pending translation review | E03-E13: A-F class-based tables, eligibility, duration and classification conditions; distinct Speed Trophy H caveat |
| eligibility | unknown | Scoring prerequisites are recorded, but no general participation-eligibility profile was researched. |
| format | unknown | The 4h/6h distinction supports scoring only; no complete format profile is asserted. |
| tyres | unknown | Bulletin headings are not a verified tyre profile. |
| pit-stops | unknown | Not researched for a profile. |
| sporting | unknown | E01-E02 establish evidence authority and interpretation context, not a general sporting profile. |
| technical | unknown | B6-B8 scope was inspected for scoring relevance, not a complete technical profile. |

No topic is labelled `not-published` or `not-applicable`. Remaining unknowns include actual event starter/classification data, full shared-car driver entitlement, exact dead-heat allocation, separate G/H/I reduction rules and the incorporated DMSB provisions.

## Amendments, Conflicts And Temporal Limits

1. **Verified relevant incorporation:** B3 Part 1 Art. 4, p. 1 amends event/scoring scope; its Qualifiers and NLS-calendar points wording is present in A1 Art. 4 p. 9. E03 records both anchors. This is a verified textual match, not a complete B1-B5 consolidation audit. [A1][a1] [B3][b3]
2. **B1-B5 bounded scan:** B1 affects Part 1 Art. 14 scrutineering (p. 1), technical tyres and BMW M2 braking/suspension/aerodynamics/ride height (pp. 1-8). B2 concerns Part 2 Appendix 2.15 tyre procedures (pp. 1-2). B3 also changes Appendix 2.6 Art. 2.5 brakes (p. 1). B4 concerns technical provisions and Appendix 2.6 Art. 2.16 ride height (pp. 1-2); B5 Part 2 Art. 2.11 electrical equipment (p. 1). No direct amendment of Arts. 24 or 25 was identified in their extracted text. Technical compliance can still affect final classification; this is not proof of no indirect scoring effect.
3. **B6-B8 actual scope:** B6, approved 14 July, addresses Part 2 Art. 2.4.4 cooling (p. 1) and Appendix 2.6 Art. 2.9 BMW M2 rear-wing requirements/drawings (pp. 2-3). B7, approved 30 July, revisits the same cooling article and rear-wing positioning (pp. 1-2). Their cooling text includes a maximum **10 mm x 10 mm** mesh opening. B8, approved 9 September, addresses Part 2 Art. 1.10 fuel-system safety (p. 1): its fuel-pump paragraph requires pumps to operate only with the engine running except during starting; the stated exemption concerns Group H and VLN production cars using the production tank in its original position. The adjacent shut-off-valve change contains overlapping deleted/inserted words in plain extraction, so its final mandatory-versus-recommended wording is **not resolved here**. None of the extracted B6-B8 text directly amends A1 Arts. 24-25. Rear-wing diagrams and strike-through semantics were not visually audited; no dimensions or complete technical interpretation are asserted. Their incorporation into the appropriate Part 2/appendix version is unverified, and A1's June version predates their approvals. [B6][b6] [B7][b7] [B8][b8]
4. **Numbering is not applicability:** the eight indexed bulletins do not prove complete history. Approval blocks were inspected, but separate issue dates and event-specific commencement were not established. An empty encoded amendment list must not mean no amendments. Proposed links here are B3 to A1 Art. 4, B6/B7 to their Part 2/Appendix 2.6 targets, and B8 to Part 2 Art. 1.10; uninspected target versions are not resolved Provision resources.
5. **Organizer and DMSB rules:** A1 Arts. 3 and 3.1 establish incorporation and definitive German language; Art. 18.5 explicitly cites DMSB circuit Arts. 16.4/16.5. D1-D3 bodies and the portal's two DMSB bulletin candidates were not parsed in this continuation. Their precise versions, language conflicts, amendment effects and application to a named race remain unknown. [Portal DMSB index][portal-dmsb]
6. **Editorial season-count context:** the earlier original-English April 19 observation refers to an abandoned fourth race and eight races. A1 Art. 25.2 now supplies the separate discard rule (E10), but the article is not a regulatory amendment or proof of each car's completed counting races. No actual season total is calculated. [Organizer report][season-report]
7. **Event-specific coverage:** supplementary regulations, stewards' decisions, final classifications and the Qualifiers' distinct sporting context were not audited. No named race's effective rule set, starter count, classified winner, completed distance or points has been established. An approval/version date or lack of a discovered amendment cannot fill these gaps. Art. 25.4 pp. 54-55 addresses season points ties, not an established exact race dead-heat rule; its complete tie cascade is outside this evidence slice.

## HTML Provenance

All rows returned HTTP 200. Hashes cover full response bodies held in memory. HTML is dynamic: different hashes on repeated GETs are not, by themselves, evidence of changed rules. Locators must be paired with their observation hash. Times are on **2026-09-11 UTC**.

| Ref | Retrieval UTC | SHA-256 | Language / locator |
| --- | --- | --- | --- |
| [NLS homepage][home] | 06:21:58.337552Z | `d6834fe64f37f62e5ec181708d0b345b29de7a4e3a276e4816b4da91d1f87c5b` | English route; anchor href `https://teilnehmer.vln.de` |
| [NLS rules index][rules] | 06:21:58.538059Z | `6c10d6f9ae7b4544e531e38d5267948be865b2fcab43043068c9eab7944fda8c` | German document metadata; `a[href]` for A1 |
| [NLS bulletins index][bulletins] | 06:21:58.664503Z | `d1c581a5ca29cdcb0f9a1a720b7a029ad894243f8ef266913f12bd1dee335ce4` | German document metadata; B1-B8 download anchors |
| [Portal DMSB index][portal-dmsb] | 06:22:27.833304Z | `6b24970784fa758e6fb59dcc44250a7fd095ccc75379936628a63a53c063d1c8` | German portal with English/German document labels; exact download anchors |
| [DMSB circuit-sport index][dmsb-index] | 06:23:46.935857Z | `47b271f9a9e37a90acae9dbe6b11496db1481ae486c66b0f05fa1e1a8196cfa8` | German page, English download titles; anchors ending `/282219`, `/282189`, `/282187` |
| [April 19 organizer report][season-report] | 06:23:47.406959Z | `fdd6d822f10c3453903273c4de649355795c772ba732b4f81ff76d2b6b1ac8d1` | Original English; `.entry-content p`, zero-based index 10; limited predicates above |

## Translation And Review State

The earlier filename-only metadata translations are superseded by the following **pending** records for the newly inspected passages and document identities. The records are expressed without duplicating source URLs/hashes: each row plus the common fields below plus its Ref's exact URL, SHA-256 and reacquisition timestamp is the complete logical record. No approval identity in a PDF is a translation reviewer.

Common fields for **every** E/M record:

- `source_language: de`; output `language: en`; evidence `kind: translation` (short factual paraphrase, not a purported verbatim quotation).
- `method: assistant factual English translation of German PDF text; organizer parallel English cross-check where present`.
- `version: nls-scoring-research-v2; pypdf 6.16.2; Python 3.12.10`.
- `translated_at: 2026-09-11T06:51:42.9167838Z`, the UTC record-assembly timestamp for this translation pass; extraction/rechecks occurred from 06:47:29.997768 through 06:51:11.973022 UTC. This is not a document date.
- `review_state: pending`; `reviewer: null`; `reviewed_at: null`; `authorization: null`.
- `source_url` and `source_sha256`: the exact linked Ref and full SHA-256 from the PDF ledger; `source_anchor`: the locator in the following table. Original URLs/filenames are provenance identifiers, not retained German rule-body text.

| Translation record / evidence | Source Ref | Source anchor |
| --- | --- | --- |
| E01 | A1 | p. 1 title/organizer/as-at/visa; p. 6 Art. 2.3, German and English approval clauses |
| E02 | A1 | pp. 7-8 Art. 3; p. 8 Arts. 3.1-3.2 |
| E03-B3 | B3 | p. 1 Part 1 Art. 4, Qualifiers and points-allocation paragraph |
| E03-A1 | A1 | p. 9 Art. 4, matching Qualifiers and points-allocation paragraph |
| E04 | A1 | p. 51 Art. 25, registration/fee and nonregistered participants |
| E05 | A1 | pp. 51-52 Art. 25.1, scope/final class rank/actual starters |
| E06 | A1 | p. 53 Art. 25.1.1 4h matrix and Art. 25.1.2 6h matrix |
| E07 | A1 | p. 52 Art. 25.1, shortened/stopped-race duration bands a/b |
| E08 | A1 | pp. 49-50 Art. 24, distance/finish/finality conditions |
| E09 | A1 | pp. 41-42 Art. 18.5, stoppage/restart, especially p. 42 DMSB reference |
| E10 | A1 | pp. 53-54 Art. 25.2, discards and disqualification |
| E11 | A1 | p. 54 Art. 25.3, double-start allocation |
| E12 | A1 | p. 60 Art. 25.6.2, eligibility/race table/qualifying points |
| E13 | A1 | pp. 52-53 Art. 25.1, objections and corrections |
| M01 | B1 | p. 1 title/visa, Part 1 Art. 14 and Part 2 Art. 1.12; pp. 2-8 Appendix 2.6 article headings; p. 8 approval block |
| M02 | B2 | p. 1 title/visa and Part 2 Appendix 2.15 heading; p. 2 approval block |
| M03 | B3 | p. 1 title/visa and Appendix 2.6 Art. 2.5 heading; p. 2 approval block |
| M04 | B4 | p. 1 title/visa/Part 2 heading; p. 2 Appendix 2.6 Art. 2.16 heading; p. 3 DMSB approval block |
| M05 | B5 | p. 1 title/visa, Part 2 Art. 2.11 heading and approval block |
| M06 | B6 | p. 1 title/visa and Part 2 Art. 2.4.4; pp. 2-3 Appendix 2.6 Art. 2.9 text/figure captions; p. 4 approval block |
| M07 | B7 | p. 1 title/visa, Part 2 Art. 2.4.4 and Appendix 2.6 Art. 2.9; p. 2 figure caption and approval block |
| M08 | B8 | p. 1 title/visa, Part 2 Art. 1.10 fuel-pump paragraph and approval block; shut-off-valve edit explicitly unresolved |

M records cover the short English identity/amendment summaries above, not a translation of entire technical provisions or unread images. E06 includes the numeric matrices. E03 deliberately has **two** Translation Records, one for each independently hashed document. The preexisting original-English HTML observations remain paraphrases, not translation approvals. No accepted state, actual reviewer or acceptance authorization has been supplied.

PDF identity and rule evidence are not human-reviewed. Private research authorization does not authorize a Translation Record to be marked accepted. There is no candidate acceptance, publication permission, inferred no-amendments finding or rule-completeness claim in this note.

## Method And Explicit Blockers

Ordinary public HTTPS GETs used the root `.venv` Python 3.12.10, HTTPX and SHA-256; the earlier HTML discovery used BeautifulSoup. PDF response bodies stayed in process memory. No PDF/HTML body or German regulatory prose was written to the repository. The temporary excerpt-output incident below is an explicit exception to a stricter no-disk-text claim. No credentials, secondary sporting summaries, access-control bypass or remote translation service were used. Terminal calls were serial, with no concurrent research terminal.

**PDF parsing blocker resolved on 2026-09-11:** the user installed `pypdf 6.16.2` in the root `.venv`. A serial reacquisition at 06:47:29.997768-06:47:39.390885 UTC successfully parsed A1 (63 pages) and B1-B8 (8, 2, 2, 3, 1, 4, 2, 1 pages respectively) using `pypdf.PdfReader(BytesIO(response.content))`. All nine response-body SHA-256 values match the ledger above. Subsequent targeted re-fetches through 06:51:11 UTC had the same hashes. Plain text extraction, bounded left-column `visitor_text` extraction and a layout-mode table cross-check were used. Layout mode warned about rotated text; numeric row/column alignment was visible, but this was not visual PDF review or OCR. Images, strike-through and some typography remain extraction limits. No package or dependency file was changed in this continuation.

**Temporary-output incident:** the first scan exceeded the terminal tool's aggregate output limit, creating two overflow transcripts outside the repository; a subsequent roughly 10 KB excerpt created a third. All three identified files were removed and their absence explicitly verified at **2026-09-11T06:51:42.9167838Z** after an earlier cleanup check found a remaining copy. Later calls were limited to approximately 3 KB of excerpt text. No raw PDF was written. This note does not claim that editor/session infrastructure has no transcript retention; no original German rule text is retained in the repository.

**Remaining evidence gates:** human translation review; A1's contradictory approval date and separately unknown issue date; exact DMSB editions/Arts. 16.4-16.5 and amendment effects; visual interpretation of relevant graphical/deletion changes if technical validity becomes material; real event eligibility, starter counts and final classifications. No full rulebook, complete amendment history, race dead-heat allocation or generic crew points entitlement is claimed.

**Implementation follow-up:** [the pending NLS inventory](../backend/fixtures/nls-2026-regulations.json)
now represents VLN organizer authority, the verified organizer portal and unknown
issue dates. It contains A1 and B3, 14 English passages and Provisions, and seven
profile topics. Its `nls-scoring-v1` Translation Records were assembled from this
research, with their own timestamp; all remain pending. The fixture is a candidate,
not approval or a completed Publication.

Both PDF hashes were subsequently verified through `prepare_candidate` against a
disposable in-memory schedule baseline. Tests confirm preservation of F1 and the
schedule, and rejection of publication while translations remain pending. These
checks do not establish translation acceptance or event applicability. The research
and implementation did not change the operational review queue or live stores.

[issue]: https://github.com/chwunderpers/racing-hub/issues/12
[home]: https://www.nuerburgring-langstrecken-serie.de/language/en/
[legal]: https://www.nuerburgring-langstrecken-serie.de/language/en/imprint/
[rules]: https://teilnehmer.vln.de/formulare.php?d=Ausschreibung
[bulletins]: https://teilnehmer.vln.de/formulare.php?d=Bulletins
[portal-dmsb]: https://teilnehmer.vln.de/formulare.php?d=DMSB-Reglements
[a1]: https://teilnehmer.vln.de/download.php?file=teilnehmer/Ausschreibung/A1%20Ausschreibung%20Teil%201_SPORTLICHES%20REGLEMENT_2026_genehmigt_nachBulletin5.pdf
[b1]: https://teilnehmer.vln.de/download.php?file=teilnehmer/Bulletins/Bulletin_1_2026_genehmigt.pdf
[b2]: https://teilnehmer.vln.de/download.php?file=teilnehmer/Bulletins/Bulletin_2_2026_genehmigt.pdf
[b3]: https://teilnehmer.vln.de/download.php?file=teilnehmer/Bulletins/Bulletin_3_2026_genehmigt.pdf
[b4]: https://teilnehmer.vln.de/download.php?file=teilnehmer/Bulletins/Bulletin_4_2026_genehmigt.pdf
[b5]: https://teilnehmer.vln.de/download.php?file=teilnehmer/Bulletins/Bulletin_5_2026_genehmigt.pdf
[b6]: https://teilnehmer.vln.de/download.php?file=teilnehmer/Bulletins/Bulletin_6_2026_genehmigt.pdf
[b7]: https://teilnehmer.vln.de/download.php?file=teilnehmer/Bulletins/Bulletin_7_2026_genehmigt.pdf
[b8]: https://teilnehmer.vln.de/download.php?file=teilnehmer/Bulletins/Bulletin_8_2026_genehmigt.pdf
[dmsb-index]: https://www.dmsb.de/de/automobilsport/rundstrecke
[d1]: https://www.dmsb.de/de/automobilsport/rundstrecke/file/282219
[d2]: https://www.dmsb.de/de/automobilsport/rundstrecke/file/282189
[d3]: https://www.dmsb.de/de/automobilsport/rundstrecke/file/282187
[portal-circuit]: https://teilnehmer.vln.de/download.php?file=teilnehmer/DMSB-Reglements/Circuit%20Regulations%202026.pdf
[portal-app1]: https://teilnehmer.vln.de/download.php?file=teilnehmer/DMSB-Reglements/Circuit%20Regulations%202026_Appendix_1.pdf
[portal-app2]: https://teilnehmer.vln.de/download.php?file=teilnehmer/DMSB-Reglements/Circuit%20Regulations%202026_Appendix_2.pdf
[dmsb-b2]: https://teilnehmer.vln.de/download.php?file=teilnehmer/DMSB-Reglements/Bulletin_1_Rundstrecken-Reglement_Anhang_2_.pdf
[dmsb-b3]: https://teilnehmer.vln.de/download.php?file=teilnehmer/DMSB-Reglements/Bulletin_1_Rundstrecken-Reglement_Anhang_3.pdf
[season-report]: https://www.nuerburgring-langstrecken-serie.de/language/en/2026/04/19/five-brands-in-the-top-five-audis-success-and-a-nail-biting-finish-at-the-nurburgring/