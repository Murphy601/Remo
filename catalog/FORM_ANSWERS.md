# Form answers (per document)

These answers map to the intake questions for the 50 internal engineering documents in documents/.

Direct file links: [DOWNLOADS.md](../DOWNLOADS.md). All 50 as a zip: [documents.zip](../documents.zip).

## Answers that are the same for every file

1. **Current or most recent job title:** Web Developer
2. **Years of professional experience:** 5–10 (about six years, freelance 2020–present)
3. **Field:** Software Engineering / Data Science
4. **Pages:** 42–50 (counted with LibreOffice Writer → PDF)

Author on every document: Michael Gilfilian, Web Developer, Hillcrest Digital. Engagements covered: Harbor & Oak Outfitters, Lakeshore Hardware Group, and a 2023 IT support internship at Whetstone Industrial.

## Per-document answers (questions 4–7)

| # | File | Pages | Words | Written | Description |
|---|---|---|---|---|---|
| 1 | `01-whetstone-azure-mailbox-requirements.docx` | 43 | 12838 | 14-03-2023 | Requirements cut for moving Whetstone user mailboxes to Exchange Online so IT, HRIS, and the intern share one scope after WTS-4418 was reopened. |
| 2 | `02-whetstone-ticket-triage-design.docx` | 43 | 14174 | 04-04-2023 | Technical design for a Python helpdesk triage bot at Whetstone, written so Carla Nguyen and Brett Holtz share one classifier cut before WTS-4502 is built. |
| 3 | `03-whetstone-imaging-sop.docx` | 43 | 14626 | 21-04-2023 | On-bench SOP for imaging Whetstone shop-floor laptops from the Intune golden, written for a cold run with exact commands and refuse conditions. |
| 4 | `04-whetstone-aad-duplicate-incident.docx` | 43 | 14516 | 18-04-2023 | Incident report for duplicate Azure AD accounts after an HRIS feed retry, covering timeline, impact, and the refuse on auto-merge. |
| 5 | `05-whetstone-azure-kickoff-notes.docx` | 43 | 14981 | 09-02-2023 | Decision-oriented kickoff notes for Whetstone Azure mailbox and identity work, written so a colleague can act without the recording. |
| 6 | `06-whetstone-fileshare-memo.docx` | 43 | 12271 | 28-03-2023 | Recommendation memo asking Brett Holtz to approve Azure Files for three Whetstone shares and to refuse the IaaS file-server quote. |
| 7 | `07-whetstone-vpn-mfa-runbook.docx` | 43 | 13997 | 11-04-2023 | On-call runbook for Whetstone plant VPN with MFA, written so a desk person who did not set it up can diagnose a failed login without waking Brett. |
| 8 | `08-whetstone-imaging-test-notes.docx` | 43 | 14203 | 02-05-2023 | Acceptance notes for the Whetstone Windows 11 golden image, written so Owen and the intern share one pass/fail list before the golden is marked current. |
| 9 | `09-harbor-shopify-theme-requirements.docx` | 43 | 14128 | 18-06-2020 | Requirements for the Harbor & Oak Shopify theme v1, written so Dana, Jenna, and the developer share one template cut after HBR-1104. |
| 10 | `10-harbor-liquid-theme-design.docx` | 46 | 11996 | 04-08-2020 | Technical design for the Harbor & Oak Liquid theme, covering sections, metafields, and a pickup stub that will survive a checkout change. |
| 11 | `11-harbor-seo-90day-notes.docx` | 46 | 11980 | 12-03-2021 | Decision notes from the Harbor & Oak 90-day SEO review, capturing the title pattern, collection index, and the refuse on city stuffing. |
| 12 | `12-harbor-mothers-day-checkout-incident.docx` | 43 | 14368 | 11-05-2021 | Incident report for the Harbor & Oak Mother's Day checkout stall caused by a gift-wrap app 429, including timeline and the refuse on retries. |
| 13 | `13-harbor-local-pickup-prd.docx` | 45 | 12010 | 22-07-2021 | Product requirements for Harbor & Oak local pickup, written for Dana, Evan, and the developer before the rate is turned on. |
| 14 | `14-harbor-shopify-deploy-runbook.docx` | 43 | 14175 | 16-09-2021 | Deploy runbook for the Harbor & Oak Shopify theme, written so a cold publish does not hide pickup and so rollback is unpublish. |
| 15 | `15-harbor-inventory-sync-design.docx` | 42 | 14347 | 09-11-2021 | Systems design for Harbor & Oak inventory sync, choosing a 15-minute POS poll over a live vendor webhook. |
| 16 | `16-harbor-shopify-vs-react-memo.docx` | 43 | 12251 | 07-12-2021 | Recommendation memo telling Dana Whitlock to stay on Shopify for the Harbor & Oak storefront and to refuse a custom React rebuild. |
| 17 | `17-harbor-product-photo-notes.docx` | 43 | 15019 | 14-12-2021 | Meeting notes locking Harbor & Oak product photo rules: size, format, alt text, and the refuse on uncompressed lifestyle galleries. |
| 18 | `18-harbor-csv-load-sop.docx` | 43 | 14073 | 17-02-2022 | SOP for loading Harbor & Oak product CSVs, with a hard stop on blank SKUs and a dry-run count before any write. |
| 19 | `19-harbor-ga4-double-count-incident.docx` | 44 | 12006 | 08-03-2022 | Incident report for Harbor & Oak GA4 double-counted purchases after the theme pixel and GTM both fired, with the one-pixel cut. |
| 20 | `20-harbor-email-tool-design.docx` | 43 | 14448 | 26-04-2022 | Technical design for Harbor & Oak abandoned-cart email, choosing Klaviyo with pickup and POS suppress over a custom Node sender. |
| 21 | `21-harbor-gift-card-prd.docx` | 43 | 14143 | 09-06-2022 | PRD for Harbor & Oak gift cards with a single Shopify ledger for in-store sale and online redeem, refusing a second-ledger app. |
| 22 | `22-harbor-checkout-test-strategy.docx` | 43 | 12916 | 21-07-2022 | Checkout test strategy for Harbor & Oak, locking block-merge cases for pickup, wrap-off, gift card, and a single GA4 purchase event. |
| 23 | `23-harbor-owner-integration-guide.docx` | 43 | 12822 | 25-08-2022 | Owner integration guide for Harbor & Oak: pickup shelf, product CSV, theme preview, and who to contact, written so Dana does not need a wiki. |
| 24 | `24-harbor-wholesale-requirements.docx` | 43 | 12707 | 13-10-2022 | Requirements for Harbor & Oak wholesale v1: a hidden catalog and 11 tagged accounts, refusing a paid B2B app. |
| 25 | `25-lakeshore-inventory-api-requirements.docx` | 43 | 12710 | 22-09-2022 | Requirements for the Lakeshore inventory position API v1, written so store ops and the developer share one scope after LSH-4401. |
| 26 | `26-lakeshore-inventory-rest-design.docx` | 43 | 12722 | 03-11-2022 | REST design for the Lakeshore inventory API: storeId as CHAR(2), cursors, timeout, and 503 on replica lag. |
| 27 | `27-lakeshore-four-store-systems-design.docx` | 45 | 11955 | 15-12-2022 | Systems design for Lakeshore four-store stock: POS as source, API in the middle, Woo as a projection, no pooled bin. |
| 28 | `28-lakeshore-nightly-stock-runbook.docx` | 43 | 14635 | 16-02-2023 | On-call runbook for the Lakeshore nightly Woo stock projection, with checksum, zero-row paging, and a refuse on laptop reruns. |
| 29 | `29-lakeshore-negative-onhand-incident.docx` | 43 | 12008 | 16-03-2023 | Incident report for Lakeshore negative on-hand after overlapping stock jobs, with clamp, lock, and the refuse on auto-backorder. |
| 30 | `30-lakeshore-store-pickup-prd.docx` | 43 | 12504 | 04-05-2023 | PRD for Lakeshore four-store pickup: store picker, per-store quantity, 15:30 cutoff, no transfer-as-pickup. |
| 31 | `31-lakeshore-woo-deploy-sop.docx` | 43 | 12059 | 22-06-2023 | Deploy SOP for four Lakeshore WooCommerce storefronts, blocking live wp-admin plugin updates after the May 18 pickup hide. |
| 32 | `32-lakeshore-mongo-vs-mysql-memo.docx` | 50 | 12013 | 10-08-2023 | Recommendation memo keeping Lakeshore on-hand in MySQL and refusing a Mongo stock ledger after a contractor suggestion. |
| 33 | `33-lakeshore-store-manager-notes.docx` | 46 | 11974 | 14-09-2023 | Store manager feedback notes for Lakeshore pickup, negative quantity, and weekend coverage, with owners and refused paths. |
| 34 | `34-lakeshore-react-admin-design.docx` | 48 | 11966 | 26-10-2023 | Technical design for a React stock admin at Lakeshore that reads the inventory API and never writes Woo from the browser. |
| 35 | `35-lakeshore-docker-vs-k8s-memo.docx` | 43 | 14502 | 18-01-2024 | Recommendation memo keeping Lakeshore WooCommerce on Docker Compose and Kubernetes only for inventory-api, refusing a four-site Helm move. |
| 36 | `36-lakeshore-tls-cert-incident.docx` | 43 | 12012 | 12-02-2024 | Incident report for an expired TLS certificate on the Lakeshore pickup host, with renew windows and a refuse on an uninventoried wildcard. |
| 37 | `37-lakeshore-aws-capacity-memo.docx` | 43 | 12095 | 07-03-2024 | Capacity memo for Lakeshore inventory-api on AWS, refusing a larger instance after a weekend graph that was Woo PHP, not the API. |
| 38 | `38-lakeshore-react-vs-wp-adr.docx` | 49 | 12036 | 02-04-2024 | Architecture decision record keeping Lakeshore public storefronts on WooCommerce and the stock admin on React, with Luis as acceptor. |
| 39 | `39-lakeshore-weekend-sale-load-test.docx` | 47 | 12022 | 28-05-2024 | Load test report for the Lakeshore Memorial Day sale soak at 2.4x Tuesday traffic, with fail gates and a refuse on 1x soak. |
| 40 | `40-lakeshore-mysql-migration-sop.docx` | 43 | 13913 | 11-07-2024 | SOP for Lakeshore inventory MySQL schema changes using expand/contract, an 8 second lock budget, and no same-release column drop. |
| 41 | `41-lakeshore-oncall-sop.docx` | 48 | 11965 | 22-08-2024 | On-call SOP for Lakeshore inventory-api and Woo projection, with named tells and a refuse on 'check Grafana' page bodies. |
| 42 | `42-lakeshore-aws-terraform-design.docx` | 43 | 12880 | 19-09-2024 | Terraform design for Lakeshore inventory-api on AWS: four modules, stg/prod workspaces, one account, no 4k-line main.tf. |
| 43 | `43-lakeshore-pos-exception-prd.docx` | 47 | 12031 | 16-01-2025 | PRD mapping Lakeshore POS stock-mismatch exceptions to six shared codes with cashier sentences, refusing raw HTTP status on the till. |
| 44 | `44-lakeshore-seo-copy-rubric.docx` | 49 | 12016 | 20-02-2025 | Evaluation rubric for Lakeshore category copy and titles, failing city stuffing and locking a product-category-store pattern. |
| 45 | `45-lakeshore-redis-stock-design.docx` | 42 | 14770 | 13-03-2025 | Technical design for a Redis cache in front of Lakeshore on-hand reads, with a 45s TTL and fail-open to MySQL instead of stale-as-fresh. |
| 46 | `46-lakeshore-weekend-double-charge-postmortem.docx` | 43 | 14266 | 10-04-2025 | Postmortem for Lakeshore weekend double-charges on prepaid pickup, covering the missing idempotency key, 11 refunds, and the refuse on laptop capture retries. |
| 47 | `47-hillcrest-client-onboard-sop.docx` | 43 | 12011 | 13-06-2024 | SOP for onboarding a Hillcrest Digital web client: access, staging host, ticket prefix, first deploy window, and a refuse on Slack password paste. |
| 48 | `48-hillcrest-secrets-access-sop.docx` | 43 | 14871 | 25-07-2024 | SOP for Hillcrest Digital secrets and access: per-client vaults, seven-day expiry after pause, logged break-glass, no secrets in tickets. |
| 49 | `49-hillcrest-staging-per-client-design.docx` | 43 | 13643 | 06-02-2025 | Technical design for per-client Hillcrest staging hosts, refusing a shared preview after a Harbor/Lakeshore leftover mix. |
| 50 | `50-hillcrest-q3-pipeline-notes.docx` | 43 | 14795 | 07-08-2025 | Q3 pipeline notes for Hillcrest Digital: Lakeshore active work, Harbor maintenance, one new onboard maximum, and a refuse on two first-publishes in one week. |

