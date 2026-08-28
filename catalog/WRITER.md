# House style for Pinecrest / Ridgeway Word files

World file: `catalog/world.json`
Author: Jeilen Jones. Do not put a phone number or personal email in the Word files.
Do not name Nolan, Lincoln College, or Lake Oconee Academy as employers.
Hosts use `.internal` (`pinecrest.internal`, `ridgeway.internal`).


World file: `catalog/world.json`
Schema: `catalog/SCHEMA.txt`
Source: `content/<slug>.json` (one file per document)
Output: `documents/<slug>.docx`

## JSON top-level (every file)

```
{
  "slug": "...",
  "doc_id": "...",
  "title": "...",
  "subtitle": "...",
  "doc_type": "...",
  "kicker": "...",
  "org": "Pinecrest Fulfillment" | "Ridgeway Diesel",
  "classification": "INTERNAL",
  "version": "last revision row",
  "status": "matches the kind of document",
  "date": "November 9, 2023",
  "author": "Jeilen Jones",
  "role": "Order Picker" | "Shop Helper",
  "team": "...",
  "audience": "...",
  "owners": "...",
  "related": "ticket IDs and sibling docs",
  "summary": "2-4 sentences, what the doc is and who it is for.",
  "form_description": "1-2 sentences. What it is and what it was written for.",
  "field": "Operations / Logistics",
  "revision_history": [["1.0","date","name","notes"], ...],
  "blocks": [ ... ]
}
```

Date in the JSON `date` field must be English: "April 11, 2023".

Status follows the document kind (runbook In force, incident Closed, memo For decision, notes Issued, design Accepted). Do not stamp every file Approved / v1.2.

Hosts use `.internal` (`whetstone.internal`, `harbor.internal`, `lakeshore.internal`, `hillcrest.internal`). Do not use the RFC documentation TLD `.example` except in a Spring filename such as `application-local.yml.example`.

## Length

The generator expands each file into the 40-50 page band. Front matter must still carry the real decisions. Remainder sections have to be in-genre and file-local. Do not mill the same exhibit stub, and do not reuse the same leftover headings or leftover sentences across files.

## Voice (non-negotiable)

Write like a working engineer sending this to colleagues. Concrete. A little uneven. Specific names, hostnames, lag numbers, ticket IDs, SQL object names, theme files.

Banned words/phrases: handshake, furthermore, moreover, additionally, leverage, utilize, robust, seamless, holistic, landscape, delve, cutting-edge, empower, streamline, it's important to note, in order to, at the end of the day, moving forward (unless literal calendar), synergy, paradigm, unlock, comprehensive, ensure, facilitate, pivotal, nestled, tapestry.

No em dashes. No "It's not X, it's Y." No three-item parallel slogans.

Every document must include:
- at least one rejected alternative and why it died
- at least two named people from the world file plus 1-2 extra colleagues
- open questions with owners
- numbers that are not round (8.2M, 7.4 min, 12-40s, $14.6k)
- one section a VP could skim (decision / recommendation) AND one section a working engineer could execute (commands, schemas, failure modes)

Do not put a home address, phone, or LinkedIn in the Word files. Do not name Cummins. Do not write pentest or exploit procedures.

## Block mix

Use h1/h2/h3, many `p` blocks (most of the words live here), 3+ tables, 1-3 callouts, bullets/steps, and for runbooks/designs at least one `code` block with real commands.

Meeting notes: decisions, owners, open questions, next steps. Not a transcript.

Runbooks: exact commands, preconditions, what to do when it fails.

Incidents: timeline, impact, contributing factors, what you will actually change.

Designs: constraints, trade-offs, edge cases, failure modes.

Do not invent public-company filings or copy public docs. Keep it internal. Never Infosys, Wipro, HCL, or real bank/hospital names.
