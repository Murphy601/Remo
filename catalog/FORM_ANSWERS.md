# Form answers (per document)

These answers map to the intake questions for the 50 internal engineering documents in documents/.

Direct file links: [DOWNLOADS.md](../DOWNLOADS.md). All 50 as a zip: [documents.zip](../documents.zip).

## Answers that are the same for every file

1. **Current or most recent job title:** Software Engineer II
2. **Years of professional experience:** 5–10 (about six years, 2019–present)
3. **Field:** Software Engineering / Data Science
4. **Pages:** 40–48 (counted with LibreOffice Writer → PDF)

Author on every document: Aman Kumar, Software Engineer II, Northstar Engineering. Engagements covered: Oakridge Industrial, Riverview Health Network, Clearhaven Markets.

## Per-document answers (questions 4–7)

| # | File | Pages | Words | Written | Description |
|---|---|---|---|---|---|
| 1 | `01-oakridge-inventory-api-requirements.docx` | 43 | 12801 | 18-11-2019 | Requirements document for the Oakridge inventory position API v1, written so plant ops, the EM, and the implementing engineers share one scope cut after tick... |
| 2 | `02-oakridge-new-engineer-integration-guide.docx` | 43 | 11981 | 21-02-2020 | Internal integration guide for Northstar engineers joining the Oakridge inventory-api work, covering VPN, schema, local snapshot, extract path, and ownership. |
| 3 | `03-oakridge-inventory-rest-design.docx` | 44 | 13991 | 09-01-2020 | Technical design for the Oakridge inventory position REST API v1, covering resources, cursors, caching, and failure modes for implementers and reviewers. |
| 4 | `04-oakridge-ops-kickoff-notes.docx` | 44 | 14140 | 16-10-2019 | Decision-oriented kickoff notes for the Oakridge inventory position API, written so a colleague can act without listening to the WebEx recording. |
| 5 | `05-oakridge-inventory-extract-sop.docx` | 41 | 14405 | 12-03-2020 | On-call SOP for the Oakridge nightly inventory extract and replica load, written for a cold 2am run with exact commands and refuse conditions. |
| 6 | `06-riverview-unified-patient-api-prd.docx` | 44 | 12164 | 27-08-2020 | Product requirements for the Riverview unified patient read API, written for CMIO, nursing, integration, and Northstar engineering before the RapidChart Flag... |
| 7 | `07-riverview-identity-merge-design.docx` | 48 | 11957 | 14-01-2021 | Technical design for Riverview record merge and identity resolution, written for engineering, HIM, and the CMIO liaison before any auto-link is enabled. |
| 8 | `08-riverview-inflated-census-incident.docx` | 45 | 11967 | 22-06-2021 | Incident report for the inflated Riverview census counts, written after the Flagstaff bed-board mismatch, covering timeline, impact, root cause, and the dedu... |
| 9 | `09-riverview-api-test-strategy.docx` | 48 | 11994 | 05-03-2021 | QA test strategy for the unified patient read API, written so engineering and Sneha share one fixture policy and so the four pre-staging regressions stay man... |
| 10 | `10-riverview-gha-migration-memo.docx` | 41 | 13881 | 09-11-2021 | Recommendation memo asking Priya Nair to approve moving Riverview Patient API CI off Jenkins to GitHub Actions with VLAN-hosted runners so PHI fixtures never... |
| 11 | `11-riverview-patient-api-oncall-runbook.docx` | 43 | 12049 | 30-09-2021 | On-call runbook for Riverview patient-api. Written so a Northstar engineer who did not ship the last release can isolate a facility feed, talk to ChartLine o... |
| 12 | `12-riverview-clinical-feedback-notes.docx` | 45 | 14833 | 13-04-2021 | Meeting notes from a Riverview clinical feedback session on RapidChart assemble behavior. Captures decisions, owners, and the rejected idea of leading with a... |
| 13 | `13-riverview-phi-logging-sop.docx` | 43 | 13748 | 19-07-2021 | SOP for keeping Riverview PHI out of logs, traces, and Slack. Written for on-call engineers and anyone cutting a support zip. |
| 14 | `14-riverview-fhir-vs-rest-design.docx` | 47 | 13036 | 08-10-2020 | Technical design choosing custom REST over FHIR R4 for Riverview patient-api v1, with constraints, payload math, and a rejected HAPI-on-day-one path. |
| 15 | `15-riverview-chart-assemble-prd.docx` | 47 | 12935 | 18-02-2021 | PRD for Riverview chart assemble: blocks, latency budget, partial-fill banners, caching, and success metrics tied to nurse time rather than QPS. |
| 16 | `16-clearhaven-recon-platform-design.docx` | 45 | 12004 | 15-09-2022 | Internal systems design for the Clearhaven recon platform. Written so engineering can build ingest-api, match-engine, break-svc, and recon-query, and so Clea... |
| 17 | `17-clearhaven-kafka-ingestion-redesign.docx` | 45 | 12659 | 11-04-2023 | Technical design for the Clearhaven Kafka ingest cutover. Written so ingest-api, match-engine, and SRE can ship CLH-5519 without re-arguing partition count o... |
| 18 | `18-clearhaven-api-versioning-strategy.docx` | 45 | 14199 | 03-08-2023 | Technical design for versioning Clearhaven recon HTTP APIs. Written after CLH-INC-2023-061 so engineering, QA, and the TAM have one policy for breaking changes. |
| 19 | `19-clearhaven-consumer-lag-runbook.docx` | 43 | 13893 | 20-06-2023 | Operational runbook for Clearhaven match-engine consumer lag. Written for the primary on-call to execute without the author on the call. |
| 20 | `20-clearhaven-settlement-break-incident.docx` | 44 | 11972 | 16-11-2023 | Incident report for the November 14, 2023 Clearhaven settlement break. Written for engineering, ops, TAM, and control owner so the filename idempotency gap i... |
| 21 | `21-clearhaven-kafka-vs-filedrop-memo.docx` | 40 | 14401 | 07-02-2023 | Internal recommendation memo from Aman Kumar to Priya Nair and Marcus Bell comparing three ingest options for Clearhaven recon and taking a position for Kafk... |
| 22 | `22-clearhaven-postgres-partitioning-design.docx` | 44 | 12481 | 18-05-2023 | Technical design for range-partitioning Clearhaven recon fact and break tables in Postgres 13, including indexes, detach-to-cold, query-planner risks, and an... |
| 23 | `23-clearhaven-batch-replay-prd.docx` | 46 | 11987 | 22-01-2024 | Product requirements for an ops-facing batch replay action on the Clearhaven recon platform, written by Aman Kumar with Helen Cho as acceptor and Maya Singh'... |
| 24 | `24-clearhaven-prod-deploy-sop.docx` | 45 | 11992 | 14-09-2023 | Step-by-step production deploy SOP for Clearhaven recon Helm releases, including freeze windows, canary, error-budget abort, and rollback commands. |
| 25 | `25-clearhaven-sla-review-notes.docx` | 46 | 15370 | 12-03-2024 | Internal meeting notes from the Q1 2024 Clearhaven recon SLA review, capturing decisions, the month-end 7:35 exception, open weekend-scope question, and name... |
| 26 | `26-clearhaven-idempotent-consumers-design.docx` | 43 | 11978 | 06-07-2023 | Technical design for idempotent Kafka consumers on the Clearhaven recon ingest path. Written after a week of duplicate exception tickets so the team has one... |
| 27 | `27-clearhaven-unversioned-api-incident.docx` | 46 | 11982 | 28-03-2023 | Incident report for the March 22 unversioned field rename on break-svc. Written so Priya has a record for Clearhaven, so Kavya has the review checklist that... |
| 28 | `28-clearhaven-otel-rollout-design.docx` | 44 | 14365 | 15-02-2024 | Technical design for the Clearhaven OpenTelemetry rollout. Written so Diego can size the collector, Kavya can pick agent versus SDK, and Priya can see what w... |
| 29 | `29-clearhaven-datadog-vs-grafana-memo.docx` | 45 | 12275 | 09-04-2024 | Recommendation memo for Priya Nair on Datadog versus the existing Grafana stack after a six-week trial. Written with trial invoices, cardinality counts, and... |
| 30 | `30-clearhaven-dlq-design.docx` | 46 | 11970 | 12-10-2023 | Technical design for the settlement inbound dead letter topic and replay path. Written so match-engine owns operations, ingest-svc has a producer contract, a... |
| 31 | `31-clearhaven-worker-oom-runbook.docx` | 40 | 12186 | 21-05-2024 | Internal on-call runbook for match-engine OOM on nested RailClear payloads. Written after CLH-INC-2024-091 so SE II and SRE share one set of commands and a h... |
| 32 | `32-clearhaven-schema-migration-sop.docx` | 41 | 11943 | 18-06-2024 | Standard operating procedure for Flyway migrations against Clearhaven recon Postgres. Written after the June 3 hotfix checksum incident so expand/contract an... |
| 33 | `33-clearhaven-spark-backfill-design.docx` | 43 | 12078 | 23-07-2024 | Technical design for the 2019-2022 Spark backfill onto partitioned recon tables. Written so we do not run a 4.6 billion row load on the OLTP primary and so t... |
| 34 | `34-clearhaven-capacity-fy25-memo.docx` | 43 | 12426 | 05-09-2024 | Capacity planning memo for Clearhaven recon FY25. Written to kill the 12-broker ask and replace it with 4 brokers, compaction, and Postgres disk, with a do-n... |
| 35 | `35-clearhaven-grpc-internal-adr.docx` | 46 | 11968 | 14-08-2024 | Architecture decision record for putting gRPC on the internal open-break path while leaving REST on recon-query. Accepted. Written so the next protocol argum... |
| 36 | `36-clearhaven-loadtest-8m-report.docx` | 44 | 12128 | 17-10-2024 | Internal load test report for Clearhaven recon. Written after the October 14-16 shadow runs so Priya and Marcus can decide hardware and so the match team can... |
| 37 | `37-clearhaven-postgres-failover-runbook.docx` | 40 | 13753 | 08-11-2024 | On-call runbook for Clearhaven recon Postgres. Written so a Northstar engineer can promote a replica, point ingest at the new primary, and confirm WAL withou... |
| 38 | `38-clearhaven-cdc-settlement-design.docx` | 43 | 14922 | 19-01-2023 | Technical design for Clearhaven settlement ingest. Written to freeze the lister-plus-hash approach and to kill the Debezium proposal before we spent a quarte... |
| 39 | `39-clearhaven-api-versioning-review-notes.docx` | 45 | 12926 | 25-07-2023 | Meeting notes from the July 25 architecture review of Clearhaven ops-api versioning. Written so the URI vs header decision and the /v1 sunset argument are on... |
| 40 | `40-clearhaven-kafka-rebalance-incident.docx` | 45 | 12682 | 11-01-2024 | Incident report for the January 8 match-engine rebalance storm. Written for Priya, Marcus, and the on-call rotation so the timeout and staging-partition mist... |
| 41 | `41-clearhaven-oncall-sop.docx` | 44 | 13686 | 07-12-2023 | Internal SOP for Northstar engineers covering Clearhaven reconciliation production. Written so a tired person at 02:14 ET can decide whether to page, who to... |
| 42 | `42-clearhaven-terraform-aws-design.docx` | 46 | 11960 | 28-03-2024 | Technical design for moving Clearhaven recon AWS resources under Terraform modules and a locked apply path. Written for engineers who will import, plan, and... |
| 43 | `43-clearhaven-exception-codes-prd.docx` | 44 | 12125 | 05-12-2024 | Product requirements for structured recon exception codes, mapping, UI, reporting, and immutable history. Written for engineering, ops, QA, and the Clearhave... |
| 44 | `44-clearhaven-model-summary-eval-rubric.docx` | 45 | 11959 | 13-02-2025 | Operational evaluation rubric for Northstar engineers scoring model-written Clearhaven recon break summaries. Used in the weekly review queue, not as an acad... |
| 45 | `45-clearhaven-matchkey-redis-design.docx` | 43 | 14198 | 02-05-2024 | Technical design for a Redis hot cache of Clearhaven recon match keys. Written for the people who will implement the client, size the box, and sit the incide... |
| 46 | `46-clearhaven-k8s-compute-memo.docx` | 47 | 12036 | 02-11-2023 | Internal recommendation memo from Software Engineer II Aman Kumar to the Clearhaven engineering manager and SRE lead, arguing for a two-phase EKS migration o... |
| 47 | `47-clearhaven-latency-cut-readout.docx` | 46 | 12011 | 24-05-2023 | Meeting notes from the post-cutover readout of Clearhaven Kafka ingestion, capturing measured latency, Helen Cho's month-end hold, the 90-day file-drop emerg... |
| 48 | `48-clearhaven-helm-rollback-runbook.docx` | 42 | 14261 | 29-08-2024 | Internal helm rollback runbook for three Clearhaven production charts. Covers schema preconditions, exact commands, leftover hook and CRD checks, and a worke... |
| 49 | `49-clearhaven-audit-trail-requirements.docx` | 43 | 13871 | 17-11-2022 | Requirements for Clearhaven break-change audit trail: insert-only 7-year store, Helen Cho's export, prohibition on PAN/SSN, and rejection of 30-day applicati... |
| 50 | `50-clearhaven-duplicate-weekend-postmortem.docx` | 47 | 12027 | 16-06-2025 | Blameless incident postmortem for the June 7-8 2025 Clearhaven weekend batch that double-posted 62,104 legs after a manual replay and the Monday catch-up bot... |