Page counts were measured by converting each `.docx` with LibreOffice and reading PDF page counts. Files are 42–50 pages. Word counts are ~11,955–15,019, so well above 150 words per page.

## Full write-ups (copy/paste for question 6–7)

### 1. Whetstone mailbox cutover to Exchange Online, v1 requirements

- **File:** `documents/01-whetstone-azure-mailbox-requirements.docx`
- **Doc ID:** WTS-REQ-2023-011
- **Type:** Requirements document
- **Form type (dropdown):** Requirements doc
- **4. Pages:** 43 (LibreOffice), 12838 words
- **6. Description:** Requirements cut for moving Whetstone user mailboxes to Exchange Online so IT, HRIS, and the intern share one scope after WTS-4418 was reopened.
- **7. Written:** 14-03-2023 (March 14, 2023)
- **Role at the time:** IT Support Intern

### 2. Helpdesk ticket triage bot, technical design

- **File:** `documents/02-whetstone-ticket-triage-design.docx`
- **Doc ID:** WTS-TDD-2023-018
- **Type:** Technical design document
- **Form type (dropdown):** Technical design doc
- **4. Pages:** 43 (LibreOffice), 14174 words
- **6. Description:** Technical design for a Python helpdesk triage bot at Whetstone, written so Carla Nguyen and Brett Holtz share one classifier cut before WTS-4502 is built.
- **7. Written:** 04-04-2023 (April 4, 2023)
- **Role at the time:** IT Support Intern

