# Warehouse and diesel-shop documents

Fifty internal Word files (`.docx`) authored by **Jeilen Jones**, Order Picker at Pinecrest Fulfillment, plus shop-helper work at Ridgeway Diesel matching diesel and truck coursework (brakes, PM, electrical, fuel systems).

**Download:** [DOWNLOADS.md](DOWNLOADS.md) has a direct link for each file. [documents.zip](documents.zip) is all 50 in one archive.

## What you actually open

All finished files live in [`documents/`](documents/). Intake answers are in [`catalog/FORM_ANSWERS.md`](catalog/FORM_ANSWERS.md).

| Era | Engagement | Count | Kinds of docs |
| --- | --- | --- | --- |
| Oct 2023–2025 | Pinecrest Fulfillment (order pick / pack / dock) | 32 | SOPs, incidents, notes, memos, requirements, pick-path design, QA rubric |
| 2022–2023 | Ridgeway Diesel (shop helper) | 18 | PM, brakes, fuel, electrical, drivetrain, welding/hydraulics, parts, road test |

Every file is **40–50 pages**, measured in LibreOffice.

## Shared intake answers

1. **Job title:** Order Picker
2. **Years:** 1–5 (Order Picker from October 2023; diesel shop helper 2022–2023)
3. **Field:** Operations / Logistics
4. **Pages:** 40–50 each (LibreOffice Writer → PDF)
5. **Upload:** the `.docx` under `documents/` (submit the zip of docx files, not the GitHub repo)
6–7. **Description and date:** see FORM_ANSWERS

## Regenerate from source

```bash
pip install -r requirements.txt
python3 tools/seed_jeilen.py
python3 tools/generate.py
python3 tools/count_pages.py
python3 tools/write_catalog.py
```