Page counts were measured by converting each `.docx` with LibreOffice and reading PDF page counts. Files are 40–48 pages. Word counts are ~11,943–15,370, so well above 150 words per page.

## Full write-ups (copy/paste for question 6–7)

### 1. Oakridge Inventory Position API v1 Requirements

- **File:** `documents/01-oakridge-inventory-api-requirements.docx`
- **Doc ID:** OAK-REQ-2019-014
- **Type:** Requirements document
- **4. Pages:** 43 (LibreOffice), 12801 words
- **6. Description:** Requirements document for the Oakridge inventory position API v1, written so plant ops, the EM, and the implementing engineers share one scope cut after ticket OAK-4412 was reopened.
- **7. Written:** 18-11-2019 (November 18, 2019)
- **Role at the time:** Junior Software Engineer

### 2. Oakridge inventory-api integration guide for new engineers

- **File:** `documents/02-oakridge-new-engineer-integration-guide.docx`
- **Doc ID:** OAK-DOC-2020-003
- **Type:** Integration documentation
- **4. Pages:** 43 (LibreOffice), 11981 words
- **6. Description:** Internal integration guide for Northstar engineers joining the Oakridge inventory-api work, covering VPN, schema, local snapshot, extract path, and ownership.
- **7. Written:** 21-02-2020 (February 21, 2020)
- **Role at the time:** Junior Software Engineer