### 3. Windows 11 golden-image SOP for shop-floor laptops

- **File:** `documents/03-whetstone-imaging-sop.docx`
- **Doc ID:** WTS-SOP-2023-022
- **Type:** Runbook / SOP
- **Form type (dropdown):** Runbook / SOPs
- **4. Pages:** 43 (LibreOffice), 14626 words
- **6. Description:** On-bench SOP for imaging Whetstone shop-floor laptops from the Intune golden, written for a cold run with exact commands and refuse conditions.
- **7. Written:** 21-04-2023 (April 21, 2023)
- **Role at the time:** IT Support Intern

### 4. Incident: duplicate Azure AD accounts after HRIS feed retry

- **File:** `documents/04-whetstone-aad-duplicate-incident.docx`
- **Doc ID:** WTS-INC-2023-031
- **Type:** Incident report
- **Form type (dropdown):** Incident report
- **4. Pages:** 43 (LibreOffice), 14516 words
- **6. Description:** Incident report for duplicate Azure AD accounts after an HRIS feed retry, covering timeline, impact, and the refuse on auto-merge.
- **7. Written:** 18-04-2023 (April 18, 2023)
- **Role at the time:** IT Support Intern

### 5. Azure mailbox and identity kickoff notes, February 9

- **File:** `documents/05-whetstone-azure-kickoff-notes.docx`
- **Doc ID:** WTS-MTG-2023-007
- **Type:** Meeting notes
- **Form type (dropdown):** Other
- **4. Pages:** 43 (LibreOffice), 14981 words
- **6. Description:** Decision-oriented kickoff notes for Whetstone Azure mailbox and identity work, written so a colleague can act without the recording.
- **7. Written:** 09-02-2023 (February 9, 2023)
- **Role at the time:** IT Support Intern

