# Internal engineering documents

Fifty internal engineering Word files (`.docx`) authored by **Aman Kumar**, Software Engineer II at Northstar Engineering, covering backend and data-platform work from 2019–2025.

**Download:** [DOWNLOADS.md](DOWNLOADS.md) has a direct link for each file. [documents.zip](documents.zip) is all 50 in one archive.

## What you actually open

All finished files live in [`documents/`](documents/). Intake answers (job title, years, field, page count, description, date) are in [`catalog/FORM_ANSWERS.md`](catalog/FORM_ANSWERS.md).

| Era | Engagement | Count | Kinds of docs |
| --- | --- | --- | --- |
| 2019–2020 | Oakridge Industrial (manufacturing ERP) | 5 | requirements, design, SOP, meeting notes, integration guide |
| 2020–2022 | Riverview Health Network (hospital data platform) | 10 | PRDs, identity-merge design, incident, test strategy, runbooks, PHI SOP |
| 2022–2025 | Clearhaven Markets (transaction recon, ~8.2M records/day) | 35 | systems design, Kafka ingest, incidents, runbooks, ADRs, capacity, eval rubric |

Every file is **40–50 pages**, measured in LibreOffice. Word counts sit around 12,500–15,000, so the 150-words-per-page bar still holds.

## Shared intake answers

1. **Job title:** Software Engineer II
2. **Years:** 5–10
3. **Field:** Software Engineering / Data Science
4. **Pages:** see FORM_ANSWERS (40–50 each, LibreOffice)
5. **Upload:** the `.docx` under `documents/`
6–7. **Description and date:** see FORM_ANSWERS

## Regenerate from source

JSON for each document is in `content/`. Layout is `tools/docx_builder.py`.

```bash
pip install -r requirements.txt
python3 tools/generate.py
```

Output lands in `documents/` again.