### 3. Oakridge inventory-api v1 REST design

- **File:** `documents/03-oakridge-inventory-rest-design.docx`
- **Doc ID:** OAK-TDD-2020-002
- **Type:** Technical design
- **4. Pages:** 44 (LibreOffice), 13991 words
- **6. Description:** Technical design for the Oakridge inventory position REST API v1, covering resources, cursors, caching, and failure modes for implementers and reviewers.
- **7. Written:** 09-01-2020 (January 9, 2020)
- **Role at the time:** Junior Software Engineer

### 4. Oakridge inventory API ops kickoff notes

- **File:** `documents/04-oakridge-ops-kickoff-notes.docx`
- **Doc ID:** OAK-MTG-2019-044
- **Type:** Meeting notes
- **4. Pages:** 44 (LibreOffice), 14140 words
- **6. Description:** Decision-oriented kickoff notes for the Oakridge inventory position API, written so a colleague can act without listening to the WebEx recording.
- **7. Written:** 16-10-2019 (October 16, 2019)
- **Role at the time:** Junior Software Engineer

### 5. Oakridge nightly inventory extract SOP

- **File:** `documents/05-oakridge-inventory-extract-sop.docx`
- **Doc ID:** OAK-SOP-2020-011
- **Type:** SOP / runbook
- **4. Pages:** 41 (LibreOffice), 14405 words
- **6. Description:** On-call SOP for the Oakridge nightly inventory extract and replica load, written for a cold 2am run with exact commands and refuse conditions.
- **7. Written:** 12-03-2020 (March 12, 2020)
- **Role at the time:** Junior Software Engineer