### 6. Memo: stop lifting fs01 into a Windows VM in Azure

- **File:** `documents/06-whetstone-fileshare-memo.docx`
- **Doc ID:** WTS-MEM-2023-014
- **Type:** Recommendation memo
- **Form type (dropdown):** Other
- **4. Pages:** 43 (LibreOffice), 12271 words
- **6. Description:** Recommendation memo asking Brett Holtz to approve Azure Files for three Whetstone shares and to refuse the IaaS file-server quote.
- **7. Written:** 28-03-2023 (March 28, 2023)
- **Role at the time:** IT Support Intern

### 7. Runbook: plant VPN with MFA, no trusted-subnet exception

- **File:** `documents/07-whetstone-vpn-mfa-runbook.docx`
- **Doc ID:** WTS-RB-2023-019
- **Type:** Runbook / SOP
- **Form type (dropdown):** Runbook / SOPs
- **4. Pages:** 43 (LibreOffice), 13997 words
- **6. Description:** On-call runbook for Whetstone plant VPN with MFA, written so a desk person who did not set it up can diagnose a failed login without waking Brett.
- **7. Written:** 11-04-2023 (April 11, 2023)
- **Role at the time:** IT Support Intern

### 8. Imaging acceptance notes, four shop-floor SKUs

- **File:** `documents/08-whetstone-imaging-test-notes.docx`
- **Doc ID:** WTS-TST-2023-024
- **Type:** Test strategy notes
- **Form type (dropdown):** Other
- **4. Pages:** 43 (LibreOffice), 14203 words
- **6. Description:** Acceptance notes for the Whetstone Windows 11 golden image, written so Owen and the intern share one pass/fail list before the golden is marked current.
- **7. Written:** 02-05-2023 (May 2, 2023)
- **Role at the time:** IT Support Intern

### 9. Harbor & Oak Shopify theme v1 requirements

- **File:** `documents/09-harbor-shopify-theme-requirements.docx`
- **Doc ID:** HBR-REQ-2020-008
- **Type:** Requirements document
- **Form type (dropdown):** Requirements doc
- **4. Pages:** 43 (LibreOffice), 14128 words
- **6. Description:** Requirements for the Harbor & Oak Shopify theme v1, written so Dana, Jenna, and the developer share one template cut after HBR-1104.
- **7. Written:** 18-06-2020 (June 18, 2020)
- **Role at the time:** Web Developer

### 10. Harbor & Oak Liquid theme design

- **File:** `documents/10-harbor-liquid-theme-design.docx`
- **Doc ID:** HBR-TDD-2020-021
- **Type:** Technical design document
- **Form type (dropdown):** Technical design doc
- **4. Pages:** 46 (LibreOffice), 11996 words
- **6. Description:** Technical design for the Harbor & Oak Liquid theme, covering sections, metafields, and a pickup stub that will survive a checkout change.
- **7. Written:** 04-08-2020 (August 4, 2020)
- **Role at the time:** Web Developer

### 11. Harbor & Oak SEO 90-day notes, March 12

- **File:** `documents/11-harbor-seo-90day-notes.docx`
- **Doc ID:** HBR-MTG-2021-033
- **Type:** Meeting notes
- **Form type (dropdown):** Other
- **4. Pages:** 46 (LibreOffice), 11980 words
- **6. Description:** Decision notes from the Harbor & Oak 90-day SEO review, capturing the title pattern, collection index, and the refuse on city stuffing.
- **7. Written:** 12-03-2021 (March 12, 2021)
- **Role at the time:** Web Developer

### 12. Incident: Mother's Day checkout 429 on gift-wrap app

- **File:** `documents/12-harbor-mothers-day-checkout-incident.docx`
- **Doc ID:** HBR-INC-2021-044
- **Type:** Incident report
- **Form type (dropdown):** Incident report
- **4. Pages:** 43 (LibreOffice), 14368 words
- **6. Description:** Incident report for the Harbor & Oak Mother's Day checkout stall caused by a gift-wrap app 429, including timeline and the refuse on retries.
- **7. Written:** 11-05-2021 (May 11, 2021)
- **Role at the time:** Web Developer

### 13. PRD: Harbor & Oak local pickup

- **File:** `documents/13-harbor-local-pickup-prd.docx`
- **Doc ID:** HBR-PRD-2021-052
- **Type:** Product requirements document
- **Form type (dropdown):** Product requirements doc
- **4. Pages:** 45 (LibreOffice), 12010 words
- **6. Description:** Product requirements for Harbor & Oak local pickup, written for Dana, Evan, and the developer before the rate is turned on.
- **7. Written:** 22-07-2021 (July 22, 2021)
- **Role at the time:** Web Developer

### 14. Runbook: Harbor & Oak Shopify theme deploy

- **File:** `documents/14-harbor-shopify-deploy-runbook.docx`
- **Doc ID:** HBR-RB-2021-061
- **Type:** Runbook / SOP
- **Form type (dropdown):** Runbook / SOPs
- **4. Pages:** 43 (LibreOffice), 14175 words
- **6. Description:** Deploy runbook for the Harbor & Oak Shopify theme, written so a cold publish does not hide pickup and so rollback is unpublish.
- **7. Written:** 16-09-2021 (September 16, 2021)
- **Role at the time:** Web Developer

