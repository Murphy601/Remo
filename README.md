# Internal engineering documents

Fifty internal engineering Word files (`.docx`) authored by **Michael Gilfilian**, Web Developer at Hillcrest Digital, covering freelance web and IT support work from 2020–2025, plus a 2023 internship at Whetstone Industrial.

**Download:** [DOWNLOADS.md](DOWNLOADS.md) has a direct link for each file. [documents.zip](documents.zip) is all 50 in one archive.

## What you actually open

All finished files live in [`documents/`](documents/). Intake answers (job title, years, field, page count, description, date) are in [`catalog/FORM_ANSWERS.md`](catalog/FORM_ANSWERS.md).

| Era | Engagement | Count | Kinds of docs |
| --- | --- | --- | --- |
| Jan–May 2023 | Whetstone Industrial (IT support intern) | 8 | requirements, design, SOP, incident, notes, memo, runbook, test notes |
| 2020–2022 | Harbor & Oak Outfitters (Shopify / SEO) | 16 | requirements, Liquid design, SEO notes, incidents, PRDs, runbooks, systems design, memos |
| 2022–2025 | Lakeshore Hardware Group (Woo / inventory API) | 22 | requirements, REST and systems design, runbooks, incidents, PRDs, memos, ADR, load test, Terraform, Redis |
| 2024–2025 | Hillcrest Digital (practice) | 4 | client onboard SOP, secrets SOP, staging design, Q3 pipeline notes |

Every file is **40–50 pages**, measured in LibreOffice. Word counts sit around 12,000–15,500, so the 150-words-per-page bar still holds.

## Shared intake answers

1. **Job title:** Web Developer
2. **Years:** 5–10 (about six years, freelance 2020–present)
3. **Field:** Software Engineering / Data Science
4. **Pages:** see FORM_ANSWERS (40–50 each, LibreOffice)
5. **Upload:** the `.docx` under `documents/` (submit the zip of docx files, not the GitHub repo)
6–7. **Description and date:** see FORM_ANSWERS

## Regenerate from source

JSON for each document is in `content/`. Layout is `tools/docx_builder.py`.

```bash
pip install -r requirements.txt
python3 tools/seed_michael.py
python3 tools/generate.py
python3 tools/count_pages.py
python3 tools/write_catalog.py
```

Output lands in `documents/` again.