### 6. Unified Patient Read API for RapidChart and the ED tracker

- **File:** `documents/06-riverview-unified-patient-api-prd.docx`
- **Doc ID:** RVH-PRD-2020-019
- **Type:** PRD
- **4. Pages:** 44 (LibreOffice), 12164 words
- **6. Description:** Product requirements for the Riverview unified patient read API, written for CMIO, nursing, integration, and Northstar engineering before the RapidChart Flagstaff pilot.
- **7. Written:** 27-08-2020 (August 27, 2020)
- **Role at the time:** Software Engineer

### 7. Identity resolution and record merge for Riverview patient records

- **File:** `documents/07-riverview-identity-merge-design.docx`
- **Doc ID:** RVH-TDD-2021-004
- **Type:** Technical design
- **4. Pages:** 48 (LibreOffice), 11957 words
- **6. Description:** Technical design for Riverview record merge and identity resolution, written for engineering, HIM, and the CMIO liaison before any auto-link is enabled.
- **7. Written:** 14-01-2021 (January 14, 2021)
- **Role at the time:** Software Engineer

### 8. Inflated inpatient census from partial-sync duplicates

- **File:** `documents/08-riverview-inflated-census-incident.docx`
- **Doc ID:** RVH-INC-2021-118
- **Type:** Incident report
- **4. Pages:** 45 (LibreOffice), 11967 words
- **6. Description:** Incident report for the inflated Riverview census counts, written after the Flagstaff bed-board mismatch, covering timeline, impact, root cause, and the dedup fix.
- **7. Written:** 22-06-2021 (June 22, 2021)
- **Role at the time:** Software Engineer

### 9. Patient Chart API test strategy (pytest, recorded fixtures, no PHI in CI)

- **File:** `documents/09-riverview-api-test-strategy.docx`
- **Doc ID:** RVH-QA-2021-007
- **Type:** Test strategy
- **4. Pages:** 48 (LibreOffice), 11994 words
- **6. Description:** QA test strategy for the unified patient read API, written so engineering and Sneha share one fixture policy and so the four pre-staging regressions stay mandatory.
- **7. Written:** 05-03-2021 (March 5, 2021)
- **Role at the time:** Software Engineer

### 10. Leave jenkins-legacy-3 for GitHub Actions on VLAN runners

- **File:** `documents/10-riverview-gha-migration-memo.docx`
- **Doc ID:** RVH-MEM-2021-031
- **Type:** Recommendation memo
- **4. Pages:** 41 (LibreOffice), 13881 words
- **6. Description:** Recommendation memo asking Priya Nair to approve moving Riverview Patient API CI off Jenkins to GitHub Actions with VLAN-hosted runners so PHI fixtures never leave the hospital network.
- **7. Written:** 09-11-2021 (November 9, 2021)
- **Role at the time:** Software Engineer

### 11. patient-api on-call runbook

- **File:** `documents/11-riverview-patient-api-oncall-runbook.docx`
- **Doc ID:** RVH-RB-2021-016
- **Type:** Runbook
- **4. Pages:** 43 (LibreOffice), 12049 words
- **6. Description:** On-call runbook for Riverview patient-api. Written so a Northstar engineer who did not ship the last release can isolate a facility feed, talk to ChartLine on-call, and avoid dumping PHI into Slack at 3am.
- **7. Written:** 30-09-2021 (September 30, 2021)
- **Role at the time:** Software Engineer

### 12. RapidChart clinical feedback, April 13

- **File:** `documents/12-riverview-clinical-feedback-notes.docx`
- **Doc ID:** RVH-MTG-2021-022
- **Type:** Meeting notes
- **4. Pages:** 45 (LibreOffice), 14833 words
- **6. Description:** Meeting notes from a Riverview clinical feedback session on RapidChart assemble behavior. Captures decisions, owners, and the rejected idea of leading with a 'unified API' narrative.
- **7. Written:** 13-04-2021 (April 13, 2021)
- **Role at the time:** Software Engineer

### 13. PHI in logs, traces, and support dumps

- **File:** `documents/13-riverview-phi-logging-sop.docx`
- **Doc ID:** RVH-SOP-2021-009
- **Type:** SOP
- **4. Pages:** 43 (LibreOffice), 13748 words
- **6. Description:** SOP for keeping Riverview PHI out of logs, traces, and Slack. Written for on-call engineers and anyone cutting a support zip.
- **7. Written:** 19-07-2021 (July 19, 2021)
- **Role at the time:** Software Engineer

### 14. FHIR R4 vs purpose-built REST for year one

- **File:** `documents/14-riverview-fhir-vs-rest-design.docx`
- **Doc ID:** RVH-TDD-2020-011
- **Type:** Technical design
- **4. Pages:** 47 (LibreOffice), 13036 words
- **6. Description:** Technical design choosing custom REST over FHIR R4 for Riverview patient-api v1, with constraints, payload math, and a rejected HAPI-on-day-one path.
- **7. Written:** 08-10-2020 (October 8, 2020)
- **Role at the time:** Software Engineer