### 15. Harbor & Oak inventory sync, systems design

- **File:** `documents/15-harbor-inventory-sync-design.docx`
- **Doc ID:** HBR-SYS-2021-070
- **Type:** Systems design document
- **Form type (dropdown):** Systems design doc
- **4. Pages:** 42 (LibreOffice), 14347 words
- **6. Description:** Systems design for Harbor & Oak inventory sync, choosing a 15-minute POS poll over a live vendor webhook.
- **7. Written:** 09-11-2021 (November 9, 2021)
- **Role at the time:** Web Developer

### 16. Memo: stay on Shopify for storefront, React only for admin later

- **File:** `documents/16-harbor-shopify-vs-react-memo.docx`
- **Doc ID:** HBR-MEM-2021-077
- **Type:** Recommendation memo
- **Form type (dropdown):** Other
- **4. Pages:** 43 (LibreOffice), 12251 words
- **6. Description:** Recommendation memo telling Dana Whitlock to stay on Shopify for the Harbor & Oak storefront and to refuse a custom React rebuild.
- **7. Written:** 07-12-2021 (December 7, 2021)
- **Role at the time:** Web Developer

### 17. Product photo pipeline notes, December 14

- **File:** `documents/17-harbor-product-photo-notes.docx`
- **Doc ID:** HBR-MTG-2021-081
- **Type:** Meeting notes
- **Form type (dropdown):** Other
- **4. Pages:** 43 (LibreOffice), 15019 words
- **6. Description:** Meeting notes locking Harbor & Oak product photo rules: size, format, alt text, and the refuse on uncompressed lifestyle galleries.
- **7. Written:** 14-12-2021 (December 14, 2021)
- **Role at the time:** Web Developer

### 18. SOP: Harbor & Oak product CSV load

- **File:** `documents/18-harbor-csv-load-sop.docx`
- **Doc ID:** HBR-SOP-2022-012
- **Type:** Runbook / SOP
- **Form type (dropdown):** Runbook / SOPs
- **4. Pages:** 43 (LibreOffice), 14073 words
- **6. Description:** SOP for loading Harbor & Oak product CSVs, with a hard stop on blank SKUs and a dry-run count before any write.
- **7. Written:** 17-02-2022 (February 17, 2022)
- **Role at the time:** Web Developer

### 19. Incident: GA4 double-count after theme and app both fired purchase

- **File:** `documents/19-harbor-ga4-double-count-incident.docx`
- **Doc ID:** HBR-INC-2022-019
- **Type:** Incident report
- **Form type (dropdown):** Incident report
- **4. Pages:** 44 (LibreOffice), 12006 words
- **6. Description:** Incident report for Harbor & Oak GA4 double-counted purchases after the theme pixel and GTM both fired, with the one-pixel cut.
- **7. Written:** 08-03-2022 (March 8, 2022)
- **Role at the time:** Web Developer

### 20. Harbor & Oak abandoned-cart email design

- **File:** `documents/20-harbor-email-tool-design.docx`
- **Doc ID:** HBR-TDD-2022-028
- **Type:** Technical design document
- **Form type (dropdown):** Technical design doc
- **4. Pages:** 43 (LibreOffice), 14448 words
- **6. Description:** Technical design for Harbor & Oak abandoned-cart email, choosing Klaviyo with pickup and POS suppress over a custom Node sender.
- **7. Written:** 26-04-2022 (April 26, 2022)
- **Role at the time:** Web Developer

### 21. PRD: Harbor & Oak gift cards, in-store and online

- **File:** `documents/21-harbor-gift-card-prd.docx`
- **Doc ID:** HBR-PRD-2022-034
- **Type:** Product requirements document
- **Form type (dropdown):** Product requirements doc
- **4. Pages:** 43 (LibreOffice), 14143 words
- **6. Description:** PRD for Harbor & Oak gift cards with a single Shopify ledger for in-store sale and online redeem, refusing a second-ledger app.
- **7. Written:** 09-06-2022 (June 9, 2022)
- **Role at the time:** Web Developer

### 22. Harbor & Oak checkout test strategy

- **File:** `documents/22-harbor-checkout-test-strategy.docx`
- **Doc ID:** HBR-TST-2022-041
- **Type:** Test strategy
- **Form type (dropdown):** Other
- **4. Pages:** 43 (LibreOffice), 12916 words
- **6. Description:** Checkout test strategy for Harbor & Oak, locking block-merge cases for pickup, wrap-off, gift card, and a single GA4 purchase event.
- **7. Written:** 21-07-2022 (July 21, 2022)
- **Role at the time:** Web Developer

### 23. Harbor & Oak owner integration guide

- **File:** `documents/23-harbor-owner-integration-guide.docx`
- **Doc ID:** HBR-DOC-2022-048
- **Type:** Integration guide
- **Form type (dropdown):** Other
- **4. Pages:** 43 (LibreOffice), 12822 words
- **6. Description:** Owner integration guide for Harbor & Oak: pickup shelf, product CSV, theme preview, and who to contact, written so Dana does not need a wiki.
- **7. Written:** 25-08-2022 (August 25, 2022)
- **Role at the time:** Web Developer

