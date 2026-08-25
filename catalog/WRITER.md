# Writer instructions (read this first)

You are writing original fictional internal engineering documents for Aman Kumar's portfolio of professional writing samples. They are NOT real client deliverables. Never mention Infosys, Wipro, HCL, Handshake, or any real bank/hospital.

World file: `/workspace/catalog/world.json`
Schema: `/workspace/catalog/SCHEMA.txt`
Output: `/workspace/content/<slug>.json`  (one file per document)

## JSON top-level (every file)

```
{
  "slug": "...",
  "doc_id": "...",
  "title": "...",
  "subtitle": "...",
  "doc_type": "...",
  "kicker": "...",
  "org": "Northstar Engineering",
  "classification": "INTERNAL",
  "version": "1.2",
  "status": "Approved",
  "date": "November 18, 2019",
  "author": "Aman Kumar",
  "role": "...",
  "team": "...",
  "audience": "...",
  "owners": "...",
  "related": "ticket IDs and sibling docs",
  "summary": "2-4 sentences, what the doc is and who it is for.",
  "form_description": "1-2 sentences. What it is and what it was written for.",
  "field": "Software Engineering / Data Science",
  "revision_history": [["1.0","date","name","notes"], ...],
  "blocks": [ ... ]
}
```

Date in the JSON `date` field must be English: "April 11, 2023".

## Length

Minimum 2800 words in the combined text of summary + all block text/items/table cells. Target 3200-4200. If you finish under 2800, add another failure-mode section, not filler.

## Voice (non-negotiable)

Write like a working engineer sending this to colleagues. Concrete. A little uneven. Specific names, hostnames, lag numbers, ticket IDs, plant codes, SQL object names.

Banned words/phrases: furthermore, moreover, additionally, leverage, utilize, robust, seamless, holistic, landscape, delve, cutting-edge, empower, streamline, it's important to note, in order to, at the end of the day, moving forward (unless literal calendar), synergy, paradigm, unlock, comprehensive, ensure, facilitate, pivotal, nestled, tapestry.

No em dashes. No "It's not X, it's Y." No three-item parallel slogans.

Every document must include:
- at least one rejected alternative and why it died
- at least two named people from the world file plus 1-2 extra fictional colleagues
- open questions with owners
- numbers that are not round (8.2M, 7.4 min, 12-40s, $14.6k)
- one section a VP could skim (decision / recommendation) AND one section a working engineer could execute (commands, schemas, failure modes)

## Block mix

Use h1/h2/h3, many `p` blocks (most of the words live here), 3+ tables, 1-3 callouts, bullets/steps, and for runbooks/designs at least one `code` block with real commands.

Meeting notes: decisions, owners, open questions, next steps. Not a transcript.

Runbooks: exact commands, preconditions, what to do when it fails.

Incidents: timeline, impact, contributing factors, what you will actually change.

Designs: constraints, trade-offs, edge cases, failure modes.

Do not invent public-company filings or copy public docs. Keep it internal and fictional.