### 15. Chart assemble requirements, RapidChart opening view

- **File:** `documents/15-riverview-chart-assemble-prd.docx`
- **Doc ID:** RVH-PRD-2021-006
- **Type:** PRD
- **4. Pages:** 47 (LibreOffice), 12935 words
- **6. Description:** PRD for Riverview chart assemble: blocks, latency budget, partial-fill banners, caching, and success metrics tied to nurse time rather than QPS.
- **7. Written:** 18-02-2021 (February 18, 2021)
- **Role at the time:** Software Engineer

### 16. Clearhaven transaction reconciliation platform: end-to-end systems design

- **File:** `documents/16-clearhaven-recon-platform-design.docx`
- **Doc ID:** CLH-TDD-2022-021
- **Type:** Systems design
- **4. Pages:** 45 (LibreOffice), 12004 words
- **6. Description:** Internal systems design for the Clearhaven recon platform. Written so engineering can build ingest-api, match-engine, break-svc, and recon-query, and so Clearhaven ops can sign off on audit and residency constraints.
- **7. Written:** 15-09-2022 (September 15, 2022)
- **Role at the time:** Software Engineer II

### 17. Kafka ingestion redesign for Clearhaven settlement feeds

- **File:** `documents/17-clearhaven-kafka-ingestion-redesign.docx`
- **Doc ID:** CLH-TDD-2023-008
- **Type:** Technical design
- **4. Pages:** 45 (LibreOffice), 12659 words
- **6. Description:** Technical design for the Clearhaven Kafka ingest cutover. Written so ingest-api, match-engine, and SRE can ship CLH-5519 without re-arguing partition count on the change window.
- **7. Written:** 11-04-2023 (April 11, 2023)
- **Role at the time:** Software Engineer II

### 18. URI versioning for Clearhaven recon APIs

- **File:** `documents/18-clearhaven-api-versioning-strategy.docx`
- **Doc ID:** CLH-TDD-2023-017
- **Type:** Technical design
- **4. Pages:** 45 (LibreOffice), 14199 words
- **6. Description:** Technical design for versioning Clearhaven recon HTTP APIs. Written after CLH-INC-2023-061 so engineering, QA, and the TAM have one policy for breaking changes.
- **7. Written:** 03-08-2023 (August 3, 2023)
- **Role at the time:** Software Engineer II

### 19. Runbook: match-engine Kafka consumer lag

- **File:** `documents/19-clearhaven-consumer-lag-runbook.docx`
- **Doc ID:** CLH-RB-2023-012
- **Type:** Runbook
- **4. Pages:** 43 (LibreOffice), 13893 words
- **6. Description:** Operational runbook for Clearhaven match-engine consumer lag. Written for the primary on-call to execute without the author on the call.
- **7. Written:** 20-06-2023 (June 20, 2023)
- **Role at the time:** Software Engineer II

### 20. Incident report: November 14 settlement break after duplicate RailClear file

- **File:** `documents/20-clearhaven-settlement-break-incident.docx`
- **Doc ID:** CLH-INC-2023-204
- **Type:** Incident report
- **4. Pages:** 44 (LibreOffice), 11972 words
- **6. Description:** Incident report for the November 14, 2023 Clearhaven settlement break. Written for engineering, ops, TAM, and control owner so the filename idempotency gap is closed in code and in the window checklist.
- **7. Written:** 16-11-2023 (November 16, 2023)
- **Role at the time:** Software Engineer II

### 21. Stop waiting on 15-minute file drops: subscribe to RailClear bus

- **File:** `documents/21-clearhaven-kafka-vs-filedrop-memo.docx`
- **Doc ID:** CLH-MEM-2023-004
- **Type:** Recommendation memo
- **4. Pages:** 40 (LibreOffice), 14401 words
- **6. Description:** Internal recommendation memo from Aman Kumar to Priya Nair and Marcus Bell comparing three ingest options for Clearhaven recon and taking a position for Kafka on the existing RailClear bus.
- **7. Written:** 07-02-2023 (February 7, 2023)
- **Role at the time:** Software Engineer II

### 22. Daily range partitions for recon.fact_leg and recon.break_header

- **File:** `documents/22-clearhaven-postgres-partitioning-design.docx`
- **Doc ID:** CLH-TDD-2023-011
- **Type:** Technical design
- **4. Pages:** 44 (LibreOffice), 12481 words
- **6. Description:** Technical design for range-partitioning Clearhaven recon fact and break tables in Postgres 13, including indexes, detach-to-cold, query-planner risks, and an 8-second lock-budget migration.
- **7. Written:** 18-05-2023 (May 18, 2023)
- **Role at the time:** Software Engineer II

### 23. Ops replay of a failed ingest batch, no SSH

- **File:** `documents/23-clearhaven-batch-replay-prd.docx`
- **Doc ID:** CLH-PRD-2024-002
- **Type:** PRD
- **4. Pages:** 46 (LibreOffice), 11987 words
- **6. Description:** Product requirements for an ops-facing batch replay action on the Clearhaven recon platform, written by Aman Kumar with Helen Cho as acceptor and Maya Singh's no-edit constraint as a hard out-of-scope.
- **7. Written:** 22-01-2024 (January 22, 2024)
- **Role at the time:** Software Engineer II