### 24. Harbor & Oak wholesale v1 requirements

- **File:** `documents/24-harbor-wholesale-requirements.docx`
- **Doc ID:** HBR-REQ-2022-055
- **Type:** Requirements document
- **Form type (dropdown):** Requirements doc
- **4. Pages:** 43 (LibreOffice), 12707 words
- **6. Description:** Requirements for Harbor & Oak wholesale v1: a hidden catalog and 11 tagged accounts, refusing a paid B2B app.
- **7. Written:** 13-10-2022 (October 13, 2022)
- **Role at the time:** Web Developer

### 25. Lakeshore inventory position API v1 requirements

- **File:** `documents/25-lakeshore-inventory-api-requirements.docx`
- **Doc ID:** LSH-REQ-2022-014
- **Type:** Requirements document
- **Form type (dropdown):** Requirements doc
- **4. Pages:** 43 (LibreOffice), 12710 words
- **6. Description:** Requirements for the Lakeshore inventory position API v1, written so store ops and the developer share one scope after LSH-4401.
- **7. Written:** 22-09-2022 (September 22, 2022)
- **Role at the time:** Web Developer

### 26. Lakeshore inventory API REST design

- **File:** `documents/26-lakeshore-inventory-rest-design.docx`
- **Doc ID:** LSH-TDD-2022-022
- **Type:** Technical design document
- **Form type (dropdown):** Technical design doc
- **4. Pages:** 43 (LibreOffice), 12722 words
- **6. Description:** REST design for the Lakeshore inventory API: storeId as CHAR(2), cursors, timeout, and 503 on replica lag.
- **7. Written:** 03-11-2022 (November 3, 2022)
- **Role at the time:** Web Developer

### 27. Lakeshore four-store stock path, systems design

- **File:** `documents/27-lakeshore-four-store-systems-design.docx`
- **Doc ID:** LSH-SYS-2022-031
- **Type:** Systems design document
- **Form type (dropdown):** Systems design doc
- **4. Pages:** 45 (LibreOffice), 11955 words
- **6. Description:** Systems design for Lakeshore four-store stock: POS as source, API in the middle, Woo as a projection, no pooled bin.
- **7. Written:** 15-12-2022 (December 15, 2022)
- **Role at the time:** Web Developer

### 28. Runbook: Lakeshore nightly stock projection to Woo

- **File:** `documents/28-lakeshore-nightly-stock-runbook.docx`
- **Doc ID:** LSH-RB-2023-008
- **Type:** Runbook / SOP
- **Form type (dropdown):** Runbook / SOPs
- **4. Pages:** 43 (LibreOffice), 14635 words
- **6. Description:** On-call runbook for the Lakeshore nightly Woo stock projection, with checksum, zero-row paging, and a refuse on laptop reruns.
- **7. Written:** 16-02-2023 (February 16, 2023)
- **Role at the time:** Web Developer

### 29. Incident: negative on-hand after overlapping stock jobs

- **File:** `documents/29-lakeshore-negative-onhand-incident.docx`
- **Doc ID:** LSH-INC-2023-017
- **Type:** Incident report
- **Form type (dropdown):** Incident report
- **4. Pages:** 43 (LibreOffice), 12008 words
- **6. Description:** Incident report for Lakeshore negative on-hand after overlapping stock jobs, with clamp, lock, and the refuse on auto-backorder.
- **7. Written:** 16-03-2023 (March 16, 2023)
- **Role at the time:** Web Developer

### 30. PRD: Lakeshore store pickup across four stores

- **File:** `documents/30-lakeshore-store-pickup-prd.docx`
- **Doc ID:** LSH-PRD-2023-026
- **Type:** Product requirements document
- **Form type (dropdown):** Product requirements doc
- **4. Pages:** 43 (LibreOffice), 12504 words
- **6. Description:** PRD for Lakeshore four-store pickup: store picker, per-store quantity, 15:30 cutoff, no transfer-as-pickup.
- **7. Written:** 04-05-2023 (May 4, 2023)
- **Role at the time:** Web Developer

### 31. SOP: WooCommerce deploy for four Lakeshore storefronts

- **File:** `documents/31-lakeshore-woo-deploy-sop.docx`
- **Doc ID:** LSH-SOP-2023-033
- **Type:** Runbook / SOP
- **Form type (dropdown):** Runbook / SOPs
- **4. Pages:** 43 (LibreOffice), 12059 words
- **6. Description:** Deploy SOP for four Lakeshore WooCommerce storefronts, blocking live wp-admin plugin updates after the May 18 pickup hide.
- **7. Written:** 22-06-2023 (June 22, 2023)
- **Role at the time:** Web Developer

### 32. Memo: keep MySQL for stock, Mongo only for catalog extras

- **File:** `documents/32-lakeshore-mongo-vs-mysql-memo.docx`
- **Doc ID:** LSH-MEM-2023-041
- **Type:** Recommendation memo
- **Form type (dropdown):** Other
- **4. Pages:** 50 (LibreOffice), 12013 words
- **6. Description:** Recommendation memo keeping Lakeshore on-hand in MySQL and refusing a Mongo stock ledger after a contractor suggestion.
- **7. Written:** 10-08-2023 (August 10, 2023)
- **Role at the time:** Web Developer

### 33. Store manager feedback notes, September 14

- **File:** `documents/33-lakeshore-store-manager-notes.docx`
- **Doc ID:** LSH-MTG-2023-049
- **Type:** Meeting notes
- **Form type (dropdown):** Other
- **4. Pages:** 46 (LibreOffice), 11974 words
- **6. Description:** Store manager feedback notes for Lakeshore pickup, negative quantity, and weekend coverage, with owners and refused paths.
- **7. Written:** 14-09-2023 (September 14, 2023)
- **Role at the time:** Web Developer

### 34. Lakeshore React stock admin, technical design

- **File:** `documents/34-lakeshore-react-admin-design.docx`
- **Doc ID:** LSH-TDD-2023-058
- **Type:** Technical design document
- **Form type (dropdown):** Technical design doc
- **4. Pages:** 48 (LibreOffice), 11966 words
- **6. Description:** Technical design for a React stock admin at Lakeshore that reads the inventory API and never writes Woo from the browser.
- **7. Written:** 26-10-2023 (October 26, 2023)
- **Role at the time:** Web Developer

### 35. Memo: Docker Compose for Woo, Kubernetes only for inventory-api

- **File:** `documents/35-lakeshore-docker-vs-k8s-memo.docx`
- **Doc ID:** LSH-MEM-2024-006
- **Type:** Recommendation memo
- **Form type (dropdown):** Other
- **4. Pages:** 43 (LibreOffice), 14502 words
- **6. Description:** Recommendation memo keeping Lakeshore WooCommerce on Docker Compose and Kubernetes only for inventory-api, refusing a four-site Helm move.
- **7. Written:** 18-01-2024 (January 18, 2024)
- **Role at the time:** Web Developer

### 36. Incident: expired TLS certificate on pickup.lakeshore.internal

- **File:** `documents/36-lakeshore-tls-cert-incident.docx`
- **Doc ID:** LSH-INC-2024-014
- **Type:** Incident report
- **Form type (dropdown):** Incident report
- **4. Pages:** 43 (LibreOffice), 12012 words
- **6. Description:** Incident report for an expired TLS certificate on the Lakeshore pickup host, with renew windows and a refuse on an uninventoried wildcard.
- **7. Written:** 12-02-2024 (February 12, 2024)
- **Role at the time:** Web Developer

### 37. Memo: AWS capacity for weekend sales, stay on two API pods until 40 percent headroom fails

- **File:** `documents/37-lakeshore-aws-capacity-memo.docx`
- **Doc ID:** LSH-MEM-2024-022
- **Type:** Capacity memo
- **Form type (dropdown):** Other
- **4. Pages:** 43 (LibreOffice), 12095 words
- **6. Description:** Capacity memo for Lakeshore inventory-api on AWS, refusing a larger instance after a weekend graph that was Woo PHP, not the API.
- **7. Written:** 07-03-2024 (March 7, 2024)
- **Role at the time:** Web Developer

### 38. ADR: React admin for stock, WordPress stays the public storefront

- **File:** `documents/38-lakeshore-react-vs-wp-adr.docx`
- **Doc ID:** LSH-ADR-2024-029
- **Type:** Architecture decision record
- **Form type (dropdown):** Other
- **4. Pages:** 49 (LibreOffice), 12036 words
- **6. Description:** Architecture decision record keeping Lakeshore public storefronts on WooCommerce and the stock admin on React, with Luis as acceptor.
- **7. Written:** 02-04-2024 (April 2, 2024)
- **Role at the time:** Web Developer

### 39. Load report: Lakeshore Memorial Day weekend sale

- **File:** `documents/39-lakeshore-weekend-sale-load-test.docx`
- **Doc ID:** LSH-TST-2024-037
- **Type:** Load test report
- **Form type (dropdown):** Other
- **4. Pages:** 47 (LibreOffice), 12022 words
- **6. Description:** Load test report for the Lakeshore Memorial Day sale soak at 2.4x Tuesday traffic, with fail gates and a refuse on 1x soak.
- **7. Written:** 28-05-2024 (May 28, 2024)
- **Role at the time:** Web Developer

### 40. SOP: MySQL 8 schema change for inventory, expand then contract

- **File:** `documents/40-lakeshore-mysql-migration-sop.docx`
- **Doc ID:** LSH-SOP-2024-044
- **Type:** Runbook / SOP
- **Form type (dropdown):** Runbook / SOPs
- **4. Pages:** 43 (LibreOffice), 13913 words
- **6. Description:** SOP for Lakeshore inventory MySQL schema changes using expand/contract, an 8 second lock budget, and no same-release column drop.
- **7. Written:** 11-07-2024 (July 11, 2024)
- **Role at the time:** Web Developer

### 41. On-call SOP for Lakeshore inventory-api and Woo projection

- **File:** `documents/41-lakeshore-oncall-sop.docx`
- **Doc ID:** LSH-SOP-2024-051
- **Type:** Runbook / SOP
- **Form type (dropdown):** Runbook / SOPs
- **4. Pages:** 48 (LibreOffice), 11965 words
- **6. Description:** On-call SOP for Lakeshore inventory-api and Woo projection, with named tells and a refuse on 'check Grafana' page bodies.
- **7. Written:** 22-08-2024 (August 22, 2024)
- **Role at the time:** Web Developer

### 42. Lakeshore AWS Terraform layout for inventory-api