### 24. Production deploy for ingest-api, match-engine, and break-svc

- **File:** `documents/24-clearhaven-prod-deploy-sop.docx`
- **Doc ID:** CLH-SOP-2023-019
- **Type:** SOP
- **4. Pages:** 45 (LibreOffice), 11992 words
- **6. Description:** Step-by-step production deploy SOP for Clearhaven recon Helm releases, including freeze windows, canary, error-budget abort, and rollback commands.
- **7. Written:** 14-09-2023 (September 14, 2023)
- **Role at the time:** Software Engineer II

### 25. Q1 2024 recon SLA review

- **File:** `documents/25-clearhaven-sla-review-notes.docx`
- **Doc ID:** CLH-MTG-2024-015
- **Type:** Meeting notes
- **4. Pages:** 46 (LibreOffice), 15370 words
- **6. Description:** Internal meeting notes from the Q1 2024 Clearhaven recon SLA review, capturing decisions, the month-end 7:35 exception, open weekend-scope question, and named action items.
- **7. Written:** 12-03-2024 (March 12, 2024)
- **Role at the time:** Software Engineer II

### 26. Idempotent consumers for settlement ingest

- **File:** `documents/26-clearhaven-idempotent-consumers-design.docx`
- **Doc ID:** CLH-TDD-2023-014
- **Type:** Technical design
- **4. Pages:** 43 (LibreOffice), 11978 words
- **6. Description:** Technical design for idempotent Kafka consumers on the Clearhaven recon ingest path. Written after a week of duplicate exception tickets so the team has one schema, one commit order, and a list of failure modes before Kavya starts the CLH-6012 branch.
- **7. Written:** 06-07-2023 (July 6, 2023)
- **Role at the time:** Software Engineer II

### 27. break-svc renamed status to break_status without a version

- **File:** `documents/27-clearhaven-unversioned-api-incident.docx`
- **Doc ID:** CLH-INC-2023-061
- **Type:** Incident report
- **4. Pages:** 46 (LibreOffice), 11982 words
- **6. Description:** Incident report for the March 22 unversioned field rename on break-svc. Written so Priya has a record for Clearhaven, so Kavya has the review checklist that failed, and so the versioning design has a concrete failure to point at.
- **7. Written:** 28-03-2023 (March 28, 2023)
- **Role at the time:** Software Engineer II

### 28. OpenTelemetry rollout for ingest, match, break, and query

- **File:** `documents/28-clearhaven-otel-rollout-design.docx`
- **Doc ID:** CLH-TDD-2024-006
- **Type:** Technical design
- **4. Pages:** 44 (LibreOffice), 14365 words
- **6. Description:** Technical design for the Clearhaven OpenTelemetry rollout. Written so Diego can size the collector, Kavya can pick agent versus SDK, and Priya can see what we are not buying from Datadog while the trial is still open.
- **7. Written:** 15-02-2024 (February 15, 2024)
- **Role at the time:** Software Engineer II

### 29. Stay on Grafana for metrics. Do not buy Datadog as a platform.

- **File:** `documents/29-clearhaven-datadog-vs-grafana-memo.docx`
- **Doc ID:** CLH-MEM-2024-009
- **Type:** Recommendation memo
- **4. Pages:** 45 (LibreOffice), 12275 words
- **6. Description:** Recommendation memo for Priya Nair on Datadog versus the existing Grafana stack after a six-week trial. Written with trial invoices, cardinality counts, and a backup trigger so we do not reopen the debate every quarter.
- **7. Written:** 09-04-2024 (April 9, 2024)
- **Role at the time:** Software Engineer II

### 30. Dead letter topic for settlement inbound

- **File:** `documents/30-clearhaven-dlq-design.docx`
- **Doc ID:** CLH-TDD-2023-022
- **Type:** Technical design
- **4. Pages:** 46 (LibreOffice), 11970 words
- **6. Description:** Technical design for the settlement inbound dead letter topic and replay path. Written so match-engine owns operations, ingest-svc has a producer contract, and oncall has a depth alert instead of a skip table nobody reads.
- **7. Written:** 12-10-2023 (October 12, 2023)
- **Role at the time:** Software Engineer II

### 31. Match-engine worker OOM runbook for nested RailClear files

- **File:** `documents/31-clearhaven-worker-oom-runbook.docx`
- **Doc ID:** CLH-RB-2024-007
- **Type:** Runbook
- **4. Pages:** 40 (LibreOffice), 12186 words
- **6. Description:** Internal on-call runbook for match-engine OOM on nested RailClear payloads. Written after CLH-INC-2024-091 so SE II and SRE share one set of commands and a hard rule against unbounded memory bumps.
- **7. Written:** 21-05-2024 (May 21, 2024)
- **Role at the time:** Software Engineer II

### 32. Flyway schema migrations on recon Postgres

- **File:** `documents/32-clearhaven-schema-migration-sop.docx`
- **Doc ID:** CLH-SOP-2024-011
- **Type:** SOP
- **4. Pages:** 41 (LibreOffice), 11943 words
- **6. Description:** Standard operating procedure for Flyway migrations against Clearhaven recon Postgres. Written after the June 3 hotfix checksum incident so expand/contract and abort steps live in one place.
- **7. Written:** 18-06-2024 (June 18, 2024)
- **Role at the time:** Software Engineer II

### 33. Historical backfill of 2019-2022 legs into partitioned recon tables

- **File:** `documents/33-clearhaven-spark-backfill-design.docx`
- **Doc ID:** CLH-TDD-2024-014
- **Type:** Technical design
- **4. Pages:** 43 (LibreOffice), 12078 words
- **6. Description:** Technical design for the 2019-2022 Spark backfill onto partitioned recon tables. Written so we do not run a 4.6 billion row load on the OLTP primary and so the DST edge is explicit before Chris starts the job.
- **7. Written:** 23-07-2024 (July 23, 2024)
- **Role at the time:** Software Engineer II

### 34. FY25 capacity for Clearhaven recon: four brokers, not twelve

- **File:** `documents/34-clearhaven-capacity-fy25-memo.docx`
- **Doc ID:** CLH-MEM-2024-018
- **Type:** Capacity planning memo
- **4. Pages:** 43 (LibreOffice), 12426 words
- **6. Description:** Capacity planning memo for Clearhaven recon FY25. Written to kill the 12-broker ask and replace it with 4 brokers, compaction, and Postgres disk, with a do-nothing SLA forecast.
- **7. Written:** 05-09-2024 (September 5, 2024)
- **Role at the time:** Software Engineer II

### 35. gRPC for the match-engine to break-svc open-break path

- **File:** `documents/35-clearhaven-grpc-internal-adr.docx`
- **Doc ID:** CLH-ADR-2024-003
- **Type:** Architecture decision record
- **4. Pages:** 46 (LibreOffice), 11968 words
- **6. Description:** Architecture decision record for putting gRPC on the internal open-break path while leaving REST on recon-query. Accepted. Written so the next protocol argument cites load numbers instead of taste.
- **7. Written:** 14-08-2024 (August 14, 2024)
- **Role at the time:** Software Engineer II

### 36. Load test report: match path at 8.2M and 11.4M daily

- **File:** `documents/36-clearhaven-loadtest-8m-report.docx`
- **Doc ID:** CLH-TST-2024-008
- **Type:** Load test report
- **4. Pages:** 44 (LibreOffice), 12128 words
- **6. Description:** Internal load test report for Clearhaven recon. Written after the October 14-16 shadow runs so Priya and Marcus can decide hardware and so the match team can pick the break-svc work.
- **7. Written:** 17-10-2024 (October 17, 2024)
- **Role at the time:** Software Engineer II

### 37. Runbook: Patroni failover for recon-pg

- **File:** `documents/37-clearhaven-postgres-failover-runbook.docx`
- **Doc ID:** CLH-RB-2024-015
- **Type:** Runbook
- **4. Pages:** 40 (LibreOffice), 13753 words
- **6. Description:** On-call runbook for Clearhaven recon Postgres. Written so a Northstar engineer can promote a replica, point ingest at the new primary, and confirm WAL without waiting for the DBA if Rina is unreachable.
- **7. Written:** 08-11-2024 (November 8, 2024)
- **Role at the time:** Software Engineer II

### 38. Technical design: settlement file landings into Kafka

- **File:** `documents/38-clearhaven-cdc-settlement-design.docx`
- **Doc ID:** CLH-TDD-2023-002
- **Type:** Technical design
- **4. Pages:** 43 (LibreOffice), 14922 words
- **6. Description:** Technical design for Clearhaven settlement ingest. Written to freeze the lister-plus-hash approach and to kill the Debezium proposal before we spent a quarter on a connector with no source database.
- **7. Written:** 19-01-2023 (January 19, 2023)
- **Role at the time:** Software Engineer II

### 39. Architecture review notes: recon API versioning

- **File:** `documents/39-clearhaven-api-versioning-review-notes.docx`
- **Doc ID:** CLH-MTG-2023-041
- **Type:** Meeting notes
- **4. Pages:** 45 (LibreOffice), 12926 words
- **6. Description:** Meeting notes from the July 25 architecture review of Clearhaven ops-api versioning. Written so the URI vs header decision and the /v1 sunset argument are on paper before the August design freezes.
- **7. Written:** 25-07-2023 (July 25, 2023)
- **Role at the time:** Software Engineer II

### 40. Incident report: match-engine rebalance storm, January 8, 2024

- **File:** `documents/40-clearhaven-kafka-rebalance-incident.docx`
- **Doc ID:** CLH-INC-2024-017
- **Type:** Incident report
- **4. Pages:** 45 (LibreOffice), 12682 words
- **6. Description:** Incident report for the January 8 match-engine rebalance storm. Written for Priya, Marcus, and the on-call rotation so the timeout and staging-partition mistakes are not tribal knowledge.
- **7. Written:** 11-01-2024 (January 11, 2024)
- **Role at the time:** Software Engineer II

### 41. Clearhaven Reconciliation On-Call SOP

- **File:** `documents/41-clearhaven-oncall-sop.docx`
- **Doc ID:** CLH-SOP-2023-028
- **Type:** SOP
- **4. Pages:** 44 (LibreOffice), 13686 words
- **6. Description:** Internal SOP for Northstar engineers covering Clearhaven reconciliation production. Written so a tired person at 02:14 ET can decide whether to page, who to call, and what not to deploy.
- **7. Written:** 07-12-2023 (December 7, 2023)
- **Role at the time:** Software Engineer II

### 42. Clearhaven Recon Terraform Modules for AWS