- **File:** `documents/42-lakeshore-aws-terraform-design.docx`
- **Doc ID:** LSH-TDD-2024-059
- **Type:** Technical design document
- **Form type (dropdown):** Technical design doc
- **4. Pages:** 43 (LibreOffice), 12880 words
- **6. Description:** Terraform design for Lakeshore inventory-api on AWS: four modules, stg/prod workspaces, one account, no 4k-line main.tf.
- **7. Written:** 19-09-2024 (September 19, 2024)
- **Role at the time:** Web Developer

### 43. PRD: POS exception codes for stock mismatch

- **File:** `documents/43-lakeshore-pos-exception-prd.docx`
- **Doc ID:** LSH-PRD-2025-007
- **Type:** Product requirements document
- **Form type (dropdown):** Product requirements doc
- **4. Pages:** 47 (LibreOffice), 12031 words
- **6. Description:** PRD mapping Lakeshore POS stock-mismatch exceptions to six shared codes with cashier sentences, refusing raw HTTP status on the till.
- **7. Written:** 16-01-2025 (January 16, 2025)
- **Role at the time:** Web Developer

### 44. Eval rubric: Lakeshore category copy and title pattern

- **File:** `documents/44-lakeshore-seo-copy-rubric.docx`
- **Doc ID:** LSH-EVAL-2025-011
- **Type:** Evaluation rubric
- **Form type (dropdown):** Other
- **4. Pages:** 49 (LibreOffice), 12016 words
- **6. Description:** Evaluation rubric for Lakeshore category copy and titles, failing city stuffing and locking a product-category-store pattern.
- **7. Written:** 20-02-2025 (February 20, 2025)
- **Role at the time:** Web Developer

### 45. Lakeshore Redis cache for on-hand reads, technical design

- **File:** `documents/45-lakeshore-redis-stock-design.docx`
- **Doc ID:** LSH-TDD-2025-018
- **Type:** Technical design document
- **Form type (dropdown):** Technical design doc
- **4. Pages:** 42 (LibreOffice), 14770 words
- **6. Description:** Technical design for a Redis cache in front of Lakeshore on-hand reads, with a 45s TTL and fail-open to MySQL instead of stale-as-fresh.
- **7. Written:** 13-03-2025 (March 13, 2025)
- **Role at the time:** Web Developer

### 46. Postmortem: weekend double-charge on pickup prepaid

- **File:** `documents/46-lakeshore-weekend-double-charge-postmortem.docx`
- **Doc ID:** LSH-INC-2025-024
- **Type:** Incident report / postmortem
- **Form type (dropdown):** Incident report
- **4. Pages:** 43 (LibreOffice), 14266 words
- **6. Description:** Postmortem for Lakeshore weekend double-charges on prepaid pickup, covering the missing idempotency key, 11 refunds, and the refuse on laptop capture retries.
- **7. Written:** 10-04-2025 (April 10, 2025)
- **Role at the time:** Web Developer

### 47. Hillcrest Digital client onboard SOP

- **File:** `documents/47-hillcrest-client-onboard-sop.docx`
- **Doc ID:** HIL-SOP-2024-031
- **Type:** Runbook / SOP
- **Form type (dropdown):** Runbook / SOPs
- **4. Pages:** 43 (LibreOffice), 12011 words
- **6. Description:** SOP for onboarding a Hillcrest Digital web client: access, staging host, ticket prefix, first deploy window, and a refuse on Slack password paste.
- **7. Written:** 13-06-2024 (June 13, 2024)
- **Role at the time:** Web Developer

### 48. Hillcrest Digital secrets and access SOP

- **File:** `documents/48-hillcrest-secrets-access-sop.docx`
- **Doc ID:** HIL-SOP-2024-038
- **Type:** Runbook / SOP
- **Form type (dropdown):** Runbook / SOPs
- **4. Pages:** 43 (LibreOffice), 14871 words
- **6. Description:** SOP for Hillcrest Digital secrets and access: per-client vaults, seven-day expiry after pause, logged break-glass, no secrets in tickets.
- **7. Written:** 25-07-2024 (July 25, 2024)
- **Role at the time:** Web Developer

### 49. Hillcrest staging-per-client design

- **File:** `documents/49-hillcrest-staging-per-client-design.docx`
- **Doc ID:** HIL-TDD-2025-009
- **Type:** Technical design document
- **Form type (dropdown):** Technical design doc
- **4. Pages:** 43 (LibreOffice), 13643 words
- **6. Description:** Technical design for per-client Hillcrest staging hosts, refusing a shared preview after a Harbor/Lakeshore leftover mix.
- **7. Written:** 06-02-2025 (February 6, 2025)
- **Role at the time:** Web Developer

### 50. Hillcrest Q3 pipeline notes, August 7

- **File:** `documents/50-hillcrest-q3-pipeline-notes.docx`
- **Doc ID:** HIL-MTG-2025-016
- **Type:** Meeting notes
- **Form type (dropdown):** Other
- **4. Pages:** 43 (LibreOffice), 14795 words
- **6. Description:** Q3 pipeline notes for Hillcrest Digital: Lakeshore active work, Harbor maintenance, one new onboard maximum, and a refuse on two first-publishes in one week.
- **7. Written:** 07-08-2025 (August 7, 2025)
- **Role at the time:** Web Developer