- **File:** `documents/42-clearhaven-terraform-aws-design.docx`
- **Doc ID:** CLH-TDD-2024-009
- **Type:** Technical design
- **4. Pages:** 46 (LibreOffice), 11960 words
- **6. Description:** Technical design for moving Clearhaven recon AWS resources under Terraform modules and a locked apply path. Written for engineers who will import, plan, and apply, and for Priya who needs a one-screen decision.
- **7. Written:** 28-03-2024 (March 28, 2024)
- **Role at the time:** Software Engineer II

### 43. Structured Exception Codes for Reconciliation Breaks

- **File:** `documents/43-clearhaven-exception-codes-prd.docx`
- **Doc ID:** CLH-PRD-2024-021
- **Type:** PRD
- **4. Pages:** 44 (LibreOffice), 12125 words
- **6. Description:** Product requirements for structured recon exception codes, mapping, UI, reporting, and immutable history. Written for engineering, ops, QA, and the Clearhaven compliance reviewer who asked for history in November.
- **7. Written:** 05-12-2024 (December 5, 2024)
- **Role at the time:** Software Engineer II

### 44. Evaluation Rubric for Model-Generated Reconciliation Summaries

- **File:** `documents/44-clearhaven-model-summary-eval-rubric.docx`
- **Doc ID:** CLH-EVAL-2025-003
- **Type:** Evaluation rubric
- **4. Pages:** 45 (LibreOffice), 11959 words
- **6. Description:** Operational evaluation rubric for Northstar engineers scoring model-written Clearhaven recon break summaries. Used in the weekly review queue, not as an academic benchmark.
- **7. Written:** 13-02-2025 (February 13, 2025)
- **Role at the time:** Software Engineer II

### 45. Redis Hot Cache for Reconciliation Match Keys

- **File:** `documents/45-clearhaven-matchkey-redis-design.docx`
- **Doc ID:** CLH-TDD-2024-012
- **Type:** Technical design
- **4. Pages:** 43 (LibreOffice), 14198 words
- **6. Description:** Technical design for a Redis hot cache of Clearhaven recon match keys. Written for the people who will implement the client, size the box, and sit the incident when Redis dies during the window.
- **7. Written:** 02-05-2024 (May 2, 2024)
- **Role at the time:** Software Engineer II

### 46. Move match-engine off the 2021 EC2 worker AMIs onto EKS

- **File:** `documents/46-clearhaven-k8s-compute-memo.docx`
- **Doc ID:** CLH-MEM-2023-027
- **Type:** Recommendation memo
- **4. Pages:** 47 (LibreOffice), 12036 words
- **6. Description:** Internal recommendation memo from Software Engineer II Aman Kumar to the Clearhaven engineering manager and SRE lead, arguing for a two-phase EKS migration of match-engine compute and rejecting an AMI-in-DaemonSet shortcut.
- **7. Written:** 02-11-2023 (November 2, 2023)
- **Role at the time:** Software Engineer II

### 47. Kafka ingestion readout: 40 min to ~9 min, month-end still open

- **File:** `documents/47-clearhaven-latency-cut-readout.docx`
- **Doc ID:** CLH-MTG-2023-028
- **Type:** Meeting notes
- **4. Pages:** 46 (LibreOffice), 12011 words
- **6. Description:** Meeting notes from the post-cutover readout of Clearhaven Kafka ingestion, capturing measured latency, Helen Cho's month-end hold, the 90-day file-drop emergency path, and open work on RailClear dual-write.
- **7. Written:** 24-05-2023 (May 24, 2023)
- **Role at the time:** Software Engineer II

### 48. Helm rollback for match-engine, ingest-api, and break-svc

- **File:** `documents/48-clearhaven-helm-rollback-runbook.docx`
- **Doc ID:** CLH-RB-2024-011
- **Type:** Runbook
- **4. Pages:** 42 (LibreOffice), 14261 words
- **6. Description:** Internal helm rollback runbook for three Clearhaven production charts. Covers schema preconditions, exact commands, leftover hook and CRD checks, and a worked example from the January 2024 rebalance incident.
- **7. Written:** 29-08-2024 (August 29, 2024)
- **Role at the time:** Software Engineer II

### 49. Audit trail for break changes: who, when, before/after, ticket id

- **File:** `documents/49-clearhaven-audit-trail-requirements.docx`
- **Doc ID:** CLH-REQ-2022-033
- **Type:** Requirements document
- **4. Pages:** 43 (LibreOffice), 13871 words
- **6. Description:** Requirements for Clearhaven break-change audit trail: insert-only 7-year store, Helen Cho's export, prohibition on PAN/SSN, and rejection of 30-day application logs as the control.
- **7. Written:** 17-11-2022 (November 17, 2022)
- **Role at the time:** Software Engineer II

### 50. Weekend batch June 7-8 posted duplicate legs: replay and Monday catch-up both ran

- **File:** `documents/50-clearhaven-duplicate-weekend-postmortem.docx`
- **Doc ID:** CLH-INC-2025-088
- **Type:** Incident postmortem
- **4. Pages:** 47 (LibreOffice), 12027 words
- **6. Description:** Blameless incident postmortem for the June 7-8 2025 Clearhaven weekend batch that double-posted 62,104 legs after a manual replay and the Monday catch-up both ran. Impact was exception-queue noise; cash was held.
- **7. Written:** 16-06-2025 (June 16, 2025)
- **Role at the time:** Software Engineer II
